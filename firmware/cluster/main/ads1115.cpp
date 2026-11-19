#include "platform.hpp"

#include <array>
#include <cerrno>
#include <cstdlib>

#include "cluster/calibration.hpp"
#include "driver/i2c_master.h"
#include "esp_check.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"

namespace cluster::platform {
namespace {

constexpr char kTag[] = "cluster_ads";
constexpr uint8_t kConfigRegister = 0x01;
constexpr uint8_t kConversionRegister = 0x00;
constexpr int kTransferTimeoutMs = 20;

struct Profile {
    explicit Profile(float low, float high) : minimum(low), maximum(high) {}

    std::array<CalibrationKnot, 16> knots{};
    size_t count = 0;
    float minimum;
    float maximum;
};

Profile fuel_profile(0, 100);
Profile oil_temp_profile(-40, 400);
i2c_master_dev_handle_t adc = nullptr;
QueueHandle_t adc_queue = nullptr;

void load_profile(Profile& profile, const char* text, const char* name)
{
    if (!*text) {
        return;
    }
    size_t count = 0;
    const char* cursor = text;
    while (count < profile.knots.size()) {
        char* end = nullptr;
        errno = 0;
        const long raw = std::strtol(cursor, &end, 10);
        if (errno || end == cursor || *end != ':' || raw < 0 || raw > 32767) {
            break;
        }

        cursor = end + 1;
        const float value = std::strtof(cursor, &end);
        if (errno || end == cursor || (*end != ',' && *end != '\0')) {
            break;
        }
        profile.knots[count++] = {static_cast<int32_t>(raw), value};
        if (*end == '\0') {
            if (calibration_valid(profile.knots.data(), count, profile.minimum, profile.maximum)) {
                profile.count = count;
                return;
            }
            break;
        }
        cursor = end + 1;
    }
    ESP_LOGW(kTag, "%s calibration is invalid. Channel disabled", name);
}

esp_err_t read_register(uint8_t address, uint16_t& value)
{
    uint8_t bytes[2]{};
    const esp_err_t result = i2c_master_transmit_receive(adc, &address, 1, bytes, 2, kTransferTimeoutMs);
    value = (static_cast<uint16_t>(bytes[0]) << 8) | bytes[1];
    return result;
}

esp_err_t read_channel(unsigned channel, int32_t& raw_counts)
{
    // ADS1115 single shot, AINn versus GND, +/-4.096 V, 128 SPS, comparator off.
    const uint16_t config = 0xc383 | (channel << 12);
    const uint8_t command[] = {kConfigRegister, static_cast<uint8_t>(config >> 8),
                               static_cast<uint8_t>(config)};
    const esp_err_t start = i2c_master_transmit(adc, command, sizeof(command), kTransferTimeoutMs);
    if (start != ESP_OK) {
        return start;
    }
    vTaskDelay(pdMS_TO_TICKS(12));

    uint16_t status = 0;
    const esp_err_t status_result = read_register(kConfigRegister, status);
    if (status_result != ESP_OK) {
        return status_result;
    }
    if ((status & 0x8000) == 0) {
        return ESP_ERR_TIMEOUT;
    }
    if (status != config) {
        return ESP_ERR_INVALID_RESPONSE;
    }

    uint16_t value = 0;
    const esp_err_t result = read_register(kConversionRegister, value);
    raw_counts = value < 0x8000 ? value : static_cast<int32_t>(value) - 65536;
    return result;
}

Reading sample_channel(const Profile& profile, unsigned channel, bool& fault)
{
    if (profile.count == 0) {
        return {};
    }
    int32_t raw_counts = 0;
    if (read_channel(channel, raw_counts) != ESP_OK) {
        fault = true;
        return {};
    }
    return calibrated_reading(profile.knots.data(), profile.count, raw_counts, profile.minimum,
                              profile.maximum, now_ms());
}

void run_adc(void*)
{
    bool previous_fault = false;
    while (true) {
        LocalSensors next{};
        next.fuel = sample_channel(fuel_profile, 0, next.fault);
        next.oil_temp = sample_channel(oil_temp_profile, 1, next.fault);
        if (next.fault != previous_fault) {
            if (next.fault) {
                ESP_LOGW(kTag, "ADS1115 conversion failed. Affected readings unavailable");
            } else {
                ESP_LOGI(kTag, "ADS1115 conversions recovered");
            }
            previous_fault = next.fault;
        }
        xQueueOverwrite(adc_queue, &next);
        vTaskDelay(pdMS_TO_TICKS(200));
    }
}

} // namespace

esp_err_t start_adc()
{
    load_profile(fuel_profile, CONFIG_CLUSTER_ADS1115_FUEL_KNOTS, "A0 fuel");
    load_profile(oil_temp_profile, CONFIG_CLUSTER_ADS1115_OIL_TEMP_KNOTS, "A1 oil temperature");
    if (fuel_profile.count == 0 && oil_temp_profile.count == 0) {
        ESP_LOGI(kTag, "No measured ADS1115 calibration. I2C remains disabled");
        return ESP_OK;
    }

    i2c_master_bus_config_t bus_config{};
    bus_config.i2c_port = I2C_NUM_1;
    bus_config.sda_io_num = kAdcSda;
    bus_config.scl_io_num = kAdcScl;
    bus_config.clk_source = I2C_CLK_SRC_DEFAULT;
    bus_config.glitch_ignore_cnt = 7;
    i2c_master_bus_handle_t bus = nullptr;
    ESP_RETURN_ON_ERROR(i2c_new_master_bus(&bus_config, &bus), kTag, "ADS1115 I2C bus initialization failed");

    i2c_device_config_t device_config{};
    device_config.dev_addr_length = I2C_ADDR_BIT_LEN_7;
    device_config.device_address = 0x48;
    device_config.scl_speed_hz = 100000;
    esp_err_t err = i2c_master_bus_add_device(bus, &device_config, &adc);
    if (err == ESP_OK) {
        adc_queue = xQueueCreate(1, sizeof(LocalSensors));
        if (!adc_queue || xTaskCreate(run_adc, "cluster_adc", 4 * 1024, nullptr, 2, nullptr) != pdPASS) {
            err = ESP_ERR_NO_MEM;
        }
    }
    if (err != ESP_OK) {
        if (adc_queue) {
            vQueueDelete(adc_queue);
            adc_queue = nullptr;
        }
        if (adc) {
            i2c_master_bus_rm_device(adc);
            adc = nullptr;
        }
        i2c_del_master_bus(bus);
    }
    return err;
}

bool take_adc_sample(LocalSensors& sample)
{
    return adc_queue && xQueueReceive(adc_queue, &sample, 0) == pdTRUE;
}

} // namespace cluster::platform
