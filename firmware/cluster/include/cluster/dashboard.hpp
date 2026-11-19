#pragma once
#include "../../ui/rpm_animation.hpp"
#include "cluster/types.hpp"
#include <lvgl.h>
namespace cluster {
class Dashboard {
public:
  void create(lv_obj_t *parent);
  void update(const ViewState &, const History &, uint64_t now_ms);

private:
  static void draw_event(lv_event_t *event);
  lv_obj_t *root_ = nullptr;
  ViewState view_{};
  History history_{};
  uint64_t now_ = 0;
  RpmAnimation rpm_animation_{};
  float visual_rpm_ = 0;
};
} // namespace cluster
