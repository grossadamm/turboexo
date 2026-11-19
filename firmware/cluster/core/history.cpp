#include "cluster/types.hpp"

#include <algorithm>

namespace cluster {
namespace {

bool is_fresh(const Reading& value, uint64_t now_ms)
{
    return value.present() && now_ms >= value.observed_ms &&
           now_ms - value.observed_ms < kTelemetryStaleMs;
}

} // namespace

void History::append(const Snapshot& snapshot, uint64_t now_ms)
{
    if (count_ != 0 && now_ms < at(count_ - 1).time_ms) {
        clear();
    }

    const auto push = [this](const HistoryPoint& point) {
        points_[head_] = point;
        head_ = (head_ + 1) % kHistoryCapacity;
        count_ = std::min(count_ + 1, kHistoryCapacity);
    };
    const auto& rpm = snapshot.get(Metric::Rpm);
    const auto& map = snapshot.get(Metric::MapKpa);
    const auto& tps = snapshot.get(Metric::TpsPercent);
    const bool readable = snapshot.link == LinkState::Live || snapshot.link == LinkState::Replay;
    const bool rpm_valid = readable && is_fresh(rpm, now_ms);
    const bool map_valid = readable && is_fresh(map, now_ms);
    const bool tps_valid = readable && is_fresh(tps, now_ms);
    const auto mask = static_cast<uint8_t>((rpm_valid ? 1 : 0) |
                                           (map_valid ? 2 : 0) |
                                           (tps_valid ? 4 : 0));
    if (mask == 0) {
        if (count_ != 0 && at(count_ - 1).valid_mask != 0) {
            push({now_ms});
        }
        have_observation_ = false;
    } else {
        const uint64_t observed_ms = std::max({rpm_valid ? rpm.observed_ms : 0,
                                               map_valid ? map.observed_ms : 0,
                                               tps_valid ? tps.observed_ms : 0});
        if (!have_observation_ || observed_ms != last_observed_ms_ ||
            count_ == 0 || mask != at(count_ - 1).valid_mask) {
            if (have_observation_ && observed_ms < last_observed_ms_) {
                clear();
            }
            if (have_observation_ && observed_ms - last_observed_ms_ >= kTelemetryStaleMs) {
                push({last_observed_ms_ + kTelemetryStaleMs});
            }
            const uint64_t point_ms = count_ == 0 ? observed_ms :
                                      std::max(observed_ms, at(count_ - 1).time_ms);
            push({point_ms, rpm.value, map.value, tps.value, mask});
            last_observed_ms_ = observed_ms;
            have_observation_ = true;
        }
    }
    while (count_ != 0 && now_ms - at(0).time_ms > kHistoryWindowMs) {
        --count_;
    }
}

void History::clear()
{
    head_ = 0;
    count_ = 0;
    have_observation_ = false;
}

const HistoryPoint& History::at(size_t chronological_index) const
{
    return points_[(head_ + kHistoryCapacity - count_ + chronological_index) % kHistoryCapacity];
}

} // namespace cluster
