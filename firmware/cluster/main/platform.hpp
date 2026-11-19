#pragma once

#include "cluster/controls.hpp"

#include "driver/gpio.h"
#include "esp_err.h"
#include "esp_timer.h"
#include "sdkconfig.h"

namespace cluster::platform {

inline uint64_t now_ms() { return static_cast<uint64_t>(esp_timer_get_time()) / 1000; }

// Rev 1.4 H4 board assignments. Restrict external pins to the verified bank,
// away from USB, straps, internal LCD/touch/audio and microSD pins.
inline constexpr gpio_num_t kAdcSda = GPIO_NUM_15;
inline constexpr gpio_num_t kAdcScl = GPIO_NUM_16;
inline constexpr gpio_num_t kEcuTx = GPIO_NUM_17;
inline constexpr gpio_num_t kEcuRx = GPIO_NUM_18;
inline constexpr gpio_num_t kModeButton = GPIO_NUM_19;
inline constexpr gpio_num_t kBrightnessButton = GPIO_NUM_20;
inline constexpr gpio_num_t kReplayButton = GPIO_NUM_21;
inline constexpr gpio_num_t kSdData0 = GPIO_NUM_39;
inline constexpr gpio_num_t kSdData1 = GPIO_NUM_40;
inline constexpr gpio_num_t kSdData2 = GPIO_NUM_41;
inline constexpr gpio_num_t kSdData3 = GPIO_NUM_42;
inline constexpr gpio_num_t kSdClk = GPIO_NUM_43;
inline constexpr gpio_num_t kSdCmd = GPIO_NUM_44;
inline constexpr gpio_num_t kSdPowerEnable = GPIO_NUM_45;
inline constexpr gpio_num_t kSdDetect = GPIO_NUM_46;

constexpr bool valid_external_pins()
{
    constexpr gpio_num_t pins[] = {
        kAdcSda, kAdcScl, kEcuTx, kEcuRx, kModeButton, kBrightnessButton, kReplayButton
    };
    uint64_t used = 0;
    for (const gpio_num_t pin : pins) {
        if (pin < GPIO_NUM_15 || pin > GPIO_NUM_21 || !GPIO_IS_VALID_OUTPUT_GPIO(pin)) {
            return false;
        }
        const uint64_t bit = uint64_t{1} << pin;
        if (used & bit) {
            return false;
        }
        used |= bit;
    }
    return true;
}
static_assert(valid_external_pins(), "Cluster H4 pin assignments conflict");

esp_err_t start_display();
void await_first_frame();
bool display_ready();
esp_err_t backlight(uint8_t percent);

esp_err_t configure_buttons();
ButtonInputs read_buttons();

struct PreferenceSaveResult {
    esp_err_t error;
    bool committed;
};

class Preferences {
public:
    esp_err_t load(ViewState& view);
    void changed(uint64_t now_ms);
    PreferenceSaveResult save_if_settled(const ViewState& view, uint64_t now_ms);

private:
    uint32_t handle_ = 0;
    uint16_t stored_ = 0;
    uint64_t save_at_ms_ = 0;
};

#ifdef CONFIG_CLUSTER_LIVE
esp_err_t start_uart();
void confirm_ecu_reset();
bool take_uart_snapshot(Snapshot& snapshot);
#endif

#ifdef CONFIG_CLUSTER_ADS1115
struct LocalSensors {
    Reading fuel;
    Reading oil_temp;
    bool fault = false;
};
esp_err_t start_adc();
bool take_adc_sample(LocalSensors& sample);
#endif

#ifdef CONFIG_CLUSTER_SD_LOGGING
enum class LogState : uint8_t { Starting, Active, Fault };
esp_err_t start_logger();
LogState log_state();
bool enqueue_log(const Snapshot& snapshot);
#endif

} // namespace cluster::platform
