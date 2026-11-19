#pragma once

#include "cluster/types.hpp"

namespace cluster {

struct ClientConfig {
    bool vss_enabled = false;
    bool oil_enabled = false;
    bool oil_calibrated = false;
    uint32_t ego_delay_ms = 15000;
    uint32_t cycle_ms = 200;
    uint32_t stale_ms = kTelemetryStaleMs;
};

struct TxRequest {
    std::array<uint8_t, 7> bytes{};
    size_t size = 0;
};

class TelemetryClient {
public:
    explicit TelemetryClient(ClientConfig config = {});
    void confirm_ecu_reset(uint64_t now_ms);
    TxRequest tick(uint64_t now_ms);
    void tx_complete(bool fully_written, uint64_t now_ms);
    void receive(const uint8_t* bytes, size_t count, uint64_t now_ms);
    void transport_error(uint64_t now_ms);
    void expire(Snapshot& snapshot, uint64_t now_ms) const;
    bool take_snapshot(Snapshot& out);
    LinkState state() const;

private:
    enum class Phase : uint8_t { Inhibited, Drain, Idle, Writing, Reading, Guard };
    enum class Command : uint8_t { Identity, First, Second };

    void recover(uint64_t now_ms, LinkState link);
    void latch_fault();
    void reset_target_gate();
    bool target_window_elapsed(uint64_t observed_ms) const;
    void finish_response(uint64_t now_ms);
    void publish();
    size_t response_size() const;

    ClientConfig config_;
    Phase phase_ = Phase::Inhibited;
    Command command_ = Command::Identity;
    LinkState link_ = LinkState::AwaitEcuReset;
    uint64_t due_ms_ = 0;
    uint64_t last_rx_ms_ = 0;
    uint64_t deadline_ms_ = 0;
    uint64_t cycle_started_ms_ = 0;
    uint64_t first_observed_ms_ = 0;
    uint64_t last_published_ms_ = 0;
    uint64_t running_since_ms_ = 0;
    uint64_t previous_first_ms_ = 0;
    uint8_t last_uptime_ = 0;
    uint8_t last_sync_losses_ = 0;
    uint32_t rejected_frames_ = 0;
    size_t rx_count_ = 0;
    std::array<uint8_t, 46> rx_{};
    std::array<uint8_t, 44> first_{};
    Snapshot pending_{};
    bool snapshot_pending_ = false;
    bool have_published_ = false;
    bool tracking_run_ = false;
};

} // namespace cluster
