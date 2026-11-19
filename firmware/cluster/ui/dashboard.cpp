#include "cluster/dashboard.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>

LV_FONT_DECLARE(cluster_num_64);
LV_FONT_DECLARE(cluster_num_96);
LV_FONT_DECLARE(cluster_num_144);
LV_FONT_DECLARE(cluster_num_220);
LV_FONT_DECLARE(cluster_text_26);
LV_FONT_DECLARE(cluster_text_34);
extern "C" {
LV_IMAGE_DECLARE(cluster_icon_oil_can);
LV_IMAGE_DECLARE(cluster_icon_thermometer);
LV_IMAGE_DECLARE(cluster_icon_fuel);
LV_IMAGE_DECLARE(cluster_icon_gauge);
}
namespace cluster {
namespace {
constexpr uint32_t ink = 0xf2f5f2, muted = 0xa9b5af, mint = 0xb1ebd4,
                   amber = 0xffc16b, cyan = 0x80d5ec, base = 0x293c31;
float clamp(float v, float a, float b) { return std::max(a, std::min(b, v)); }
void line(lv_layer_t *l, float x1, float y1, float x2, float y2, uint32_t c,
          int w = 2) {
  lv_draw_line_dsc_t d;
  lv_draw_line_dsc_init(&d);
  d.color = lv_color_hex(c);
  d.width = w;
  d.p1 = {(lv_value_precise_t)x1, (lv_value_precise_t)y1};
  d.p2 = {(lv_value_precise_t)x2, (lv_value_precise_t)y2};
  lv_draw_line(l, &d);
}
void rect(lv_layer_t *l, int x, int y, int w, int h, uint32_t c) {
  if (w <= 0 || h <= 0)
    return;
  lv_draw_rect_dsc_t d;
  lv_draw_rect_dsc_init(&d);
  d.bg_color = lv_color_hex(c);
  d.bg_opa = LV_OPA_COVER;
  lv_area_t a = {x, y, x + w - 1, y + h - 1};
  lv_draw_rect(l, &d, &a);
}
void text(lv_layer_t *l, int x, int y, int w, const char *s, const lv_font_t *f,
          uint32_t c = ink, lv_text_align_t align = LV_TEXT_ALIGN_LEFT) {
  lv_draw_label_dsc_t d;
  lv_draw_label_dsc_init(&d);
  d.text = s;
  d.text_local = 1;
  d.font = f;
  d.color = lv_color_hex(c);
  d.align = align;
  lv_area_t a = {x, y, x + w - 1, y + (int)f->line_height + 5};
  lv_draw_label(l, &d, &a);
}
const Reading &get(const Snapshot &s, Metric m) { return s.get(m); }
bool valid(const Reading &r, uint64_t now) {
  return r.present() && std::isfinite(r.value) && now >= r.observed_ms &&
         now - r.observed_ms <= kTelemetryStaleMs;
}
void val(char *out, size_t n, const Reading &r, uint64_t now, int decimals = 0,
         bool sign = false) {
  if (!valid(r, now)) {
    std::snprintf(out, n, "--");
    return;
  }
  if (decimals == 2)
    std::snprintf(out, n, sign ? "%+.2f" : "%.2f", r.value);
  else if (decimals == 1)
    std::snprintf(out, n, sign ? "%+.1f" : "%.1f", r.value);
  else
    std::snprintf(out, n, sign ? "%+.0f" : "%.0f", r.value);
}
void header(lv_layer_t *l, const ViewState &v) {
  const auto &s = v.telemetry;
  const char *status = "";
  uint32_t c = amber;
  switch (s.link) {
  case LinkState::Replay:
    status = v.replay_paused ? "REPLAY PAUSED / SIM AUX" : "REPLAY / SIM AUX";
    c = muted;
    break;
  case LinkState::AwaitEcuReset:
    status = "RESET ECU, THEN HOLD MODE";
    break;
  case LinkState::Connecting:
    status = "CONNECTING";
    break;
  case LinkState::Live:
    status = "LIVE";
    c = muted;
    break;
  case LinkState::Stale:
    status = "ECU OFFLINE / STALE";
    break;
  case LinkState::Unsupported:
    status = "ECU UNSUPPORTED";
    break;
  case LinkState::TransportFault:
    status = "TX FAULT / RESET ECU, HOLD MODE";
    break;
  }
  if (s.protection_flags) {
    char b[80];
    std::snprintf(b, sizeof b, "ECU PROTECTION:%s%s%s%s%s%s",
                  s.protection_flags & 1 ? " RPM" : "",
                  s.protection_flags & 2 ? " MAP" : "",
                  s.protection_flags & 4 ? " OIL" : "",
                  s.protection_flags & 8 ? " AFR" : "",
                  s.protection_flags & 16 ? " COOLANT" : "",
                  s.protection_flags & 0xe0 ? " INPUT/OTHER" : "");
    text(l, 220, 8, 840, b, &cluster_text_26, 0xff7068, LV_TEXT_ALIGN_CENTER);
  } else
    text(l, 320, 8, 640, status, &cluster_text_26, c, LV_TEXT_ALIGN_CENTER);
  const char *log_status = v.logging_fault    ? "LOG ERROR"
                           : v.log_dropped    ? "LOG DROPS"
                           : v.logging_active ? "LOG"
                                              : "";
  if (*log_status)
    text(l, 45, 38, 175, log_status, &cluster_text_26,
         v.logging_fault || v.log_dropped ? amber : mint);
  if (v.peripheral_faults) {
    char f[80];
    std::snprintf(f, sizeof f, "CHECK:%s%s%s%s",
                  v.peripheral_faults & ButtonsFault ? " BUTTONS" : "",
                  v.peripheral_faults & AdcFault ? " SENSORS" : "",
                  v.peripheral_faults & PreferencesFault ? " PREFS" : "",
                  v.peripheral_faults & UartFault ? " UART" : "");
    text(l, 230, 38, 820, f, &cluster_text_26, amber, LV_TEXT_ALIGN_CENTER);
  } else if (s.get(Metric::OilPsi).quality == Quality::Unverified) {
    text(l, 320, 38, 640, "OIL PRESSURE UNVERIFIED", &cluster_text_26, muted,
         LV_TEXT_ALIGN_CENTER);
  }
}

void icon(lv_layer_t *l, int x, int y, int kind) {
  const lv_image_dsc_t *assets[] = {&cluster_icon_oil_can,
                                    &cluster_icon_thermometer,
                                    &cluster_icon_fuel, &cluster_icon_gauge};
  lv_draw_image_dsc_t d;
  lv_draw_image_dsc_init(&d);
  d.src = assets[kind];
  lv_area_t a = {x, y, x + 31, y + 31};
  lv_draw_image(l, &d, &a);
}
struct Gauge {
  Metric m;
  const char *name;
  const char *unit;
  float lo, hi;
  const char *a;
  const char *b;
  const char *c;
  bool signed_value;
};
void gauges(lv_layer_t *l, const Snapshot &s, uint64_t now, const Gauge *g,
            const int *xs, uint32_t color) {
  for (int i = 0; i < 4; i++) {
    int x = xs[i];
    const auto &r = get(s, g[i].m);
    char b[48];
    val(b, sizeof b, r, now, g[i].signed_value ? 1 : 0, g[i].signed_value);
    // Align the label, reading, and scale to the accepted baselines.  The
    // unit shares the reading baseline and the complete group stays centered.
    constexpr int label_baseline = 610, value_baseline = 675;
    constexpr int bar_y = 700, bar_height = 18, scale_baseline = 756;
    const int label_y = label_baseline - (cluster_text_26.line_height -
                                          cluster_text_26.base_line);
    const int value_y = value_baseline -
                        (cluster_num_64.line_height - cluster_num_64.base_line);
    const int unit_y = value_baseline - (cluster_text_26.line_height -
                                         cluster_text_26.base_line);
    const int scale_y = scale_baseline - (cluster_text_26.line_height -
                                          cluster_text_26.base_line);
    icon(l, x - 140, label_y - 4,
         i == 0
             ? 0
             : (g[i].m == Metric::FuelPercent ? 2
                                              : (g[i].signed_value ? 3 : 1)));
    text(l, x - 108, label_y, 253, g[i].name, &cluster_text_26, muted,
         LV_TEXT_ALIGN_CENTER);
    lv_point_t value_size{}, unit_size{};
    lv_text_get_size(&value_size, b, &cluster_num_64, 0, 0, 1000,
                     LV_TEXT_FLAG_NONE);
    lv_text_get_size(&unit_size, g[i].unit, &cluster_text_26, 0, 0, 1000,
                     LV_TEXT_FLAG_NONE);
    constexpr int unit_gap = 10;
    int group_left = x - (value_size.x + unit_gap + unit_size.x) / 2;
    text(l, group_left, value_y, value_size.x + 4, b, &cluster_num_64);
    text(l, group_left + value_size.x + unit_gap, unit_y, unit_size.x + 4,
         g[i].unit, &cluster_text_26, muted);
    int left = x - 117;
    rect(l, left, bar_y, 234, bar_height, base);
    if (valid(r, now)) {
      float f = clamp((r.value - g[i].lo) / (g[i].hi - g[i].lo), 0, 1),
            z = g[i].signed_value ? 0.5f : 0;
      int start = left + (int)(234 * std::min(f, z)),
          width = (int)(234 * std::abs(f - z));
      rect(l, start, bar_y, width, bar_height, color);
    }
    for (int j = 0; j <= 4; j++) {
      int p = left + 234 * j / 4;
      line(l, p, bar_y + bar_height + 4, p,
           bar_y + bar_height + 4 + (j % 2 ? 4 : 8), muted, 2);
    }
    if (g[i].signed_value)
      line(l, x, bar_y - 3, x, bar_y + bar_height + 3, ink, 2);
    text(l, left - 40, scale_y, 80, g[i].a, &cluster_text_26, muted,
         LV_TEXT_ALIGN_CENTER);
    text(l, x - 30, scale_y, 60, g[i].b, &cluster_text_26, muted,
         LV_TEXT_ALIGN_CENTER);
    text(l, left + 194, scale_y, 80, g[i].c, &cluster_text_26, muted,
         LV_TEXT_ALIGN_CENTER);
  }
}
void street(lv_layer_t *l, const ViewState &v, uint64_t now, float visual_rpm) {
  auto &s = v.telemetry;
  text(l, 45, 8, 200, "STREET", &cluster_text_26, muted);
  text(l, 1040, 8, 195, "RPM x 1000", &cluster_text_26, muted,
       LV_TEXT_ALIGN_RIGHT);
  header(l, v);
  float rpm = clamp(visual_rpm / 8000, 0, 1);
  for (int i = 0; i < 96; i++) {
    float a = 3.14159265f + i * 3.14159265f / 96,
          b = 3.14159265f + (i + 1) * 3.14159265f / 96;
    line(l, 640 + 540 * cos(a), 390 + 300 * sin(a), 640 + 540 * cos(b),
         390 + 300 * sin(b), i < rpm * 96 ? mint : base, 12);
  }
  for (int i = 0; i <= 16; i++) {
    float a = 3.14159265f + i * 3.14159265f / 16;
    float cs = cos(a), sn = sin(a);
    line(l, 640 + 520 * cs, 390 + 280 * sn, 640 + (i % 2 ? 510 : 502) * cs,
         390 + (i % 2 ? 270 : 262) * sn, muted, i % 2 ? 2 : 3);
    if (i % 2 == 0) {
      char b[8];
      std::snprintf(b, sizeof b, "%d", i / 2);
      text(l, 640 + 472 * cs - 25, 390 + 232 * sn - 18, 50, b, &cluster_text_34,
           muted, LV_TEXT_ALIGN_CENTER);
    }
  }
  char b[48];
  val(b, sizeof b, get(s, Metric::SpeedMph), now);
  text(l, 330, 220, 620, b, &cluster_num_220, ink, LV_TEXT_ALIGN_CENTER);
  text(l, 540, 404, 200, "MPH", &cluster_text_34, muted, LV_TEXT_ALIGN_CENTER);
  val(b, sizeof b, get(s, Metric::Rpm), now);
  lv_point_t size{};
  lv_text_get_size(&size, b, &cluster_num_64, 0, 0, 400, LV_TEXT_FLAG_NONE);
  lv_point_t unit_size{};
  lv_text_get_size(&unit_size, "RPM", &cluster_text_26, 0, 0, 200,
                   LV_TEXT_FLAG_NONE);
  int left = 640 - (size.x + 12 + unit_size.x) / 2;
  text(l, left, 449, size.x + 4, b, &cluster_num_64);
  text(l, left + size.x + 12, 480, unit_size.x + 4, "RPM", &cluster_text_26,
       muted);
  const Gauge g[] = {
      {Metric::OilPsi, "OIL PRESSURE", "psi", 0, 100, "0", "50", "100", false},
      {Metric::CoolantF, "COOLANT", "°F", 120, 280, "120", "200", "280", false},
      {Metric::FuelPercent, "FUEL", "%", 0, 100, "E", "1/2", "F", false},
      {Metric::BoostPsi, "BOOST / VAC", "psi", -15, 15, "-15", "0", "+15",
       true}};
  const int xs[] = {175, 485, 795, 1105};
  gauges(l, s, now, g, xs, mint);
}
void track(lv_layer_t *l, const ViewState &v, uint64_t now, float visual_rpm) {
  auto &s = v.telemetry;
  text(l, 55, 8, 200, "TRACK", &cluster_text_26, muted);
  text(l, 1040, 8, 185, "RPM x 1000", &cluster_text_26, muted,
       LV_TEXT_ALIGN_RIGHT);
  header(l, v);
  float rpm = clamp(visual_rpm / 8000, 0, 1);
  for (int i = 0; i < 116; i++) {
    float x = 60 + i * 10,
          y = 167 - .10f * (x - 60) + .000035f * (x - 60) * (x - 60),
          h = 18 + (x - 60) / 1160 * 50;
    rect(l, (int)x, (int)y, 11, (int)h, i < rpm * 116 ? amber : 0x383126);
  }
  for (int i = 0; i <= 8; i++) {
    int x = 60 + i * 145;
    float y = 167 - .10f * (x - 60) + .000035f * (x - 60) * (x - 60);
    char b[8];
    std::snprintf(b, sizeof b, "%d", i);
    text(l, x - 15, (int)y - 43, 30, b, &cluster_text_26, muted,
         LV_TEXT_ALIGN_CENTER);
  }
  char b[48];
  val(b, sizeof b, get(s, Metric::Rpm), now);
  text(l, 55, 245, 730, b, &cluster_num_220);
  text(l, 65, 470, 200, "RPM", &cluster_text_34, amber);
  val(b, sizeof b, get(s, Metric::SpeedMph), now);
  text(l, 800, 299, 420, b, &cluster_num_144, ink, LV_TEXT_ALIGN_RIGHT);
  text(l, 1020, 470, 200, "MPH", &cluster_text_34, muted, LV_TEXT_ALIGN_RIGHT);
  const Gauge g[] = {
      {Metric::OilPsi, "OIL PRESSURE", "psi", 0, 100, "0", "50", "100", false},
      {Metric::OilTempF, "OIL TEMP", "°F", 140, 300, "140", "220", "300",
       false},
      {Metric::CoolantF, "COOLANT", "°F", 120, 240, "120", "180", "240", false},
      {Metric::BoostPsi, "BOOST / VAC", "psi", -15, 15, "-15", "0", "+15",
       true}};
  const int xs[] = {190, 490, 790, 1090};
  gauges(l, s, now, g, xs, amber);
}
void tuning(lv_layer_t *l, const ViewState &v, const History &h, uint64_t now) {
  const auto &s = v.telemetry;
  text(l, 55, 8, 300, "TUNING / TRACE", &cluster_text_26, cyan);
  header(l, v);
  const int xs[] = {55, 355, 630, 1040};
  const char *names[] = {"ENGINE", "LOAD", "RAW AFR / UNVERIFIED", "THROTTLE"};
  const Metric ms[] = {Metric::Rpm, Metric::MapKpa, Metric::AfrRaw,
                       Metric::TpsPercent};
  const char *units[] = {"RPM", "kPa ABS", "TARGET", "TPS %"};
  for (int i = 0; i < 4; i++) {
    text(l, xs[i], 78, i == 2 ? 400 : 240, names[i], &cluster_text_26, muted);
    char b[48];
    val(b, sizeof b, get(s, ms[i]), now, i == 2 ? 1 : 0);
    const int value_width = i == 0 ? 285 : (i == 2 ? 380 : 240);
    lv_point_t measured{};
    lv_text_get_size(&measured, b, &cluster_num_96, 0, 0, 1000,
                     LV_TEXT_FLAG_NONE);
    const lv_font_t *value_font =
        measured.x > value_width ? &cluster_num_64 : &cluster_num_96;
    text(l, xs[i], 110, value_width, b, value_font);
    if (i == 2) {
      char target[24], label[64];
      if (s.target_echo_possible)
        std::snprintf(target, sizeof target, "--");
      else
        val(target, sizeof target, get(s, Metric::AfrTarget), now, 1);
      const bool warming = s.link == LinkState::Live &&
                           s.target_echo_possible && (s.engine_flags & 1) &&
                           !(s.engine_flags & 2) && s.synchronized &&
                           valid(get(s, Metric::Rpm), now);
      std::snprintf(label, sizeof label, "TARGET %s%s", target,
                    warming ? " / WARMUP" : "");
      text(l, xs[i], 215, 400, label, &cluster_text_26, muted);
    } else
      text(l, xs[i], 215, 240, units[i], &cluster_text_26, muted);
  }
  const char *labels[] = {"RPM", "MAP / kPa", "TPS / %"};
  const uint32_t colors[] = {cyan, mint, amber};
  const float maxes[] = {8000, 180, 100};
  for (int lane = 0; lane < 3; lane++) {
    int basey = 365 + lane * 110;
    text(l, 55, basey - 48, 190, labels[lane], &cluster_text_26, colors[lane]);
    bool have = false;
    float px = 0, py = 0;
    for (size_t i = 0; i < h.size(); i++) {
      const auto &p = h.at(i);
      if (p.time_ms > now || now - p.time_ms > kHistoryWindowMs ||
          !(p.valid_mask & (1 << lane))) {
        have = false;
        continue;
      }
      float value = lane == 0 ? p.rpm : lane == 1 ? p.map_kpa : p.tps_percent;
      if (!std::isfinite(value)) {
        have = false;
        continue;
      }
      float x = 250 +
                970 * (1.0f - (float)(now - p.time_ms) / kHistoryWindowMs),
            y = basey - 70 * clamp(value / maxes[lane], 0, 1);
      if (have)
        line(l, px, py, x, y, colors[lane], 4);
      px = x;
      py = y;
      have = true;
    }
  }
  text(l, 250, 608, 100, "-8 s", &cluster_text_26, muted);
  text(l, 1120, 608, 100, "NOW", &cluster_text_26, muted, LV_TEXT_ALIGN_RIGHT);
  const char *names2[] = {"ADVANCE", "PW", "DUTY", "CLT / IAT", "BATTERY"};
  const Metric mm[] = {Metric::AdvanceDeg, Metric::PulseWidthMs,
                       Metric::InjectorDutyPercent, Metric::CoolantF,
                       Metric::BatteryV};
  const int xx[] = {55, 280, 505, 730, 1030};
  for (int i = 0; i < 5; i++) {
    text(l, xx[i], 665, 240, names2[i], &cluster_text_26, muted);
    char b[48], out[80];
    val(b, sizeof b, get(s, mm[i]), now,
        i == 1                       ? 2
        : i == 0 || i == 2 || i == 4 ? 1
                                     : 0);
    if (i == 3) {
      char second[24];
      val(second, sizeof second, get(s, Metric::IatF), now);
      std::snprintf(out, sizeof out, "%s / %s °F", b, second);
    } else
      std::snprintf(out, sizeof out, "%s %s", b,
                    i == 0   ? "deg"
                    : i == 1 ? "ms"
                    : i == 2 ? "%"
                             : "V");
    text(l, xx[i], 710, 240, out, &cluster_text_34);
  }
}
} // namespace
void Dashboard::create(lv_obj_t *parent) {
  root_ = lv_obj_create(parent);
  lv_obj_remove_style_all(root_);
  lv_obj_set_size(root_, 1280, 800);
  lv_obj_set_pos(root_, 0, 0);
  lv_obj_set_style_bg_color(root_, lv_color_black(), 0);
  lv_obj_set_style_bg_opa(root_, LV_OPA_COVER, 0);
  lv_obj_clear_flag(root_, LV_OBJ_FLAG_SCROLLABLE);
  lv_obj_add_event_cb(root_, draw_event, LV_EVENT_DRAW_MAIN, this);
}
void Dashboard::update(const ViewState &v, const History &h, uint64_t now) {
  const auto &rpm = v.telemetry.get(Metric::Rpm);
  visual_rpm_ = rpm_animation_.step(valid(rpm, now), rpm.value, now,
                                    v.telemetry.link == LinkState::Replay &&
                                        v.replay_paused,
                                    v.telemetry.link);
  view_ = v;
  history_ = h;
  now_ = now;
  if (root_)
    lv_obj_invalidate(root_);
}
void Dashboard::draw_event(lv_event_t *e) {
  auto *self = static_cast<Dashboard *>(lv_event_get_user_data(e));
  auto *l = lv_event_get_layer(e);
  switch (self->view_.mode) {
  case Mode::Street:
    street(l, self->view_, self->now_, self->visual_rpm_);
    break;
  case Mode::Track:
    track(l, self->view_, self->now_, self->visual_rpm_);
    break;
  case Mode::Tuning:
    tuning(l, self->view_, self->history_, self->now_);
    break;
  }
}
} // namespace cluster
