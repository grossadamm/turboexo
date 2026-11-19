#pragma once

#include "cluster/types.hpp"

namespace cluster {

constexpr uint32_t kReplayDurationMs = 54425;
Snapshot replay_sample(uint32_t offset_ms, uint64_t now_ms);
void replay_history(uint32_t offset_ms, uint64_t now_ms, History& history);

struct ReplayAdvance {
    bool changed = false;
    bool wrapped = false;
    bool reached_end = false;
};

// Pause-adjusted presentation clock. The endpoint must be presented before
// the next loop starts, even if a display frame crosses the recording end.
class ReplayTimeline {
public:
    void reset(uint64_t wall_ms, uint32_t offset_ms = 0);
    ReplayAdvance advance(uint64_t wall_ms, bool paused);
    void presented();
    uint32_t offset_ms() const { return offset_ms_; }
    uint64_t now_ms() const { return presentation_ms_; }
private:
    uint64_t last_wall_ms_ = 0;
    uint64_t presentation_ms_ = 0;
    uint32_t offset_ms_ = 0;
    bool endpoint_presented_ = false;
};

} // namespace cluster
