#include "cluster/controls.hpp"

#include <array>

namespace cluster {
namespace {

bool reset_required(LinkState link)
{
    return link == LinkState::AwaitEcuReset || link == LinkState::TransportFault;
}

void cycle_mode(ViewState& view)
{
    switch (view.mode) {
    case Mode::Street:
        view.mode = Mode::Track;
        break;
    case Mode::Track:
        view.mode = Mode::Tuning;
        break;
    case Mode::Tuning:
        view.mode = Mode::Street;
        break;
    }
}

uint8_t next_brightness(uint8_t brightness)
{
    constexpr std::array<uint8_t, 4> kBrightnessLevels{25, 45, 70, 100};
    for (const auto level : kBrightnessLevels) {
        if (level > brightness) {
            return level;
        }
    }
    return kBrightnessLevels.front();
}

} // namespace

bool Controls::Button::update(bool pressed, uint64_t now_ms)
{
    if (pressed != raw) {
        raw = pressed;
        changed_ms = now_ms;
    }
    if (raw != stable && now_ms - changed_ms >= kButtonDebounceMs) {
        stable = raw;
        return true;
    }
    return false;
}

ControlResult Controls::update(ButtonInputs inputs, ViewState& view, uint64_t now_ms)
{
    ControlResult result{};
    const bool needs_reset = reset_required(view.telemetry.link);
    if (mode_.update(inputs.mode_pressed, now_ms)) {
        if (mode_.stable) {
            mode_pressed_ms_ = now_ms;
            mode_held_for_reset_ = needs_reset && mode_reset_armed_;
            reset_confirmed_ = false;
            if (!needs_reset) {
                cycle_mode(view);
                result.preferences_changed = true;
            }
        } else if (mode_held_for_reset_ && !reset_confirmed_) {
            cycle_mode(view);
            result.preferences_changed = true;
        }
    }
    if (!mode_.stable && !mode_.raw && now_ms - mode_.changed_ms >= kButtonDebounceMs) {
        mode_reset_armed_ = true;
    }
    if (mode_.stable && mode_.raw && needs_reset && mode_held_for_reset_ &&
        !reset_confirmed_ && now_ms - mode_pressed_ms_ >= kResetHoldMs) {
        reset_confirmed_ = true;
        result.confirm_ecu_reset = true;
    }
    if (brightness_.update(inputs.brightness_pressed, now_ms) && brightness_.stable) {
        view.brightness_percent = next_brightness(view.brightness_percent);
        result.preferences_changed = true;
    }
    if (replay_.update(inputs.replay_pressed, now_ms) && replay_.stable &&
        view.telemetry.link == LinkState::Replay) {
        view.replay_paused = !view.replay_paused;
    }
    return result;
}

} // namespace cluster
