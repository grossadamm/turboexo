#include "cluster/replay.hpp"
#include "../generated/replay_data.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <iterator>

namespace cluster {
namespace {

using replay_data::samples;
static_assert(samples[std::size(samples) - 1].offset_ms == kReplayDurationMs);
static_assert(replay_data::history_window_ms == kHistoryWindowMs);
static_assert(replay_data::max_history_rows <= kHistoryCapacity);

float replay_speed(uint32_t offset_ms)
{
    struct Key {
        uint32_t offset_ms;
        float speed_mph;
    };
    constexpr std::array<Key, 7> keys{{
        {0, 32}, {12000, 46}, {20000, 64}, {28000, 78}, {33000, 92},
        {42000, 55}, {kReplayDurationMs, 30},
    }};
    const auto* end = std::lower_bound(keys.data() + 1, keys.data() + keys.size(), offset_ms,
                                       [](const Key& key, uint32_t offset) {
                                           return key.offset_ms < offset;
                                       });
    const auto& start = *(end - 1);
    const float progress = static_cast<float>(offset_ms - start.offset_ms) /
                           (end->offset_ms - start.offset_ms);
    const float smooth = progress * progress * (3 - 2 * progress);
    return start.speed_mph + (end->speed_mph - start.speed_mph) * smooth;
}

} // namespace

Snapshot replay_sample(uint32_t offset_ms, uint64_t now_ms)
{
    offset_ms = std::min(offset_ms, kReplayDurationMs);
    const auto* next = std::upper_bound(std::begin(samples), std::end(samples), offset_ms,
                                        [](uint32_t offset, const replay_data::Sample& row) {
                                            return offset < row.offset_ms;
                                        });
    const auto& row = *(next - 1);
    const uint64_t age_ms = offset_ms - row.offset_ms;
    const uint64_t sample_ms = now_ms >= age_ms ? now_ms - age_ms : 0;

    Snapshot snapshot{};
    snapshot.link = LinkState::Replay;
    snapshot.received_ms = sample_ms;
    snapshot.synchronized = row.sync != 0;
    // The replay presents the recorded target with unverified quality.
    snapshot.target_echo_possible = false;
    snapshot.set(Metric::Rpm, row.rpm, Quality::Valid, sample_ms);
    snapshot.set(Metric::MapKpa, row.map, Quality::Valid, sample_ms);
    snapshot.set(Metric::BoostPsi, (row.map - row.baro) * 0.1450377f, Quality::Valid, sample_ms);
    snapshot.set(Metric::OilPsi, row.oil, Quality::Unverified, sample_ms);
    snapshot.set(Metric::CoolantF, row.coolant, Quality::Valid, sample_ms);
    snapshot.set(Metric::BatteryV, row.battery, Quality::Valid, sample_ms);
    snapshot.set(Metric::TpsPercent, row.tps, Quality::Valid, sample_ms);
    snapshot.set(Metric::AfrRaw, row.afr, Quality::Unverified, sample_ms);
    snapshot.set(Metric::AfrTarget, row.target, Quality::Unverified, sample_ms);
    snapshot.set(Metric::AdvanceDeg, row.advance, Quality::Valid, sample_ms);
    snapshot.set(Metric::PulseWidthMs, row.pw, Quality::Valid, sample_ms);
    snapshot.set(Metric::InjectorDutyPercent, row.duty, Quality::Valid, sample_ms);
    snapshot.set(Metric::IatF, row.iat, Quality::Valid, sample_ms);
    snapshot.set(Metric::EgoCorrectionPercent, row.ego, Quality::Valid, sample_ms);
    snapshot.set(Metric::WarmupPercent, row.warmup, Quality::Valid, sample_ms);

    constexpr float kPi = 3.14159265358979323846f;
    const float position = static_cast<float>(offset_ms) / kReplayDurationMs;
    snapshot.set(Metric::SpeedMph, replay_speed(offset_ms), Quality::Simulated, now_ms);
    snapshot.set(Metric::FuelPercent, 62 - 0.2f * position, Quality::Simulated, now_ms);
    snapshot.set(Metric::OilTempF, 206 + 6 * std::sin(position * kPi), Quality::Simulated, now_ms);
    return snapshot;
}

void replay_history(uint32_t offset_ms, uint64_t now_ms, History& history)
{
    offset_ms = std::min(offset_ms, kReplayDurationMs);
    const uint32_t window_start = offset_ms > kHistoryWindowMs ?
                                  offset_ms - static_cast<uint32_t>(kHistoryWindowMs) : 0;
    history.clear();
    for (const auto& row : samples) {
        if (row.offset_ms < window_start) {
            continue;
        }
        if (row.offset_ms > offset_ms) {
            break;
        }
        const uint64_t age_ms = offset_ms - row.offset_ms;
        if (age_ms <= now_ms) {
            history.append_recorded({now_ms - age_ms, row.rpm, row.map, row.tps, 7}, now_ms);
        }
    }
}

void ReplayTimeline::reset(uint64_t wall_ms, uint32_t offset_ms)
{
    last_wall_ms_ = presentation_ms_ = wall_ms;
    offset_ms_ = std::min(offset_ms, kReplayDurationMs);
    endpoint_presented_ = false;
}

ReplayAdvance ReplayTimeline::advance(uint64_t wall_ms, bool paused)
{
    const uint64_t delta = wall_ms >= last_wall_ms_ ? wall_ms - last_wall_ms_ : 0;
    last_wall_ms_ = wall_ms;
    if (paused) {
        return {};
    }
    if (offset_ms_ == kReplayDurationMs) {
        if (!endpoint_presented_) {
            return {};
        }
        offset_ms_ = 0;
        endpoint_presented_ = false;
        presentation_ms_ += delta;
        return {true, true, false};
    }
    const uint64_t step = std::min<uint64_t>(delta, kReplayDurationMs - offset_ms_);
    offset_ms_ += static_cast<uint32_t>(step);
    presentation_ms_ += step;
    return {step != 0, false, offset_ms_ == kReplayDurationMs};
}

void ReplayTimeline::presented()
{
    if (offset_ms_ == kReplayDurationMs) {
        endpoint_presented_ = true;
    }
}

} // namespace cluster
