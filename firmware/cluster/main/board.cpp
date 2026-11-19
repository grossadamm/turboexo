#include "platform.hpp"

#include <atomic>

#include "esp_check.h"
#include "esp_log.h"
#include "esp_lvgl_port.h"
#include "esp_psram.h"
#include "nvs.h"
#include "nvs_flash.h"

extern "C" {
#include "esp32p4_lcd.h"
}

#if !defined(CONFIG_ESP32P4_LCD_70) || !defined(CONFIG_ESP32P4_LCD_NOTOUCH)
#error "The cluster supports the 4D Systems ESP32-P4-70 non-touch panel."
#endif
#if !defined(CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG)
#error "The cluster console must use USB Serial/JTAG."
#endif
#if CONFIG_ESP32P4_REV_MIN_FULL != 0 && CONFIG_ESP32P4_REV_MIN_FULL != 300
#error "Select sdkconfig.rev-prev3 or sdkconfig.rev-v3 for the board silicon."
#endif

namespace cluster::platform {
namespace {

constexpr char kTag[] = "cluster_board";
constexpr uint64_t kSaveDelayMs = 2000;
std::atomic<bool> first_render{false};

void display_refreshed(lv_event_t*)
{
    first_render.store(true, std::memory_order_relaxed);
}

uint16_t pack_preferences(const ViewState& view)
{
    return (static_cast<uint16_t>(view.mode) << 8) | view.brightness_percent;
}

} // namespace

esp_err_t start_display()
{
    constexpr int kPanelWidth = 800;
    constexpr int kPanelHeight = 1280;
    constexpr unsigned kPixelsPerDrawBuffer = 1280 * 100;
    static_assert(CONFIG_ESP32P4_4D_LCD_WIDTH == kPanelWidth);
    static_assert(CONFIG_ESP32P4_4D_LCD_HEIGHT == kPanelHeight);
    ESP_RETURN_ON_FALSE(esp_psram_is_initialized(), ESP_ERR_INVALID_STATE, kTag, "PSRAM unavailable");
    ESP_LOGI(kTag, "Detected %u MiB PSRAM", static_cast<unsigned>(esp_psram_get_size() / (1024 * 1024)));

    esp_lcd_panel_handle_t panel = nullptr;
    ESP_RETURN_ON_ERROR(esp32p4_lcd_full_init(&panel), kTag, "LCD initialization failed");

    lvgl_port_cfg_t port_config = ESP_LVGL_PORT_INIT_CONFIG();
    port_config.task_stack = 12 * 1024;
    port_config.task_max_sleep_ms = 25;
    ESP_RETURN_ON_ERROR(lvgl_port_init(&port_config), kTag, "LVGL task initialization failed");

    // Keep the default LVGL pool in fast internal RAM and add bounded
    // PSRAM capacity for the Tuning history draw tasks and temporary layers.
    constexpr size_t kLvglPoolBytes = CONFIG_LV_MEM_POOL_EXPAND_SIZE_KILOBYTES * 1024;
    void* draw_pool = heap_caps_malloc(kLvglPoolBytes, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    ESP_RETURN_ON_FALSE(draw_pool, ESP_ERR_NO_MEM, kTag, "LVGL PSRAM pool allocation failed");
    if (!lvgl_port_lock(250)) {
        heap_caps_free(draw_pool);
        return ESP_ERR_TIMEOUT;
    }
    const bool pool_registered = lv_mem_add_pool(draw_pool, kLvglPoolBytes) != nullptr;
    lvgl_port_unlock();
    if (!pool_registered) {
        heap_caps_free(draw_pool);
        return ESP_ERR_NO_MEM;
    }

    lvgl_port_display_cfg_t display_config{};
    display_config.panel_handle = panel;
    display_config.buffer_size = kPixelsPerDrawBuffer;
    display_config.double_buffer = true;
    display_config.hres = kPanelWidth;
    display_config.vres = kPanelHeight;
    display_config.color_format = LV_COLOR_FORMAT_RGB565;
    display_config.flags.buff_spiram = true;
    display_config.flags.sw_rotate = true;
    const lvgl_port_display_dsi_cfg_t dsi_config{};
    auto* display = lvgl_port_add_disp_dsi(&display_config, &dsi_config);
    ESP_RETURN_ON_FALSE(display, ESP_ERR_NO_MEM, kTag, "LVGL display registration failed");
    ESP_RETURN_ON_FALSE(lvgl_port_lock(250), ESP_ERR_TIMEOUT, kTag, "LVGL display lock timed out");
#ifdef CONFIG_CLUSTER_PANEL_ROTATE_270
    lv_display_set_rotation(display, LV_DISPLAY_ROTATION_270);
#else
    lv_display_set_rotation(display, LV_DISPLAY_ROTATION_90);
#endif
    bool landscape = lv_display_get_horizontal_resolution(display) == 1280 &&
                     lv_display_get_vertical_resolution(display) == 800;
    lvgl_port_unlock();
    ESP_RETURN_ON_FALSE(landscape, ESP_ERR_INVALID_STATE, kTag, "Unexpected logical LCD resolution");
    return ESP_OK;
}

void await_first_frame()
{
    // Called under the LVGL lock after the dashboard has been created.
    lv_display_add_event_cb(lv_display_get_default(), display_refreshed, LV_EVENT_REFR_READY, nullptr);
}

bool display_ready()
{
    return first_render.load(std::memory_order_relaxed);
}

esp_err_t backlight(uint8_t percent)
{
    return esp32p4_lcd_backlight_set((static_cast<unsigned>(percent) * 255 + 50) / 100);
}

esp_err_t configure_buttons()
{
    gpio_config_t config{};
    config.pin_bit_mask = (uint64_t{1} << kModeButton) | (uint64_t{1} << kBrightnessButton) |
                          (uint64_t{1} << kReplayButton);
    config.mode = GPIO_MODE_INPUT;
    config.pull_up_en = GPIO_PULLUP_ENABLE;
    return gpio_config(&config);
}

ButtonInputs read_buttons()
{
    return {gpio_get_level(kModeButton) == 0, gpio_get_level(kBrightnessButton) == 0,
            gpio_get_level(kReplayButton) == 0};
}

esp_err_t Preferences::load(ViewState& view)
{
    static_assert(sizeof(handle_) == sizeof(nvs_handle_t));
    esp_err_t result = nvs_flash_init();
    if (result != ESP_OK) {
        return result;
    }
    result = nvs_open("cluster", NVS_READWRITE, &handle_);
    if (result != ESP_OK) {
        return result;
    }
    uint16_t saved = 0;
    result = nvs_get_u16(handle_, "prefs", &saved);
    if (result == ESP_OK) {
        const auto mode = saved >> 8;
        const auto brightness = saved & 0xff;
        if (mode <= static_cast<int>(Mode::Tuning) && brightness > 0 && brightness <= 100) {
            view.mode = static_cast<Mode>(mode);
            view.brightness_percent = brightness;
        } else {
            result = ESP_ERR_INVALID_STATE;
        }
    }
    stored_ = pack_preferences(view);
    return result == ESP_ERR_NVS_NOT_FOUND ? ESP_OK : result;
}

void Preferences::changed(uint64_t now)
{
    if (handle_ != 0) {
        save_at_ms_ = now + kSaveDelayMs;
    }
}

PreferenceSaveResult Preferences::save_if_settled(const ViewState& view, uint64_t now)
{
    if (save_at_ms_ == 0 || now < save_at_ms_) {
        return {ESP_OK, false};
    }
    save_at_ms_ = 0;
    const uint16_t packed = pack_preferences(view);
    if (packed == stored_) {
        return {ESP_OK, false};
    }
    esp_err_t result = nvs_set_u16(handle_, "prefs", packed);
    if (result == ESP_OK) {
        result = nvs_commit(handle_);
    }
    if (result == ESP_OK) {
        stored_ = packed;
    }
    return {result, result == ESP_OK};
}

} // namespace cluster::platform
