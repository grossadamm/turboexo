#include "cluster/calibration.hpp"

#include <algorithm>
#include <cmath>

namespace cluster {
namespace {

constexpr int32_t kMaxAdcCount = 32767;
constexpr size_t kMaxKnotCount = 16;

} // namespace

bool calibration_valid(const CalibrationKnot* knots, size_t count,
                       float min_value, float max_value)
{
    if (!knots || count < 2 || count > kMaxKnotCount ||
        !std::isfinite(min_value) || !std::isfinite(max_value) || min_value >= max_value) {
        return false;
    }
    for (size_t i = 0; i < count; ++i) {
        const auto& knot = knots[i];
        if (knot.raw_counts < 0 || knot.raw_counts > kMaxAdcCount ||
            !std::isfinite(knot.value) || knot.value < min_value || knot.value > max_value ||
            (i != 0 && knot.raw_counts <= knots[i - 1].raw_counts)) {
            return false;
        }
    }
    return true;
}

Reading calibrated_reading(const CalibrationKnot* knots, size_t count,
                           int32_t raw_counts, float min_value, float max_value,
                           uint64_t now_ms)
{
    if (!calibration_valid(knots, count, min_value, max_value) ||
        raw_counts < knots[0].raw_counts || raw_counts > knots[count - 1].raw_counts) {
        return {};
    }

    const auto* upper = std::lower_bound(knots + 1, knots + count, raw_counts,
                                         [](const CalibrationKnot& knot, int32_t counts) {
                                             return knot.raw_counts < counts;
                                         });
    const auto& lower = *(upper - 1);
    const double fraction = static_cast<double>(raw_counts - lower.raw_counts) /
                            (upper->raw_counts - lower.raw_counts);
    const float value = static_cast<float>((1 - fraction) * lower.value + fraction * upper->value);
    return {value, Quality::Valid, now_ms};
}

} // namespace cluster
