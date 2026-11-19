#pragma once

#include "cluster/types.hpp"

namespace cluster {

constexpr uint32_t kReplayDurationMs = 54425;
Snapshot replay_sample(uint32_t offset_ms, uint64_t now_ms);

} // namespace cluster
