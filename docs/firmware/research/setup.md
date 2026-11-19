# ESP32-P4 build environment research

Investigated 2026-11-19 on the Apple Silicon development Mac. No firmware was flashed or hardware accessed.

## Version constraint

The board manufacturer's `4dsystems/esp32p4_lcd` 0.1.1 component declares ESP-IDF >= 5.5.2; use the proposed 5.5.5 pin for board integration, subject to verification against the complete board support package and silicon revision. The existing v5.4.3 checkout is useful as an environment probe but does not meet that component constraint. The board's silicon revision is not yet known; pre-v3 and v3 configurations require separate consideration.

## Installed tools

- macOS arm64; Apple clang 21.0.0, CMake 4.0.3, Ninja 1.13.0, Python 3.11.13, SDL2 2.30.9 (`pkg-config`).
- `/Users/adamgross/dev/esp32_s3/hardware/esp-idf` is an existing ESP-IDF v5.4.3 checkout. `~/.espressif` includes IDF Python environments and RISC-V cross-toolchain versions, but the recorded installs list S3 targets. Do not modify that checkout for this project.
- An isolated copy of the v5.4.3 `hello_world` example built successfully for `esp32p4` with `idf.py set-target esp32p4 build`, using the existing installation. This verifies the Mac can cross-compile a generic P4 image, not compatibility with the board or its peripherals.
- Apple clang compiled and ran a C++17 host executable. SDL2's `dummy` video driver created a window surface and saved a BMP headlessly. This is a feasibility probe, not an LVGL simulation: LVGL and its display integration still need to be pinned, built, and tested. A software framebuffer and image export can support screenshot tests; SDL window availability is not needed for the dummy-driver probe.

## Isolated ESP-IDF 5.5.5 setup

Espressif's [P4 setup guide](https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32p4/get-started/linux-macos-setup.html) documents the target-specific install. A separate checkout and `IDF_TOOLS_PATH` avoid changing the existing ESP-IDF and global defaults. The following commands require network access and free disk space for submodules, toolchains, and Python packages. A 66 GiB free-space reading was observed before installation; download time depends on network speed. The checkout and tool cache are kept in the persistent project-specific directory shown below.

```sh
git clone --branch v5.5.5 --depth 1 --recursive --shallow-submodules \
  https://github.com/espressif/esp-idf.git /Users/adamgross/TunerStudioProjects/TurboExo-deps/esp-idf-v5.5.5
export IDF_TOOLS_PATH=/Users/adamgross/TunerStudioProjects/TurboExo-deps/esp-idf-tools
cd /Users/adamgross/TunerStudioProjects/TurboExo-deps/esp-idf-v5.5.5
./install.sh esp32p4
source ./export.sh
idf.py --version
```

In a new shell repeat the `IDF_TOOLS_PATH` export and `source .../export.sh`. For a disposable generic compile check, copy `examples/get-started/hello_world` outside the IDF checkout, enter the copy, and run `idf.py set-target esp32p4 build`. This only produces build artifacts. For project builds, use the repository's eventual pinned configuration and build instructions; selecting the target can overwrite an existing `sdkconfig`.

## Host validation approach

Keep portable parsing and application logic independent of ESP-IDF hardware APIs and compile it with Apple clang/CMake and CTest. For screen rendering, pin the same LVGL version as the firmware, create a host display backed by a software framebuffer, and export deterministic frames for inspection. SDL2 is installed and can support interactive simulation; headless screenshot support must be implemented and validated with the chosen LVGL configuration. Host tests and screenshots cannot establish physical display timing, touch behavior, real ECU data, or board-level operation.
