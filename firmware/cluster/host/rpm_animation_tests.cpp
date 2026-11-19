#include "../ui/rpm_animation.hpp"
#include <cstdio>
#include <cstdlib>
#define CHECK(x)                                                               \
  do {                                                                         \
    if (!(x)) {                                                                \
      std::fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #x);                \
      std::exit(1);                                                            \
    }                                                                          \
  } while (0)
#include <cmath>
using namespace cluster;
static bool near(float a, float b) { return std::fabs(a - b) < 0.01f; }
int main() {
  RpmAnimation a;
  CHECK(near(a.step(true, 1000, 100, false, LinkState::Live), 1000));
  CHECK(near(a.step(true, 5000, 200, false, LinkState::Live), 1000));
  CHECK(near(a.step(true, 5000, 240, false, LinkState::Live), 3000));
  CHECK(near(a.step(true, 5000, 400, false, LinkState::Live), 5000));
  CHECK(near(a.step(true, 1000, 401, false, LinkState::Live), 5000));
  CHECK(near(a.step(true, 1000, 441, false, LinkState::Live), 3000));
  CHECK(near(a.step(true, 1000, 441, true, LinkState::Replay),
             1000)); // source reset
  CHECK(near(a.step(true, 5000, 450, false, LinkState::Replay), 1000));
  CHECK(near(a.step(true, 5000, 470, true, LinkState::Replay), 1000));
  CHECK(near(a.step(true, 5000, 5000, true, LinkState::Replay), 1000));
  CHECK(near(a.step(true, 5000, 6000, false, LinkState::Replay), 1000));
  CHECK(near(a.step(true, 5000, 6040, false, LinkState::Replay), 3000));
  CHECK(near(a.step(false, 5000, 6050, false, LinkState::Stale), 0));
  CHECK(near(a.step(true, 2000, 6060, false, LinkState::Live), 2000));
  CHECK(
      near(a.step(true, 4000, 1, false, LinkState::Live), 4000)); // clock reset
  RpmAnimation retarget;
  CHECK(near(retarget.step(true, 1000, 0, false, LinkState::Live), 1000));
  CHECK(near(retarget.step(true, 5000, 1, false, LinkState::Live), 1000));
  CHECK(near(retarget.step(true, 2000, 41, false, LinkState::Live), 3000));
  CHECK(near(retarget.step(true, 2000, 81, false, LinkState::Live), 2500));
  CHECK(near(retarget.step(true, 2000, 200, false, LinkState::Live), 2000));
  return 0;
}
