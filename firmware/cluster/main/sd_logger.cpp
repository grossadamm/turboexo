#include "platform.hpp"

#include <atomic>
#include <cerrno>
#include <cinttypes>
#include <cstdio>

#include "driver/sdmmc_host.h"
#include "esp_check.h"
#include "esp_log.h"
#include "esp_random.h"
#include "esp_vfs_fat.h"
#include "fcntl.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#include "sd_pwr_ctrl_by_on_chip_ldo.h"
#include "unistd.h"

namespace cluster::platform {
namespace {

constexpr char kTag[] = "cluster_sd";
constexpr char kMount[] = "/sdcard";
constexpr uint64_t kFlushPeriodMs = 1000;
QueueHandle_t log_queue = nullptr;
std::atomic<LogState> state{LogState::Starting};

const char* source_name(LinkState link)
{
    switch (link) {
    case LinkState::Replay: return "replay";
    case LinkState::AwaitEcuReset: return "await_reset";
    case LinkState::Connecting: return "connecting";
    case LinkState::Live: return "live";
    case LinkState::Stale: return "stale";
    case LinkState::Unsupported: return "unsupported";
    case LinkState::TransportFault: return "transport_fault";
    }
    return "unknown";
}

const char* quality_name(Quality quality)
{
    switch (quality) {
    case Quality::Valid: return "valid";
    case Quality::Unverified: return "unverified";
    case Quality::Simulated: return "simulated";
    case Quality::Missing: return "missing";
    }
    return "missing";
}

struct LogSample {
    uint64_t time_ms;
    Snapshot telemetry;
};

esp_err_t power_sd(sd_pwr_ctrl_handle_t& power)
{
    // VO4 powers the SD GPIO bank and the board's SD pull-ups. The card supply
    // itself has a separate active-low switch on GPIO45.
    sd_pwr_ctrl_ldo_config_t config{};
    config.ldo_chan_id = 4;
    ESP_RETURN_ON_ERROR(sd_pwr_ctrl_new_on_chip_ldo(&config, &power), kTag, "SD I/O LDO failed");
    ESP_RETURN_ON_ERROR(sd_pwr_ctrl_set_io_voltage(power, 3300), kTag, "SD I/O voltage failed");
    ESP_RETURN_ON_ERROR(gpio_set_level(kSdPowerEnable, 1), kTag, "SD power pin failed");
    gpio_config_t gpio{};
    gpio.pin_bit_mask = uint64_t{1} << kSdPowerEnable;
    gpio.mode = GPIO_MODE_OUTPUT;
    ESP_RETURN_ON_ERROR(gpio_config(&gpio), kTag, "SD power GPIO failed");
    gpio.pin_bit_mask = uint64_t{1} << kSdDetect;
    gpio.mode = GPIO_MODE_INPUT;
    ESP_RETURN_ON_ERROR(gpio_config(&gpio), kTag, "SD detect GPIO failed");
    if (gpio_get_level(kSdDetect) != 0) {
        return ESP_ERR_NOT_FOUND;
    }
    vTaskDelay(pdMS_TO_TICKS(100));
    ESP_RETURN_ON_ERROR(gpio_set_level(kSdPowerEnable, 0), kTag, "SD power enable failed");
    vTaskDelay(pdMS_TO_TICKS(100));
    return ESP_OK;
}

esp_err_t mount_sd(sd_pwr_ctrl_handle_t power, sdmmc_card_t*& card)
{
    sdmmc_host_t host = SDMMC_HOST_DEFAULT();
    host.slot = SDMMC_HOST_SLOT_1;
    host.flags &= ~(SDMMC_HOST_FLAG_8BIT | SDMMC_HOST_FLAG_DDR);
    host.pwr_ctrl_handle = power;
    host.command_timeout_ms = 500;
    sdmmc_slot_config_t slot = SDMMC_SLOT_CONFIG_DEFAULT();
    slot.clk = kSdClk;
    slot.cmd = kSdCmd;
    slot.d0 = kSdData0;
    slot.d1 = kSdData1;
    slot.d2 = kSdData2;
    slot.d3 = kSdData3;
    slot.d4 = slot.d5 = slot.d6 = slot.d7 = GPIO_NUM_NC;
    slot.cd = kSdDetect;
    slot.width = 4;
    esp_vfs_fat_sdmmc_mount_config_t config{};
    config.format_if_mount_failed = false;
    config.max_files = 1;
    return esp_vfs_fat_sdmmc_mount(kMount, &host, &slot, &config, &card);
}

FILE* open_unique_file()
{
    // 8.3-compatible, no wall-clock dependency. Exclusive creation guarantees
    // an existing log is never overwritten, even if random values repeat.
    for (unsigned attempt = 0; attempt < 32; ++attempt) {
        char path[32];
        std::snprintf(path, sizeof(path), "%s/C%07" PRIX32 ".CSV", kMount, esp_random() & 0x0fffffff);
        const int fd = open(path, O_WRONLY | O_CREAT | O_EXCL, 0644);
        if (fd < 0) {
            if (errno == EEXIST) {
                continue;
            }
            break;
        }
        FILE* file = fdopen(fd, "w");
        if (!file) {
            close(fd);
            break;
        }
        ESP_LOGI(kTag, "Logging to %s", path);
        return file;
    }
    return nullptr;
}

bool write_header(FILE* file)
{
    if (std::fputs("boot_ms,received_ms,source,engine_flags,protection_flags,sync_losses,"
                   "synchronized,target_echo_possible,ecu_uptime_s,ecu_loops_per_s,rejected_frames",
                   file) == EOF) {
        return false;
    }
    for (size_t index = 0; index < kMetricCount; ++index) {
        const auto* name = metric_name(static_cast<Metric>(index));
        if (std::fprintf(file, ",%s,%s_quality,%s_observed_ms", name, name, name) < 0) {
            return false;
        }
    }
    return std::fputc('\n', file) != EOF;
}

bool write_sample(FILE* file, const LogSample& sample)
{
    const Snapshot& snapshot = sample.telemetry;
    if (std::fprintf(file, "%" PRIu64 ",%" PRIu64 ",%s,%u,%u,%u,%u,%u,%u,%u,%" PRIu32,
                     sample.time_ms, snapshot.received_ms, source_name(snapshot.link),
                     static_cast<unsigned>(snapshot.engine_flags),
                     static_cast<unsigned>(snapshot.protection_flags),
                     static_cast<unsigned>(snapshot.sync_loss_count),
                     static_cast<unsigned>(snapshot.synchronized),
                     static_cast<unsigned>(snapshot.target_echo_possible),
                     static_cast<unsigned>(snapshot.ecu_uptime_seconds),
                     static_cast<unsigned>(snapshot.ecu_loops_per_second),
                     snapshot.rejected_frames) < 0) {
        return false;
    }
    for (const auto& reading : snapshot.values) {
        if (reading.present()) {
            if (std::fprintf(file, ",%.5f,%s,%" PRIu64, reading.value, quality_name(reading.quality),
                             reading.observed_ms) < 0) {
                return false;
            }
        } else if (std::fputs(",,missing,", file) == EOF) {
            return false;
        }
    }
    return std::fputc('\n', file) != EOF;
}

bool flush(FILE* file)
{
    return std::fflush(file) == 0 && fsync(fileno(file)) == 0;
}

void log_samples(FILE* file)
{
    if (!write_header(file) || !flush(file)) {
        return;
    }
    uint64_t flush_at = now_ms() + kFlushPeriodMs;
    bool dirty = false;
    state.store(LogState::Active, std::memory_order_relaxed);
    while (gpio_get_level(kSdDetect) == 0) {
        LogSample sample{};
        if (xQueueReceive(log_queue, &sample, pdMS_TO_TICKS(100))) {
            if (!write_sample(file, sample)) {
                return;
            }
            dirty = true;
        }
        const uint64_t now = now_ms();
        if (now >= flush_at) {
            if (dirty && !flush(file)) {
                return;
            }
            flush_at = now + kFlushPeriodMs;
            dirty = false;
        }
    }
}

void run_logger(void*)
{
    sd_pwr_ctrl_handle_t power = nullptr;
    sdmmc_card_t* card = nullptr;
    esp_err_t err = power_sd(power);
    if (err == ESP_OK) {
        err = mount_sd(power, card);
    }

    FILE* file = err == ESP_OK ? open_unique_file() : nullptr;
    if (file) {
        log_samples(file);
        ESP_LOGW(kTag, "Logging stopped after media removal or an I/O failure");
    } else if (err == ESP_ERR_NOT_FOUND) {
        ESP_LOGI(kTag, "No SD card detected");
    } else {
        ESP_LOGW(kTag, "SD logging unavailable: %s", err == ESP_OK ? "file open failed" : esp_err_to_name(err));
    }
    state.store(LogState::Fault, std::memory_order_relaxed);
    if (file) {
        std::fclose(file);
    }
    if (card) {
        esp_vfs_fat_sdcard_unmount(kMount, card);
    }
    if (power) {
        // Leave the I/O domain powered so GPIO45 can hold card power off.
        gpio_set_level(kSdPowerEnable, 1);
    }
    vTaskDelete(nullptr);
}

} // namespace

esp_err_t start_logger()
{
    log_queue = xQueueCreate(16, sizeof(LogSample));
    if (!log_queue || xTaskCreate(run_logger, "cluster_sd", 6 * 1024, nullptr, 2, nullptr) != pdPASS) {
        if (log_queue) {
            vQueueDelete(log_queue);
            log_queue = nullptr;
        }
        state.store(LogState::Fault, std::memory_order_relaxed);
        return ESP_ERR_NO_MEM;
    }
    return ESP_OK;
}

LogState log_state()
{
    return state.load(std::memory_order_relaxed);
}

bool enqueue_log(const Snapshot& snapshot)
{
    const LogSample sample{now_ms(), snapshot};
    return xQueueSend(log_queue, &sample, 0) == pdTRUE;
}

} // namespace cluster::platform
