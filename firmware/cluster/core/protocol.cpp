#include "cluster/protocol.hpp"

#include <algorithm>
#include <string_view>

namespace cluster {
namespace {

constexpr uint64_t kQuietMs = 12;
constexpr uint64_t kResponseDeadlineMs = 120;
constexpr uint64_t kRecoveryMs = 300;
constexpr uint32_t kMinimumCycleMs = 200;
constexpr uint64_t kExtraEgoDelayMs = 1000;
constexpr float kKpaPerPsi = 6.894757f;
constexpr float kMphPerKph = 0.621371192f;
constexpr TxRequest kIdentity{{'S'}, 1};
constexpr TxRequest kReadFirst{{'r', 0, 0x30, 0, 0, 44, 0}, 7};
constexpr TxRequest kReadSecond{{'r', 0, 0x30, 76, 0, 33, 0}, 7};

uint16_t read_u16(const uint8_t* bytes)
{
    return static_cast<uint16_t>(bytes[0] | (bytes[1] << 8));
}

int read_s8(uint8_t byte)
{
    return byte < 128 ? byte : static_cast<int>(byte) - 256;
}

float temp_f(uint8_t value)
{
    return (static_cast<int>(value) - 40) * 1.8f + 32;
}

void set_plausible(Snapshot& out, Metric metric, float value, float min, float max,
                   uint64_t observed_ms, Quality quality = Quality::Valid)
{
    if (value >= min && value <= max) {
        out.set(metric, value, quality, observed_ms);
    }
}

bool age_elapsed(uint64_t now, uint64_t then, uint64_t duration)
{
    return now < then || now - then >= duration;
}

bool looks_like_restart(uint8_t uptime, uint8_t previous_uptime, uint64_t elapsed_ms)
{
    // The first observation can occur anywhere within an ECU second.
    // Modular subtraction handles adjacent values across a normal wrap.
    const auto increments = static_cast<uint8_t>(uptime - previous_uptime);
    return increments > elapsed_ms / 1000 + 1;
}

} // namespace

TelemetryClient::TelemetryClient(ClientConfig config) : config_(config)
{
    config_.cycle_ms = std::max(config_.cycle_ms, kMinimumCycleMs);
    if (config_.stale_ms == 0) {
        config_.stale_ms = kTelemetryStaleMs;
    }
}

void TelemetryClient::confirm_ecu_reset(uint64_t now_ms)
{
    if (phase_ != Phase::Inhibited) {
        return;
    }

    recover(now_ms, LinkState::Connecting);
    due_ms_ = now_ms;
}

TxRequest TelemetryClient::tick(uint64_t now_ms)
{
    if (link_ == LinkState::Live &&
        age_elapsed(now_ms, last_published_ms_, config_.stale_ms)) {
        link_ = LinkState::Stale;
        snapshot_pending_ = false;
        reset_target_gate();
    }

    if (phase_ == Phase::Inhibited) {
        return {};
    }
    if (phase_ == Phase::Drain && now_ms >= due_ms_ && now_ms - last_rx_ms_ >= kQuietMs) {
        phase_ = Phase::Idle;
    }
    if (phase_ == Phase::Writing && now_ms >= deadline_ms_) {
        latch_fault();
    }
    if (phase_ == Phase::Guard && now_ms - last_rx_ms_ >= kQuietMs) {
        const bool stale_reply = age_elapsed(now_ms, last_rx_ms_, config_.stale_ms);
        const bool stale_cycle = command_ == Command::Second &&
                                 age_elapsed(now_ms, first_observed_ms_, config_.stale_ms);
        if (stale_reply || stale_cycle) {
            ++rejected_frames_;
            recover(now_ms, LinkState::Stale);
        } else {
            finish_response(now_ms);
        }
    } else if (phase_ == Phase::Reading && now_ms >= deadline_ms_) {
        ++rejected_frames_;
        recover(now_ms, LinkState::Stale);
    }
    if (phase_ != Phase::Idle || now_ms < due_ms_) {
        return {};
    }

    phase_ = Phase::Writing;
    deadline_ms_ = now_ms + kResponseDeadlineMs;
    rx_count_ = 0;
    switch (command_) {
    case Command::Identity:
        return kIdentity;
    case Command::First:
        cycle_started_ms_ = now_ms;
        return kReadFirst;
    case Command::Second:
        return kReadSecond;
    }
    return {};
}

void TelemetryClient::tx_complete(bool fully_written, uint64_t now_ms)
{
    if (phase_ != Phase::Writing) {
        return;
    }
    if (!fully_written) {
        latch_fault();
        return;
    }
    phase_ = Phase::Reading;
    deadline_ms_ = now_ms + kResponseDeadlineMs;
}

void TelemetryClient::receive(const uint8_t* bytes, size_t count, uint64_t now_ms)
{
    if (count == 0 || phase_ == Phase::Inhibited) {
        return;
    }
    last_rx_ms_ = now_ms;
    if (phase_ == Phase::Drain) {
        return;
    }
    if (phase_ == Phase::Writing) {
        latch_fault();
        return;
    }

    const size_t expected_size = response_size();
    if ((phase_ != Phase::Reading && phase_ != Phase::Guard) ||
        now_ms >= deadline_ms_ || count > expected_size - rx_count_) {
        ++rejected_frames_;
        recover(now_ms, LinkState::Stale);
        return;
    }
    std::copy_n(bytes, count, rx_.begin() + rx_count_);
    rx_count_ += count;

    if (command_ == Command::Identity) {
        if (rx_count_ >= 17) {
            phase_ = Phase::Guard;
        }
        return;
    }

    if (rx_[0] != 'r' || (rx_count_ >= 2 && rx_[1] != 0x30)) {
        ++rejected_frames_;
        recover(now_ms, LinkState::Stale);
        return;
    }
    if (rx_count_ == expected_size) {
        phase_ = Phase::Guard;
    }
}

void TelemetryClient::transport_error(uint64_t now_ms)
{
    if (phase_ == Phase::Writing) {
        latch_fault();
    } else if (phase_ != Phase::Inhibited) {
        ++rejected_frames_;
        recover(now_ms, LinkState::Stale);
    }
}

void TelemetryClient::expire(Snapshot& snapshot, uint64_t now_ms) const
{
    snapshot.link = state();
    if (snapshot.link == LinkState::Live &&
        age_elapsed(now_ms, last_published_ms_, config_.stale_ms)) {
        snapshot.link = LinkState::Stale;
    }
    snapshot.rejected_frames = rejected_frames_;
    for (auto& reading : snapshot.values) {
        if (reading.present() && age_elapsed(now_ms, reading.observed_ms, config_.stale_ms)) {
            reading.quality = Quality::Missing;
        }
    }
    if (snapshot.link != LinkState::Live || !target_window_elapsed(previous_first_ms_) ||
        age_elapsed(now_ms, previous_first_ms_, config_.stale_ms)) {
        snapshot.get(Metric::AfrTarget).quality = Quality::Missing;
        snapshot.target_echo_possible = true;
    }
}

bool TelemetryClient::take_snapshot(Snapshot& out)
{
    if (!snapshot_pending_) {
        return false;
    }
    out = pending_;
    snapshot_pending_ = false;
    return true;
}

LinkState TelemetryClient::state() const
{
    return link_;
}

void TelemetryClient::recover(uint64_t now_ms, LinkState link)
{
    phase_ = Phase::Drain;
    command_ = Command::Identity;
    link_ = link;
    due_ms_ = now_ms + kRecoveryMs;
    last_rx_ms_ = now_ms;
    rx_count_ = 0;
    snapshot_pending_ = false;
    have_published_ = false;
    reset_target_gate();
}

void TelemetryClient::latch_fault()
{
    phase_ = Phase::Inhibited;
    link_ = LinkState::TransportFault;
    snapshot_pending_ = false;
    have_published_ = false;
    reset_target_gate();
}

void TelemetryClient::reset_target_gate()
{
    tracking_run_ = false;
}

bool TelemetryClient::target_window_elapsed(uint64_t observed_ms) const
{
    return tracking_run_ && observed_ms >= running_since_ms_ &&
           observed_ms - running_since_ms_ >= config_.ego_delay_ms + kExtraEgoDelayMs;
}

size_t TelemetryClient::response_size() const
{
    switch (command_) {
    case Command::Identity:
        return 19;
    case Command::First:
        return 46;
    case Command::Second:
        return 35;
    }
    return 0;
}

void TelemetryClient::finish_response(uint64_t now_ms)
{
    phase_ = Phase::Idle;
    due_ms_ = now_ms;
    switch (command_) {
    case Command::Identity: {
        const std::string_view identity(reinterpret_cast<const char*>(rx_.data()), rx_count_);
        if (identity != "Speeduino 2025.01" && identity != "Speeduino 2025.01.6" &&
            identity != "Speeduino 2025.01.7") {
            ++rejected_frames_;
            recover(now_ms, LinkState::Unsupported);
            return;
        }
        command_ = Command::First;
        return;
    }
    case Command::First:
        std::copy_n(rx_.begin() + 2, first_.size(), first_.begin());
        first_observed_ms_ = last_rx_ms_;
        command_ = Command::Second;
        return;
    case Command::Second:
        publish();
        command_ = Command::First;
        due_ms_ = cycle_started_ms_ + config_.cycle_ms;
        return;
    }
}

void TelemetryClient::publish()
{
    const uint8_t* first = first_.data();
    const uint8_t* second = rx_.data() + 2;
    const uint64_t first_ms = first_observed_ms_;
    const uint64_t second_ms = last_rx_ms_;
    const uint8_t uptime = first[0];
    const uint8_t squirts = second[8] >> 5;
    const uint16_t rpm = read_u16(first + 14);
    const uint16_t pw_us = read_u16(second);
    const float map = read_u16(first + 4);
    const float baro = first[41];

    Snapshot next{};
    next.received_ms = second_ms;
    next.link = LinkState::Live;
    next.engine_flags = first[2];
    next.sync_loss_count = first[3];
    next.protection_flags = second[9];
    next.synchronized = (first[32] & 0x80) || (second[8] & 0x10);
    next.ecu_uptime_seconds = uptime;
    next.ecu_loops_per_second = read_u16(first + 26);
    next.rejected_frames = rejected_frames_;

    const bool restart = have_published_ &&
                         looks_like_restart(uptime, last_uptime_, first_ms - previous_first_ms_);
    const bool sync_loss = have_published_ && next.sync_loss_count != last_sync_losses_;
    const bool continuous = tracking_run_ && !restart && !sync_loss &&
                            !age_elapsed(first_ms, previous_first_ms_, config_.stale_ms);
    const bool running = (next.engine_flags & 0x01) && !(next.engine_flags & 0x02);
    tracking_run_ = running && next.synchronized;
    if (tracking_run_ && !continuous) {
        running_since_ms_ = first_ms;
    }
    next.target_echo_possible = !target_window_elapsed(first_ms);

    set_plausible(next, Metric::Rpm, rpm, 0, 16000, first_ms);
    set_plausible(next, Metric::MapKpa, map, 1, 500, first_ms);
    if (next.get(Metric::MapKpa).present() && baro >= 10 && baro <= 150) {
        next.set(Metric::BoostPsi, (map - baro) / kKpaPerPsi, Quality::Valid, first_ms);
    }
    set_plausible(next, Metric::IatF, temp_f(first[6]), -40, 320, first_ms);
    set_plausible(next, Metric::CoolantF, temp_f(first[7]), -40, 355, first_ms);
    set_plausible(next, Metric::BatteryV, first[9] / 10.0f, 1, 24, first_ms);
    set_plausible(next, Metric::AfrRaw, first[10] / 10.0f, 5, 25.5f, first_ms, Quality::Unverified);
    if (!next.target_echo_possible) {
        set_plausible(next, Metric::AfrTarget, first[21] / 10.0f, 5, 25.5f, first_ms);
    }
    next.set(Metric::EgoCorrectionPercent, first[11], Quality::Valid, first_ms);
    next.set(Metric::WarmupPercent, first[13], Quality::Valid, first_ms);
    next.set(Metric::AdvanceDeg, read_s8(first[24]), Quality::Valid, first_ms);
    set_plausible(next, Metric::TpsPercent, first[25] * 0.5f, 0, 100, first_ms);
    next.set(Metric::Aux0Raw, read_u16(first + 42), Quality::Unverified, first_ms);

    next.set(Metric::PulseWidthMs, pw_us / 1000.0f, Quality::Valid, second_ms);
    if (next.get(Metric::Rpm).present() && squirts != 0) {
        const float duty = static_cast<float>(pw_us) * rpm * squirts / 1200000;
        next.set(Metric::InjectorDutyPercent, duty, Quality::Valid, first_ms);
    }
    if (config_.vss_enabled) {
        set_plausible(next, Metric::SpeedMph, read_u16(second + 28) * kMphPerKph,
                      0, 300, second_ms);
    }
    if (config_.oil_enabled) {
        set_plausible(next, Metric::OilPsi, second[32], 0, 100, second_ms,
                      config_.oil_calibrated ? Quality::Valid : Quality::Unverified);
    }

    pending_ = next;
    snapshot_pending_ = true;
    have_published_ = true;
    link_ = LinkState::Live;
    last_published_ms_ = second_ms;
    previous_first_ms_ = first_ms;
    last_uptime_ = uptime;
    last_sync_losses_ = next.sync_loss_count;
}

} // namespace cluster
