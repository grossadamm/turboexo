#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

namespace cluster {

enum class Mode : uint8_t { Street, Track, Tuning };
enum class Quality : uint8_t { Missing, Valid, Unverified, Simulated };
enum class Metric : uint8_t {
    Rpm, SpeedMph, OilPsi, CoolantF, FuelPercent, OilTempF, MapKpa, BoostPsi,
    TpsPercent, AfrRaw, AfrTarget, AdvanceDeg, PulseWidthMs, InjectorDutyPercent,
    IatF, BatteryV, EgoCorrectionPercent, WarmupPercent, Aux0Raw, Count
};
constexpr size_t kMetricCount = static_cast<size_t>(Metric::Count);
constexpr size_t metric_index(Metric metric) { return static_cast<size_t>(metric); }
constexpr uint64_t kTelemetryStaleMs = 1000;
constexpr uint64_t kHistoryWindowMs = 8000;
constexpr size_t kHistoryCapacity = 256;

struct Reading {
    float value = 0;
    Quality quality = Quality::Missing;
    uint64_t observed_ms = 0;
    bool present() const { return quality != Quality::Missing; }
};

enum class LinkState : uint8_t {
    Replay, AwaitEcuReset, Connecting, Live, Stale, Unsupported, TransportFault
};

struct Snapshot {
    std::array<Reading, kMetricCount> values{};
    uint64_t received_ms = 0;
    LinkState link = LinkState::AwaitEcuReset;
    uint8_t engine_flags = 0;
    uint8_t protection_flags = 0;
    uint8_t sync_loss_count = 0;
    uint8_t ecu_uptime_seconds = 0;
    uint16_t ecu_loops_per_second = 0;
    bool synchronized = false;
    bool target_echo_possible = true;
    uint32_t rejected_frames = 0;
    const Reading& get(Metric metric) const { return values[metric_index(metric)]; }
    Reading& get(Metric metric) { return values[metric_index(metric)]; }
    void set(Metric metric, float value, Quality quality, uint64_t now_ms) {
        get(metric) = {value, quality, now_ms};
    }
};

struct HistoryPoint {
    uint64_t time_ms = 0;
    float rpm = 0;
    float map_kpa = 0;
    float tps_percent = 0;
    uint8_t valid_mask = 0; // RPM=1, MAP=2, TPS=4; zero marks an explicit gap.
};

class History {
public:
    void append(const Snapshot& snapshot, uint64_t now_ms);
    void clear();
    size_t size() const { return count_; }
    const HistoryPoint& at(size_t chronological_index) const;
private:
    std::array<HistoryPoint, kHistoryCapacity> points_{};
    size_t head_ = 0;
    size_t count_ = 0;
    uint64_t last_observed_ms_ = 0;
    bool have_observation_ = false;
};

enum PeripheralFault : uint8_t {
    ButtonsFault = 1, AdcFault = 2, PreferencesFault = 4, UartFault = 8
};

struct ViewState {
    Snapshot telemetry{};
    Mode mode = Mode::Street;
    uint8_t brightness_percent = 70;
    bool replay_paused = false;
    uint8_t peripheral_faults = 0;
    bool logging_active = false;
    bool logging_fault = false;
    uint32_t log_dropped = 0;
};

} // namespace cluster
