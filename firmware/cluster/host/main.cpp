#include "cluster/dashboard.hpp"
#include "cluster/replay.hpp"
#include <array>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <lvgl.h>
#include <string>
#ifdef CLUSTER_HAVE_SDL
#include <SDL.h>
#endif
using namespace cluster;
static std::array<uint32_t, 1280 * 800> frame{};
static std::array<uint32_t, 1280 * 800> drawbuf{};
static void flush(lv_display_t *d, const lv_area_t *a, uint8_t *p) {
  auto *src = reinterpret_cast<uint32_t *>(p);
  for (int y = a->y1; y <= a->y2; y++)
    for (int x = a->x1; x <= a->x2; x++)
      frame[y * 1280 + x] = *src++;
  lv_display_flush_ready(d);
}
static void save(const char *path) {
  FILE *f = std::fopen(path, "wb");
  if (!f) {
    std::perror(path);
    std::exit(1);
  }
  std::fprintf(f, "P6\n1280 800\n255\n");
  for (uint32_t p : frame) {
    unsigned char rgb[] = {static_cast<unsigned char>(p >> 16),
                           static_cast<unsigned char>(p >> 8),
                           static_cast<unsigned char>(p)};
    std::fwrite(rgb, 1, 3, f);
  }
  std::fclose(f);
}
static void fixture(ViewState &v, History &h, uint32_t offset,
                    const char *scenario, uint64_t now) {
  h.clear();
  v.logging_active = false;
  v.logging_fault = false;
  v.log_dropped = 0;
  replay_history(offset, now, h);
  v.telemetry = replay_sample(offset, now);
  if (std::strcmp(scenario, "offline") == 0) {
    v.telemetry = Snapshot{};
    v.telemetry.link = LinkState::Stale;
    h.clear();
  } else if (std::strcmp(scenario, "warmup") == 0) {
    v.telemetry.link = LinkState::Live;
    v.telemetry.target_echo_possible = true;
    v.telemetry.engine_flags = 1;
    v.telemetry.synchronized = true;
    for (auto &r : v.telemetry.values)
      if (r.quality == Quality::Simulated)
        r.quality = Quality::Missing;
    v.telemetry.get(Metric::AfrRaw).quality = Quality::Unverified;
  } else if (std::strcmp(scenario, "protection") == 0) {
    v.telemetry.link = LinkState::Live;
    v.telemetry.protection_flags = 4;
    for (auto &r : v.telemetry.values)
      if (r.quality == Quality::Simulated)
        r.quality = Quality::Missing;
  } else if (std::strcmp(scenario, "peripheral") == 0) {
    v.telemetry.link = LinkState::Live;
    v.peripheral_faults =
        ButtonsFault | AdcFault | PreferencesFault | UartFault;
  } else if (std::strcmp(scenario, "logging") == 0) {
    v.logging_active = true;
  } else if (std::strcmp(scenario, "log_error") == 0) {
    v.logging_fault = true;
  } else if (std::strcmp(scenario, "log_drops") == 0) {
    v.logging_active = true;
    v.log_dropped = 3;
  } else if (std::strcmp(scenario, "extremes") == 0) {
    v.telemetry.set(Metric::Rpm, 10000, Quality::Valid, now);
    v.telemetry.set(Metric::SpeedMph, 199, Quality::Valid, now);
    v.telemetry.set(Metric::OilPsi, 150, Quality::Valid, now);
    v.telemetry.set(Metric::CoolantF, 350, Quality::Valid, now);
    v.telemetry.set(Metric::OilTempF, 350, Quality::Valid, now);
    v.telemetry.set(Metric::BoostPsi, -25, Quality::Valid, now);
  }
  if (v.telemetry.link != LinkState::Replay) {
    for (auto &reading : v.telemetry.values) {
      if (reading.quality == Quality::Simulated)
        reading.quality = Quality::Missing;
    }
  }
}
int main(int argc, char **argv) {
  lv_init();
  auto *d = lv_display_create(1280, 800);
  lv_display_set_color_format(d, LV_COLOR_FORMAT_XRGB8888);
  lv_display_set_buffers(d, drawbuf.data(), nullptr, sizeof(drawbuf),
                         LV_DISPLAY_RENDER_MODE_FULL);
  lv_display_set_flush_cb(d, flush);
  Dashboard dashboard;
  dashboard.create(lv_screen_active());
  ViewState v;
  History h;
  uint64_t now = 100000;
  uint32_t offset = 20000;
  if (argc == 3 && std::strcmp(argv[1], "--capture-dir") == 0) {
    std::filesystem::create_directories(argv[2]);
    const char *modes[] = {"street", "track", "tuning"};
    const uint32_t offsets[] = {20000, 31705, kReplayDurationMs};
    for (int m = 0; m < 3; m++) {
      v.mode = static_cast<Mode>(m);
      for (auto off : offsets) {
        v.peripheral_faults = 0;
        fixture(v, h, off, "replay", now);
        // Reset animation between independent still fixtures.
        ViewState reset;
        dashboard.update(reset, h, now);
        dashboard.update(v, h, now);
        lv_refr_now(d);
        auto path = std::string(argv[2]) + "/" + modes[m] + "_" +
                    std::to_string(off) + ".ppm";
        save(path.c_str());
      }
      const char *scenarios[] = {"offline",   "warmup",     "protection",
                                 "extremes",  "peripheral", "logging",
                                 "log_error", "log_drops"};
      for (auto scenario : scenarios) {
        v.peripheral_faults = 0;
        fixture(v, h, 20000, scenario, now);
        // Reset animation between independent still fixtures.
        ViewState reset;
        dashboard.update(reset, h, now);
        dashboard.update(v, h, now);
        lv_refr_now(d);
        auto path =
            std::string(argv[2]) + "/" + modes[m] + "_" + scenario + ".ppm";
        save(path.c_str());
      }
    }
    return 0;
  }
  if (argc != 2 || std::strcmp(argv[1], "--interactive") != 0) {
    std::fprintf(stderr,
                 "Usage: cluster_sim --capture-dir DIR | --interactive\n");
    return 2;
  }

#ifdef CLUSTER_HAVE_SDL
  if (SDL_Init(SDL_INIT_VIDEO) != 0) {
    std::fprintf(stderr, "SDL: %s\n", SDL_GetError());
    return 1;
  }
  auto *w = SDL_CreateWindow("TurboExo cluster - 1/2/3 modes, space pause",
                             SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                             1280, 800, 0);
  if (!w) {
    std::fprintf(stderr, "SDL window: %s\n", SDL_GetError());
    SDL_Quit();
    return 1;
  }
  auto *r = SDL_CreateRenderer(w, -1, SDL_RENDERER_ACCELERATED);
  if (!r)
    r = SDL_CreateRenderer(w, -1, SDL_RENDERER_SOFTWARE);
  if (!r) {
    std::fprintf(stderr, "SDL renderer: %s\n", SDL_GetError());
    SDL_DestroyWindow(w);
    SDL_Quit();
    return 1;
  }
  auto *t = SDL_CreateTexture(r, SDL_PIXELFORMAT_ARGB8888,
                              SDL_TEXTUREACCESS_STREAMING, 1280, 800);
  if (!t) {
    std::fprintf(stderr, "SDL texture: %s\n", SDL_GetError());
    SDL_DestroyRenderer(r);
    SDL_DestroyWindow(w);
    SDL_Quit();
    return 1;
  }
  bool running = true, paused = false;
  auto last = std::chrono::steady_clock::now();
  ReplayTimeline timeline;
  timeline.reset(now, offset);
  while (running) {
    SDL_Event e;
    while (SDL_PollEvent(&e)) {
      if (e.type == SDL_QUIT)
        running = false;
      if (e.type == SDL_KEYDOWN && e.key.repeat == 0) {
        switch (e.key.keysym.sym) {
        case SDLK_ESCAPE:
          running = false;
          break;
        case SDLK_1:
          v.mode = Mode::Street;
          break;
        case SDLK_2:
          v.mode = Mode::Track;
          break;
        case SDLK_3:
          v.mode = Mode::Tuning;
          break;
        case SDLK_SPACE:
          paused = !paused;
          break;
        }
      }
    }
    auto cur = std::chrono::steady_clock::now();
    auto dt = std::chrono::duration_cast<std::chrono::milliseconds>(cur - last)
                  .count();
    last = cur;
    now += dt;
    timeline.advance(now, paused);
    offset = timeline.offset_ms();
    fixture(v, h, offset, "replay", timeline.now_ms());
    v.replay_paused = paused;
    dashboard.update(v, h, timeline.now_ms());
    lv_refr_now(d);
    timeline.presented();
    SDL_UpdateTexture(t, nullptr, frame.data(), 1280 * 4);
    SDL_RenderCopy(r, t, nullptr, nullptr);
    SDL_RenderPresent(r);
    SDL_Delay(30);
  }
  SDL_DestroyTexture(t);
  SDL_DestroyRenderer(r);
  SDL_DestroyWindow(w);
  SDL_Quit();
#else
  std::fprintf(stderr, "SDL unavailable; use --capture-dir DIR for capture\n");
  return 1;
#endif
}
