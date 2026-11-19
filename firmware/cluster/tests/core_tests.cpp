#include "cluster/calibration.hpp"
#include "cluster/controls.hpp"
#include "cluster/protocol.hpp"
#include "cluster/observations.hpp"
#include "cluster/replay.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <string_view>

namespace {

using namespace cluster;

constexpr uint64_t kQuiet = 12;
constexpr uint64_t kDeadline = 120;
constexpr uint64_t kBackoff = 300;
constexpr uint64_t kCycle = 200;
constexpr std::string_view kBaseIdentity = "Speeduino 2025.01";
constexpr std::array<uint8_t, 7> kFirst{'r', 0, 0x30, 0, 0, 44, 0};
constexpr std::array<uint8_t, 7> kSecond{'r', 0, 0x30, 76, 0, 33, 0};

void check(bool passed, const char* expression, int line)
{
    if (!passed) {
        std::cerr << "line " << line << ": " << expression << '\n';
        std::abort();
    }
}

#define CHECK(expression) check((expression), #expression, __LINE__)

void near(float actual, float expected, float tolerance = 0.001f)
{
    if (!(std::abs(actual - expected) <= tolerance)) {
        std::cerr << "Expected " << expected << ", got " << actual << '\n';
        std::abort();
    }
}

struct Frames {
    std::array<uint8_t, 46> first{};
    std::array<uint8_t, 35> second{};

    Frames()
    {
        first[0] = second[0] = 'r';
        first[1] = second[1] = 0x30;
        first[2] = 254;
        first[4] = 1;
        first[5] = 3;
        first[6] = 0x2c;
        first[7] = 1;
        first[8] = 0x23;
        first[9] = 0x76;
        first[11] = 138;
        first[12] = 131;
        first[13] = 101;
        first[15] = 112;
        first[16] = 0x34;
        first[17] = 0x12;
        first[18] = 'r'; // Embedded header remains ordinary payload.
        first[19] = 0x30;
        first[23] = 142;
        first[26] = 0xf9;
        first[27] = 75;
        first[28] = 0x34;
        first[29] = 0x12;
        first[34] = 0x80;
        first[43] = 99;
        first[44] = 0x56;
        first[45] = 2;
        second[2] = 0xe8;
        second[3] = 3;
        second[10] = 0x40;
        second[11] = 0x85;
        second[30] = 0x2d;
        second[31] = 1;
        second[34] = 55;
    }
};

void expect_identity(TxRequest request)
{
    CHECK(request.size == 1);
    CHECK(request.bytes[0] == 'S');
}

void expect_read(TxRequest request, const std::array<uint8_t, 7>& expected)
{
    CHECK(request.size == expected.size());
    CHECK(request.bytes == expected);
}

void feed_identity(TelemetryClient& client, std::string_view identity, uint64_t now_ms)
{
    client.receive(reinterpret_cast<const uint8_t*>(identity.data()), identity.size(), now_ms);
}

// Returns the time at which the first request has been issued.
uint64_t connect(TelemetryClient& client, uint64_t now_ms = 0,
                 std::string_view identity = kBaseIdentity)
{
    client.confirm_ecu_reset(now_ms);
    CHECK(client.state() == LinkState::Connecting);
    CHECK(client.tick(now_ms + kQuiet - 1).size == 0);
    now_ms += kQuiet;
    expect_identity(client.tick(now_ms));
    CHECK(client.tick(now_ms).size == 0);
    client.tx_complete(true, now_ms);
    feed_identity(client, identity, now_ms + 1);
    CHECK(client.tick(now_ms + kQuiet).size == 0);
    now_ms += 1 + kQuiet;
    expect_read(client.tick(now_ms), kFirst);
    return now_ms;
}

Snapshot cycle(TelemetryClient& client, uint64_t start_ms, const Frames& frames)
{
    client.tx_complete(true, start_ms);
    // Exercise every split point in the first reply, including the header.
    for (const auto& byte : frames.first) {
        client.receive(&byte, 1, start_ms + 4);
    }
    CHECK(client.tick(start_ms + 4 + kQuiet - 1).size == 0);
    const uint64_t second_request_ms = start_ms + 4 + kQuiet;
    expect_read(client.tick(second_request_ms), kSecond);
    client.tx_complete(true, second_request_ms);
    Snapshot out;
    CHECK(!client.take_snapshot(out));
    client.receive(frames.second.data(), 9, second_request_ms + 1);
    client.receive(frames.second.data() + 9, frames.second.size() - 9, second_request_ms + 3);
    CHECK(client.tick(second_request_ms + 3 + kQuiet - 1).size == 0);
    CHECK(!client.take_snapshot(out));
    CHECK(client.tick(second_request_ms + 3 + kQuiet).size == 0);
    CHECK(client.take_snapshot(out));
    CHECK(!client.take_snapshot(out));
    return out;
}

void test_disarmed_and_identity()
{
    TelemetryClient client;
    const uint8_t noise = 0xff;
    client.receive(&noise, 1, 1);
    client.transport_error(2);
    CHECK(client.state() == LinkState::AwaitEcuReset);
    CHECK(client.tick(10000).size == 0);
    client.confirm_ecu_reset(10001);
    client.receive(&noise, 1, 10012);
    CHECK(client.tick(10023).size == 0);
    expect_identity(client.tick(10024));
    client.tx_complete(true, 10024);
    feed_identity(client, kBaseIdentity, 10025);
    CHECK(client.tick(10034).size == 0);
    feed_identity(client, ".", 10035);
    CHECK(client.tick(10044).size == 0);
    feed_identity(client, "7", 10045);
    CHECK(client.tick(10056).size == 0);
    expect_read(client.tick(10057), kFirst);

    TelemetryClient patch_six;
    connect(patch_six, 0, "Speeduino 2025.01.6");
    for (const auto invalid : {"Speeduino 2025.01.5", "Speeduino 2025.01.", "Speeduino 202501 ",
                               "Speeduino 2025.01.60", "speeduino 2025.01"}) {
        TelemetryClient unsupported;
        unsupported.confirm_ecu_reset(0);
        expect_identity(unsupported.tick(kQuiet));
        unsupported.tx_complete(true, kQuiet);
        feed_identity(unsupported, invalid, 13);
        CHECK(unsupported.tick(25).size == 0);
        CHECK(unsupported.state() == (std::string_view(invalid).size() > 19 ?
                                     LinkState::Stale : LinkState::Unsupported));
        expect_identity(unsupported.tick(25 + kBackoff));
    }
}

void test_decode_and_freshness()
{
    TelemetryClient client({true, true, true});
    const auto start = connect(client);
    auto snapshot = cycle(client, start, Frames{});
    CHECK(snapshot.link == LinkState::Live);
    CHECK(snapshot.engine_flags == 1);
    CHECK(snapshot.protection_flags == 0x85);
    CHECK(snapshot.sync_loss_count == 3);
    CHECK(snapshot.ecu_uptime_seconds == 254);
    CHECK(snapshot.ecu_loops_per_second == 4660);
    CHECK(snapshot.synchronized);
    CHECK(snapshot.target_echo_possible);
    CHECK(!snapshot.get(Metric::AfrTarget).present());
    CHECK(!snapshot.get(Metric::FuelPercent).present());
    CHECK(!snapshot.get(Metric::OilTempF).present());
    CHECK(snapshot.get(Metric::AfrRaw).quality == Quality::Unverified);
    CHECK(snapshot.get(Metric::Aux0Raw).quality == Quality::Unverified);
    CHECK(snapshot.get(Metric::OilPsi).quality == Quality::Valid);
    CHECK(snapshot.get(Metric::Rpm).observed_ms == start + 4);
    CHECK(snapshot.get(Metric::OilPsi).observed_ms == snapshot.received_ms);
    near(snapshot.get(Metric::Rpm).value, 4660);
    near(snapshot.get(Metric::MapKpa).value, 300);
    near(snapshot.get(Metric::BoostPsi).value, 201 / 6.894757f);
    near(snapshot.get(Metric::IatF).value, 23);
    near(snapshot.get(Metric::CoolantF).value, 172.4f);
    near(snapshot.get(Metric::BatteryV).value, 13.8f);
    near(snapshot.get(Metric::AfrRaw).value, 13.1f);
    near(snapshot.get(Metric::EgoCorrectionPercent).value, 101);
    near(snapshot.get(Metric::WarmupPercent).value, 112);
    near(snapshot.get(Metric::AdvanceDeg).value, -7);
    near(snapshot.get(Metric::TpsPercent).value, 37.5f);
    near(snapshot.get(Metric::Aux0Raw).value, 598);
    near(snapshot.get(Metric::PulseWidthMs).value, 1);
    near(snapshot.get(Metric::InjectorDutyPercent).value, 7.766667f);
    near(snapshot.get(Metric::SpeedMph).value, 187.03273f);
    near(snapshot.get(Metric::OilPsi).value, 55);

    client.expire(snapshot, start + 1003);
    CHECK(snapshot.get(Metric::Rpm).present());
    client.expire(snapshot, start + 1004);
    CHECK(!snapshot.get(Metric::Rpm).present());
    CHECK(snapshot.get(Metric::OilPsi).present());
    CHECK(snapshot.link == LinkState::Live);
    client.tick(snapshot.received_ms + 1000);
    client.expire(snapshot, snapshot.received_ms + 1000);
    CHECK(snapshot.link == LinkState::Stale);
    CHECK(!snapshot.get(Metric::OilPsi).present());
    CHECK(snapshot.protection_flags == 0x85);
}

void test_independent_quality()
{
    Frames frames;
    frames.first[6] = frames.first[7] = 0xff;
    frames.first[27] = 255;
    frames.second[10] = 0x10; // Half sync, no squirts.
    frames.first[34] = 0;
    TelemetryClient client;
    const auto snapshot = cycle(client, connect(client), frames);
    CHECK(!snapshot.get(Metric::MapKpa).present());
    CHECK(!snapshot.get(Metric::BoostPsi).present());
    CHECK(!snapshot.get(Metric::TpsPercent).present());
    CHECK(!snapshot.get(Metric::InjectorDutyPercent).present());
    CHECK(!snapshot.get(Metric::SpeedMph).present());
    CHECK(!snapshot.get(Metric::OilPsi).present());
    CHECK(snapshot.get(Metric::CoolantF).present());
    CHECK(snapshot.get(Metric::Rpm).present());
    CHECK(snapshot.get(Metric::PulseWidthMs).present());
    CHECK(snapshot.synchronized);
    CHECK(snapshot.protection_flags == 0x85);

    frames.first[6] = 40;
    frames.first[7] = 0;
    frames.second[2] = frames.second[3] = 0xff;
    frames.second[10] = 0xf0;
    TelemetryClient uncalibrated({true, true, false});
    auto partial = cycle(uncalibrated, connect(uncalibrated), frames);
    CHECK(partial.get(Metric::OilPsi).quality == Quality::Unverified);
    CHECK(partial.get(Metric::InjectorDutyPercent).value > 100);
    CHECK(partial.get(Metric::BoostPsi).value < 0);
    frames.first[16] = frames.first[17] = 0;
    frames.second[30] = frames.second[31] = 0;
    expect_read(uncalibrated.tick(25 + kCycle), kFirst);
    partial = cycle(uncalibrated, 25 + kCycle, frames);
    CHECK(partial.get(Metric::SpeedMph).present());
    near(partial.get(Metric::SpeedMph).value, 0);
    CHECK(partial.get(Metric::InjectorDutyPercent).present());
    near(partial.get(Metric::InjectorDutyPercent).value, 0);
}

void test_rx_failures_and_recovery()
{
    const Frames frames;
    for (int failure = 0; failure < 7; ++failure) {
        TelemetryClient client;
        const auto start = connect(client);
        client.tx_complete(true, start);
        uint64_t failed_ms = start + 4;
        if (failure == 0) {
            client.receive(frames.first.data() + 1, 2, failed_ms);
        } else if (failure == 1) {
            client.receive(frames.first.data(), frames.first.size() - 1, failed_ms);
            failed_ms = start + kDeadline;
            CHECK(client.tick(failed_ms).size == 0);
        } else if (failure == 2) {
            failed_ms = start + kDeadline;
            client.receive(frames.first.data(), frames.first.size(), failed_ms);
        } else if (failure == 3) {
            client.receive(frames.first.data(), frames.first.size(), failed_ms);
            client.receive(frames.first.data(), 1, ++failed_ms);
        } else {
            client.receive(frames.first.data(), frames.first.size(), failed_ms);
            const uint64_t second_start_ms = failed_ms + kQuiet;
            expect_read(client.tick(second_start_ms), kSecond);
            client.tx_complete(true, second_start_ms);
            failed_ms = second_start_ms + 3;
            client.receive(frames.second.data(), frames.second.size(), failed_ms);
            ++failed_ms;
            if (failure == 4) {
                client.receive(frames.second.data(), 1, failed_ms);
            } else if (failure == 5) {
                client.transport_error(failed_ms);
            } else {
                failed_ms += kTelemetryStaleMs;
                CHECK(client.tick(failed_ms).size == 0);
            }
        }
        CHECK(client.state() == LinkState::Stale);
        Snapshot snapshot;
        CHECK(!client.take_snapshot(snapshot));
        CHECK(client.tick(failed_ms + kBackoff - 2).size == 0);
        client.receive(frames.first.data(), 1, failed_ms + kBackoff - 1);
        CHECK(client.tick(failed_ms + kBackoff).size == 0);
        const auto retry = failed_ms + kBackoff - 1 + kQuiet;
        expect_identity(client.tick(retry));
        client.tx_complete(true, retry);
        feed_identity(client, kBaseIdentity, retry + 1);
        expect_read(client.tick(retry + 1 + kQuiet), kFirst);
        snapshot = cycle(client, retry + 1 + kQuiet, frames);
        CHECK(snapshot.rejected_frames == 1);
        CHECK(snapshot.target_echo_possible);
    }
}

void test_on_time_response_with_guard_past_deadline()
{
    TelemetryClient client;
    const Frames frames;
    const auto start_ms = connect(client);
    client.tx_complete(true, start_ms);
    const auto reply_ms = start_ms + kDeadline - 1;
    client.receive(frames.first.data(), frames.first.size(), reply_ms);
    CHECK(client.tick(reply_ms + 1).size == 0);
    const auto second_start_ms = reply_ms + kQuiet;
    expect_read(client.tick(second_start_ms), kSecond);
    client.tx_complete(true, second_start_ms);
    const auto second_reply_ms = second_start_ms + kDeadline - 1;
    client.receive(frames.second.data(), frames.second.size(), second_reply_ms);
    Snapshot snapshot;
    CHECK(client.tick(second_reply_ms + 1).size == 0);
    CHECK(!client.take_snapshot(snapshot));
    expect_read(client.tick(second_reply_ms + kQuiet), kFirst);
    CHECK(client.take_snapshot(snapshot));
    CHECK(snapshot.rejected_frames == 0);
    CHECK(snapshot.received_ms == second_reply_ms);
}

void test_uncertain_writes()
{
    const Frames frames;
    for (int command = 0; command < 4; ++command) {
        TelemetryClient client;
        uint64_t time = kQuiet;
        if (command == 0) {
            client.confirm_ecu_reset(0);
            expect_identity(client.tick(time));
        } else {
            time = connect(client);
            if (command == 2) {
                client.tx_complete(true, time);
                client.receive(frames.first.data(), frames.first.size(), time + 4);
                time += 4 + kQuiet;
                expect_read(client.tick(time), kSecond);
            }
        }
        if (command == 3) {
            CHECK(client.tick(time + kDeadline).size == 0);
        } else if (command == 2) {
            client.transport_error(time);
        } else {
            client.tx_complete(false, time);
        }
        CHECK(client.state() == LinkState::TransportFault);
        client.receive(frames.first.data(), frames.first.size(), time + 500);
        client.transport_error(time + 501);
        CHECK(client.tick(time + 10000).size == 0);
        CHECK(client.state() == LinkState::TransportFault);
        client.confirm_ecu_reset(time + 10001);
        expect_identity(client.tick(time + 10001 + kQuiet));
    }
}

void test_target_gate()
{
    TelemetryClient client;
    Frames frames;
    uint64_t time = connect(client);
    auto snapshot = cycle(client, time, frames);
    CHECK(snapshot.target_echo_possible);
    const auto next = [&]() {
        time += kCycle;
        expect_read(client.tick(time), kFirst);
        snapshot = cycle(client, time, frames);
    };

    for (uint32_t elapsed = kCycle; elapsed <= 16000; elapsed += kCycle) {
        const auto uptime = 254 + elapsed / 1000;
        frames.first[2] = static_cast<uint8_t>(uptime);
        next();
        CHECK(snapshot.target_echo_possible == (elapsed < 16000));
    }
    CHECK(snapshot.get(Metric::AfrTarget).quality == Quality::Valid);
    near(snapshot.get(Metric::AfrTarget).value, 14.2f);

    // Each loss of continuity requires another entire qualification window.
    for (int reset = 0; reset < 5; ++reset) {
        if (reset == 0) {
            ++frames.first[5]; // Changed sync-loss count despite a current sync bit.
        } else if (reset == 1) {
            frames.first[4] = 3; // Cranking overrides a concurrent running bit.
        } else if (reset == 2) {
            frames.first[4] = 0;
        } else if (reset == 3) {
            frames.first[34] = 0;
        } else {
            frames.first[2] = 0; // Uptime jumps backwards, distinct from 255 -> 0.
        }
        next();
        CHECK(snapshot.target_echo_possible);
        CHECK(!snapshot.get(Metric::AfrTarget).present());

        frames.first[4] = 1;
        frames.first[34] = 0x80;
        next();
        for (uint32_t elapsed = kCycle; elapsed <= 16000; elapsed += kCycle) {
            if (elapsed % 1000 == 0) {
                ++frames.first[2];
            }
            next();
        }
        CHECK(!snapshot.target_echo_possible);
    }
    client.expire(snapshot, snapshot.received_ms + kTelemetryStaleMs);
    CHECK(!snapshot.get(Metric::AfrTarget).present());
    CHECK(snapshot.target_echo_possible);
}

void test_replay()
{
    const auto sample = replay_sample(20000, 30000);
    CHECK(sample.link == LinkState::Replay);
    CHECK(sample.synchronized);
    CHECK(!sample.target_echo_possible);
    CHECK(sample.received_ms == 29950);
    near(sample.get(Metric::Rpm).value, 1249);
    near(sample.get(Metric::MapKpa).value, 96);
    near(sample.get(Metric::BoostPsi).value, -0.4351131f);
    near(sample.get(Metric::AfrRaw).value, 12.4f);
    near(sample.get(Metric::AfrTarget).value, 13.1f);
    near(sample.get(Metric::SpeedMph).value, 64);
    near(sample.get(Metric::FuelPercent).value, 61.9265f);
    near(sample.get(Metric::OilTempF).value, 211.486f, 0.01f);
    CHECK(sample.get(Metric::AfrRaw).quality == Quality::Unverified);
    CHECK(sample.get(Metric::AfrTarget).quality == Quality::Unverified);
    CHECK(sample.get(Metric::OilPsi).quality == Quality::Unverified);
    for (size_t i = 0; i < kMetricCount; ++i) {
        const auto metric = static_cast<Metric>(i);
        const bool simulated = metric == Metric::SpeedMph || metric == Metric::FuelPercent ||
                               metric == Metric::OilTempF;
        CHECK((sample.values[i].quality == Quality::Simulated) == simulated);
    }
    near(replay_sample(31705, 1).get(Metric::Rpm).value, 6890);
    near(replay_sample(19097, 1).get(Metric::Rpm).value, 884); // last row at duplicate time
    near(replay_sample(0, 1).get(Metric::Rpm).value, 889);
    const auto end = replay_sample(kReplayDurationMs + 1, 1);
    near(end.get(Metric::Rpm).value, 977);
    near(end.get(Metric::SpeedMph).value, 30);
}

void test_history()
{
    History history;
    Snapshot sample;
    sample.link = LinkState::Live;
    sample.set(Metric::Rpm, 1000, Quality::Valid, 200);
    sample.set(Metric::MapKpa, 30, Quality::Valid, 200);
    sample.set(Metric::TpsPercent, 5, Quality::Valid, 200);
    history.append(sample, 220);
    history.append(sample, 250);
    CHECK(history.size() == 1);
    CHECK(history.at(0).valid_mask == 7);
    CHECK(history.at(0).time_ms == 200);

    sample.get(Metric::MapKpa).quality = Quality::Missing;
    history.append(sample, 300);
    CHECK(history.size() == 2);
    CHECK(history.at(1).valid_mask == 5);
    history.append(sample, 1200);
    history.append(sample, 1400);
    CHECK(history.size() == 3);
    CHECK(history.at(2).valid_mask == 0);
    sample.set(Metric::Rpm, 2000, Quality::Valid, 1500);
    history.append(sample, 1510);
    CHECK(history.size() == 4);
    CHECK(history.at(3).valid_mask == 1);
    history.append(sample, 9501);
    CHECK(history.size() == 1);
    CHECK(history.at(0).valid_mask == 0);

    history.clear();
    for (uint64_t now = 0; now < kHistoryCapacity + 10; ++now) {
        sample.set(Metric::Rpm, static_cast<float>(now), Quality::Valid, now);
        history.append(sample, now);
    }
    CHECK(history.size() == kHistoryCapacity);
    CHECK(history.at(0).time_ms == 10);
    CHECK(history.at(kHistoryCapacity - 1).time_ms == kHistoryCapacity + 9);

    sample.set(Metric::Rpm, 1000, Quality::Valid, 2000);
    history.append(sample, 2000);
    CHECK(history.at(kHistoryCapacity - 2).valid_mask == 0);
    CHECK(history.at(kHistoryCapacity - 1).valid_mask == 1);
}

void test_controls()
{
    Controls controls;
    ViewState view;
    view.telemetry.link = LinkState::Replay;
    controls.update({true, true, true}, view, 10);
    controls.update({}, view, 20);
    CHECK(!controls.update({true, true, true}, view, 30).preferences_changed);
    CHECK(!controls.update({true, true, true}, view, 59).preferences_changed);
    CHECK(controls.update({true, true, true}, view, 60).preferences_changed);
    CHECK(view.mode == Mode::Track);
    CHECK(view.brightness_percent == 100);
    CHECK(view.replay_paused);
    CHECK(!controls.update({true, true, true}, view, 2500).confirm_ecu_reset);
    CHECK(view.mode == Mode::Track);
    CHECK(view.replay_paused);

    view.telemetry.link = LinkState::TransportFault;
    CHECK(!controls.update({true}, view, 5000).confirm_ecu_reset);
    controls.update({}, view, 5001);
    controls.update({}, view, 5031);
    controls.update({true}, view, 5040);
    controls.update({true}, view, 5070);
    CHECK(!controls.update({true}, view, 7069).confirm_ecu_reset);
    CHECK(controls.update({true}, view, 7070).confirm_ecu_reset);
    CHECK(!controls.update({true}, view, 10000).confirm_ecu_reset);
    controls.update({}, view, 10001);
    CHECK(!controls.update({}, view, 10031).preferences_changed);
    CHECK(view.mode == Mode::Track);

    Controls boot;
    ViewState waiting;
    CHECK(!boot.update({true}, waiting, 0).confirm_ecu_reset);
    CHECK(!boot.update({true}, waiting, 2030).confirm_ecu_reset);
    CHECK(!boot.update({true}, waiting, 5000).confirm_ecu_reset);
    boot.update({}, waiting, 5001);
    boot.update({}, waiting, 5031);
    boot.update({true}, waiting, 5040);
    boot.update({true}, waiting, 5070);
    CHECK(boot.update({true}, waiting, 7070).confirm_ecu_reset);
}

void test_calibration()
{
    constexpr CalibrationKnot knots[]{{100, 100}, {200, 80}, {300, 0}};
    CHECK(calibration_valid(knots, 3, 0, 100));
    const auto midpoint = calibrated_reading(knots, 3, 250, 0, 100, 3000);
    CHECK(midpoint.quality == Quality::Valid);
    CHECK(midpoint.observed_ms == 3000);
    near(midpoint.value, 40);
    near(calibrated_reading(knots, 3, 100, 0, 100, 0).value, 100);
    near(calibrated_reading(knots, 3, 300, 0, 100, 0).value, 0);
    CHECK(!calibrated_reading(knots, 3, 99, 0, 100, 0).present());
    CHECK(!calibrated_reading(knots, 3, 301, 0, 100, 0).present());
    CHECK(!calibrated_reading(nullptr, 0, 250, 0, 100, 0).present());
    const CalibrationKnot invalid[][2] = {
        {{200, 0}, {100, 100}}, {{100, 0}, {100, 100}},
        {{-1, 0}, {100, 100}}, {{100, 0}, {32768, 100}},
        {{100, 0}, {200, 101}}, {{100, 0}, {200, std::numeric_limits<float>::quiet_NaN()}},
        {{100, 0}, {200, std::numeric_limits<float>::infinity()}},
    };
    for (const auto& profile : invalid) {
        CHECK(!calibration_valid(profile, 2, 0, 100));
    }
    CHECK(!calibration_valid(knots, 1, 0, 100));
    CHECK(!calibration_valid(knots, 3, 100, 0));
}

void test_oil_overrange()
{
    ClientConfig config;
    config.oil_enabled = config.oil_calibrated = true;
    for (const uint8_t pressure : {100, 101, 113, 255}) {
        TelemetryClient client(config);
        Frames frames;
        frames.second[34] = pressure;
        const auto snapshot = cycle(client, connect(client), frames);
        CHECK(snapshot.get(Metric::OilPsi).quality == Quality::Valid);
        near(snapshot.get(Metric::OilPsi).value, pressure);
    }
}

void test_independent_observation_logging()
{
    Snapshot before;
    Snapshot after = before;
    CHECK(!has_new_observation(before, after));
    after.set(Metric::FuelPercent, 62, Quality::Valid, 100);
    CHECK(has_new_observation(before, after)); // ECU remains disarmed.
    before = after;
    after.get(Metric::FuelPercent).observed_ms = 300;
    CHECK(has_new_observation(before, after)); // Same level, new ADC sample.
    before = after;
    after.get(Metric::FuelPercent).quality = Quality::Missing;
    CHECK(has_new_observation(before, after)); // Sensor stale without ECU change.
    before = after;
    CHECK(!has_new_observation(before, after));
    after.link = LinkState::Stale;
    CHECK(has_new_observation(before, after));
}

void test_exact_replay_history_and_endpoint()
{
    History history;
    replay_history(31705, 100000, history);
    CHECK(history.size() == 85);
    bool duplicate_transient = false;
    bool rev_sample = false;
    for (size_t i = 0; i < history.size(); ++i) {
        const auto& p = history.at(i);
        rev_sample |= p.rpm == 6355;
        if (i != 0 && p.time_ms == history.at(i - 1).time_ms) {
            const auto& previous = history.at(i - 1);
            duplicate_transient |= previous.map_kpa == 139 && p.map_kpa == 60 &&
                                   previous.rpm == 6823 && p.rpm == 6720;
        }
    }
    CHECK(duplicate_transient);
    CHECK(rev_sample);

    ReplayTimeline clock;
    clock.reset(1000, kReplayDurationMs - 10);
    auto step = clock.advance(1015, false);
    CHECK(step.reached_end && !step.wrapped);
    CHECK(clock.offset_ms() == kReplayDurationMs);
    near(replay_sample(clock.offset_ms(), clock.now_ms()).get(Metric::Rpm).value, 977);
    const auto end_time = clock.now_ms();
    CHECK(!clock.advance(2000, false).changed); // No rendered endpoint yet.
    CHECK(clock.now_ms() == end_time);
    clock.presented();
    CHECK(!clock.advance(3000, true).changed); // Pause still holds endpoint.
    step = clock.advance(3010, false);
    CHECK(step.wrapped && clock.offset_ms() == 0);
    CHECK(clock.now_ms() == end_time + 10);
    near(replay_sample(0, clock.now_ms()).get(Metric::Rpm).value, 889);
    replay_history(0, clock.now_ms(), history);
    CHECK(history.size() == 1);
    CHECK(!clock.advance(3020, true).changed);
    const auto pause_time = clock.now_ms();
    clock.advance(3030, false);
    CHECK(clock.now_ms() == pause_time + 10);
}

} // namespace

int main()
{
    test_disarmed_and_identity();
    test_decode_and_freshness();
    test_independent_quality();
    test_rx_failures_and_recovery();
    test_on_time_response_with_guard_past_deadline();
    test_uncertain_writes();
    test_target_gate();
    test_replay();
    test_history();
    test_controls();
    test_calibration();
    test_oil_overrange();
    test_independent_observation_logging();
    test_exact_replay_history_and_endpoint();
    std::cout << "Core tests passed\n";
}
