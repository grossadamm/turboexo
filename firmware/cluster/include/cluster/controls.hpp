#pragma once

#include "cluster/types.hpp"

namespace cluster {

constexpr uint64_t kButtonDebounceMs = 30;
constexpr uint64_t kResetHoldMs = 2000;

struct ButtonInputs {
    bool mode_pressed = false;
    bool brightness_pressed = false;
    bool replay_pressed = false;
};

struct ControlResult {
    bool preferences_changed = false;
    bool confirm_ecu_reset = false;
};

class Controls {
public:
    ControlResult update(ButtonInputs inputs, ViewState& view, uint64_t now_ms);

private:
    struct Button {
        bool update(bool pressed, uint64_t now_ms);

        uint64_t changed_ms = 0;
        bool raw = false;
        bool stable = false;
    };

    Button mode_;
    Button brightness_;
    Button replay_;
    uint64_t mode_pressed_ms_ = 0;
    bool mode_held_for_reset_ = false;
    bool mode_reset_armed_ = false;
    bool reset_confirmed_ = false;
};

} // namespace cluster
