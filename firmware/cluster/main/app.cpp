#include "platform.hpp"

#include "cluster/dashboard.hpp"
#include "esp_log.h"
#include "esp_lvgl_port.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#ifndef CONFIG_CLUSTER_LIVE
#include "cluster/replay.hpp"
#endif

namespace cluster::platform {
namespace {

constexpr char kTag[] = "cluster";
constexpr uint64_t kFramePeriodMs = 33;

void report_failure(const char* operation, esp_err_t err)
{
    if (err != ESP_OK) {
        ESP_LOGE(kTag, "%s failed: %s", operation, esp_err_to_name(err));
    }
}

bool check_peripheral(ViewState& view, PeripheralFault fault, const char* operation, esp_err_t err)
{
    if (err != ESP_OK) {
        view.peripheral_faults |= fault;
        report_failure(operation, err);
        return false;
    }
    return true;
}

#ifdef CONFIG_CLUSTER_LIVE
void age_reading(Reading& reading, uint64_t now)
{
    if (reading.present() && (now < reading.observed_ms || now - reading.observed_ms >= kTelemetryStaleMs)) {
        reading.quality = Quality::Missing;
    }
}
#endif

class App {
public:
    void run();

private:
    bool update_source(uint64_t now);
    void update_controls(uint64_t now);
    void render(uint64_t now);

    ViewState view_{};
    History history_{};
    Controls controls_{};
    Preferences preferences_{};
    Dashboard dashboard_{};
    bool buttons_available_ = false;
    uint64_t next_frame_ms_ = 0;
    uint64_t first_frame_deadline_ms_ = 0;
    uint8_t applied_brightness_ = 0;

#ifdef CONFIG_CLUSTER_LIVE
    bool uart_available_ = false;
#else
    uint64_t replay_tick_ms_ = 0;
    // Observation ages and trace positions share a clock that stops on pause.
    uint64_t replay_clock_ms_ = 0;
    uint64_t replay_sample_at_ms_ = 0;
    uint32_t replay_offset_ms_ = 0;
#endif
#ifdef CONFIG_CLUSTER_ADS1115
    LocalSensors local_{};
#endif
};

bool App::update_source(uint64_t now)
{
    const uint64_t previous_sample_ms = view_.telemetry.received_ms;
    const LinkState previous_link = view_.telemetry.link;
#ifdef CONFIG_CLUSTER_LIVE
    take_uart_snapshot(view_.telemetry);
    // Queue producer timestamps can be newer than the loop's initial clock read.
    now = now_ms();
    if (view_.telemetry.link == LinkState::Live) {
        for (auto& reading : view_.telemetry.values) {
            age_reading(reading, now);
        }
        if (now - view_.telemetry.received_ms >= kTelemetryStaleMs) {
            const uint32_t rejected_frames = view_.telemetry.rejected_frames;
            view_.telemetry = {};
            view_.telemetry.link = LinkState::Stale;
            view_.telemetry.rejected_frames = rejected_frames;
        }
    }
#else
    if (!view_.replay_paused) {
        const uint64_t delta = now - replay_tick_ms_;
        replay_clock_ms_ += delta;
        const uint64_t elapsed = replay_offset_ms_ + delta;
        const bool looped = elapsed >= kReplayDurationMs;
        if (looped) {
            history_.clear();
        }
        replay_offset_ms_ = elapsed % kReplayDurationMs;
        if (looped || replay_clock_ms_ >= replay_sample_at_ms_) {
            view_.telemetry = replay_sample(replay_offset_ms_, replay_clock_ms_);
            replay_sample_at_ms_ = replay_clock_ms_ + kFramePeriodMs;
        }
    }
    replay_tick_ms_ = now;
    now = replay_clock_ms_;
#endif

#ifdef CONFIG_CLUSTER_ADS1115
    if (take_adc_sample(local_)) {
        view_.peripheral_faults &= ~AdcFault;
        if (local_.fault) {
            view_.peripheral_faults |= AdcFault;
        }
    }
    now = now_ms();
    age_reading(local_.fuel, now);
    age_reading(local_.oil_temp, now);
    view_.telemetry.get(Metric::FuelPercent) = local_.fuel;
    view_.telemetry.get(Metric::OilTempF) = local_.oil_temp;
#endif

    if (!view_.replay_paused) {
        history_.append(view_.telemetry, now);
    }
    return view_.telemetry.received_ms != previous_sample_ms || view_.telemetry.link != previous_link;
}

void App::update_controls(uint64_t now)
{
    if (!buttons_available_) {
        return;
    }
    const auto result = controls_.update(read_buttons(), view_, now);
    if (result.preferences_changed) {
        preferences_.changed(now);
    }
#ifdef CONFIG_CLUSTER_LIVE
    if (uart_available_ && result.confirm_ecu_reset) {
        confirm_ecu_reset();
    }
#endif
}

void App::render(uint64_t now)
{
    if (now < next_frame_ms_) {
        return;
    }
    next_frame_ms_ = now + kFramePeriodMs;
    if (lvgl_port_lock(5)) {
#ifdef CONFIG_CLUSTER_LIVE
        const uint64_t frame_time = now;
#else
        const uint64_t frame_time = replay_clock_ms_;
#endif
        dashboard_.update(view_, history_, frame_time);
        lvgl_port_unlock();
    }
    if (first_frame_deadline_ms_ && now >= first_frame_deadline_ms_) {
        if (!display_ready()) {
            ESP_LOGE(kTag, "LCD did not complete its first render");
        }
        first_frame_deadline_ms_ = 0;
    }
    if (display_ready() && applied_brightness_ != view_.brightness_percent) {
        const auto err = backlight(view_.brightness_percent);
        report_failure("Backlight adjustment", err);
        applied_brightness_ = view_.brightness_percent;
    }
}

void App::run()
{
    const esp_err_t display_err = start_display();
    if (display_err != ESP_OK) {
        report_failure("Display start", display_err);
        return;
    }

    buttons_available_ = check_peripheral(view_, ButtonsFault, "Buttons", configure_buttons());
    check_peripheral(view_, PreferencesFault, "Preferences load", preferences_.load(view_));
    const uint64_t started = now_ms();
    first_frame_deadline_ms_ = started + 1000;
#ifndef CONFIG_CLUSTER_LIVE
    replay_tick_ms_ = started;
    replay_clock_ms_ = started;
    update_source(started);
#endif

    if (!lvgl_port_lock(250)) {
        ESP_LOGE(kTag, "Cannot create dashboard. LVGL lock timed out");
        return;
    }
    dashboard_.create(lv_screen_active());
    dashboard_.update(view_, history_, started);
    await_first_frame();
    lvgl_port_unlock();

#ifdef CONFIG_CLUSTER_LIVE
    uart_available_ = check_peripheral(view_, UartFault, "Telemetry UART", start_uart());
#endif
#ifdef CONFIG_CLUSTER_ADS1115
    check_peripheral(view_, AdcFault, "ADS1115", start_adc());
#endif
#ifdef CONFIG_CLUSTER_SD_LOGGING
    bool logger_started = false;
#endif

    while (true) {
        const bool new_sample = update_source(now_ms());
        const uint64_t now = now_ms();
        update_controls(now);
        const esp_err_t save_result = preferences_.save_if_settled(view_, now);
        check_peripheral(view_, PreferencesFault, "Preferences save", save_result);
#ifdef CONFIG_CLUSTER_SD_LOGGING
        const LogState state = log_state();
        view_.logging_active = state == LogState::Active;
        view_.logging_fault = state == LogState::Fault;
        if (new_sample && view_.logging_active && !enqueue_log(view_.telemetry) &&
            view_.log_dropped != UINT32_MAX) {
            ++view_.log_dropped;
        }
#else
        (void)new_sample;
#endif
        render(now);
#ifdef CONFIG_CLUSTER_SD_LOGGING
        // Mount the card only after the first dashboard frame.
        if (!logger_started && display_ready()) {
            logger_started = true;
            report_failure("SD logging worker", start_logger());
        }
#endif
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

} // namespace
} // namespace cluster::platform

extern "C" void app_main()
{
    static cluster::platform::App app;
    app.run();
}
