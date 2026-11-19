#pragma once

#include "cluster/types.hpp"

namespace cluster {

// ECU and local ADC samples have independent clocks. Logging must observe
// either source, including a quality transition when a source stops updating.
inline bool has_new_observation(const Snapshot& before, const Snapshot& after)
{
    if (before.received_ms != after.received_ms || before.link != after.link ||
        before.engine_flags != after.engine_flags ||
        before.protection_flags != after.protection_flags ||
        before.sync_loss_count != after.sync_loss_count ||
        before.synchronized != after.synchronized ||
        before.target_echo_possible != after.target_echo_possible ||
        before.rejected_frames != after.rejected_frames) {
        return true;
    }
    for (size_t i = 0; i < kMetricCount; ++i) {
        const auto& old = before.values[i];
        const auto& current = after.values[i];
        if (old.quality != current.quality ||
            (current.present() && (old.observed_ms != current.observed_ms ||
                                   old.value != current.value))) {
            return true;
        }
    }
    return false;
}

} // namespace cluster
