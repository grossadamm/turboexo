# Firmware integration contracts

This file fixes the boundaries between parallel implementations. The shared
model is `firmware/cluster/include/cluster/types.hpp` (main-agent owned).
All timestamps are monotonic milliseconds in the current firmware process.
UI works at fixed logical 1280×800. Only platform adapters depend on ESP-IDF.

## Core owner

Own `firmware/cluster/core/`, headers in `include/cluster/` other than
`types.hpp` and `dashboard.hpp`, `tests/core_tests.cpp`, core test CMake,
`tools/generate_replay.py`, `generated/replay_data.hpp` and calibration examples.
Expose these APIs (report proposed signature changes before applying them):

```cpp
struct ClientConfig {
    bool vss_enabled = false;
    bool oil_enabled = false;
    bool oil_calibrated = false;
    uint32_t ego_delay_ms = 15000;
    uint32_t cycle_ms = 200;
    uint32_t stale_ms = 1000;
};
struct TxRequest { std::array<uint8_t,7> bytes{}; size_t size=0; };
class TelemetryClient {
public:
    explicit TelemetryClient(ClientConfig config = {});
    void confirm_ecu_reset(uint64_t now_ms);
    TxRequest tick(uint64_t now_ms); // returns a request once; zero means none
    void tx_complete(bool fully_written, uint64_t now_ms);
    void receive(const uint8_t* bytes, size_t count, uint64_t now_ms);
    void transport_error(uint64_t now_ms); // no in-flight uncertain TX -> recover
    void expire(Snapshot& snapshot, uint64_t now_ms) const;
    bool take_snapshot(Snapshot& out);
    LinkState state() const;
};
Snapshot replay_sample(uint32_t offset_ms, uint64_t now_ms);
constexpr uint32_t kReplayDurationMs = 54425;
```

`protocol.hpp` owns client declarations, `replay.hpp` the replay API,
`calibration.hpp` calibrated ADC conversion, `controls.hpp` buttons.
`History` methods are implemented by core. No heap growth in the poller/history.
State starts `AwaitEcuReset`; no output until confirmation, and every new
firmware instance starts disarmed. Partial/indeterminate writes latch
`TransportFault`; only explicit reset confirmation clears it. Bad RX after
confirmed whole TX may recover after quiet/backoff. Publish a completed two-span
cycle only after both response guards. UI receives `state()` even with no new
snapshot. Readings already carry validity; `expire` clears stale metrics.

Replay is the sole source of simulated values, using the accepted JSON and
speed/fuel/oil-temperature functions. It must not enter a live path. The caller
owns playback time, pause, looping and clears history on backward seek/loop.
Control and calibration APIs may be designed by core, then reported to platform.

## UI owner

Own `firmware/cluster/ui/`, `include/cluster/dashboard.hpp`,
`assets/`, `host/`, `tools/generate_assets.*`, and host CMake/LVGL config.
Expose:

```cpp
class Dashboard {
public:
    void create(lv_obj_t* parent); // LVGL initialized and display created by caller
    void update(const ViewState&, const History&, uint64_t now_ms);
};
```

Keep native drawing and typefaces shared with hardware. Host offscreen fixtures
must render the same Dashboard (not the HTML mock), export 1280×800 PNG or PPM,
and run without display-server availability. Interactive host keys should cover
modes and replay pause. Host-only SDL/filesystem code cannot enter target UI.
Use LVGL 9.5.0, bundle licensed generated font/icon assets. Record asset source
and deterministic generation command. Host dependency source goes in persistent
`/Users/adamgross/TunerStudioProjects/TurboExo-deps/`, not /tmp.

## Platform owner

Own `firmware/cluster/main/`, root ESP-IDF `CMakeLists.txt`, component manifest,
partition/config files and platform drivers. Link core + UI through their
headers, keep CMake source lists explicit, and resolve component lockfile.
Live task drives TelemetryClient; replay task drives `replay_sample`. Only one
source is built/selected, default replay. Snapshot/history ownership and GUI
locking must be explicit. App task is the only writer of ViewState; platform
sensor/logger results arrive by typed messages or protected structures.

Hardware inputs: proposed TX17/RX18; buttons19/20/21; ADS SDA15/SCL16,
A0 fuel/A1 oil temperature; panel/vendor pin mappings and SD pins in research.
Validate duplicates/reserved GPIO before peripheral initialization. Long hold
Mode while awaiting/reset fault is explicit ECU-reset acknowledgement, not
ordinary mode cycling. UART writes must be full and drained before reporting
success; exceptions/errors imply uncertain transmission. Console only USB.

## Main agent

Own shared types, documentation, root validation script, integration fixes,
review fixtures/baseline and final commits/rebase/push. Do not reformat or edit
another owner's active files without coordinating. No agent commits/pushes,
changes tune/mocks, flashes hardware, deploys, or deletes failed build trees.
Use fresh persistent build directories and return concise evidence/blockers.
