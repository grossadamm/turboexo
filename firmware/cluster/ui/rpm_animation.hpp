#pragma once
#include "cluster/types.hpp"
#include <algorithm>
#include <cmath>
#include <cstdint>

namespace cluster {
// Display-only linear transition. Numeric telemetry and history never use it.
class RpmAnimation {
public:
  float step(bool available, float target, uint64_t now, bool paused,
             LinkState source) {
    if (!available || !std::isfinite(target) ||
        (source != LinkState::Live && source != LinkState::Replay)) {
      initialized_ = false;
      return 0;
    }
    if (!initialized_ || now < last_ms_ || source != source_) {
      initialized_ = true;
      source_ = source;
      current_ = start_ = target_ = target;
      last_ms_ = now;
      elapsed_ = 0;
      was_paused_ = paused;
      return current_;
    }
    const uint64_t delta = now - last_ms_;
    last_ms_ = now;
    if (!paused && !was_paused_) {
      elapsed_ += std::min<uint64_t>(delta, kDurationMs);
      elapsed_ = std::min<uint64_t>(elapsed_, kDurationMs);
      const float fraction = static_cast<float>(elapsed_) / kDurationMs;
      current_ = start_ + (target_ - start_) * fraction;
    }
    was_paused_ = paused;
    if (target != target_) {
      start_ = current_;
      target_ = target;
      elapsed_ = 0;
    }
    return current_;
  }

private:
  static constexpr uint64_t kDurationMs = 80;
  bool initialized_ = false;
  bool was_paused_ = false;
  LinkState source_ = LinkState::AwaitEcuReset;
  uint64_t last_ms_ = 0, elapsed_ = 0;
  float current_ = 0, start_ = 0, target_ = 0;
};
} // namespace cluster
