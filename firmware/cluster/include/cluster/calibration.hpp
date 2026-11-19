#pragma once

#include "cluster/types.hpp"

namespace cluster {

struct CalibrationKnot {
    int32_t raw_counts;
    float value;
};

// Knots use ascending, nonnegative ADS1115 single-ended counts. Values must
// stay within the supplied engineering range. Readings outside the measured
// count range are unavailable. A null/empty profile represents no calibration.
bool calibration_valid(const CalibrationKnot* knots, size_t count,
                       float min_value, float max_value);
Reading calibrated_reading(const CalibrationKnot* knots, size_t count,
                           int32_t raw_counts, float min_value, float max_value,
                           uint64_t now_ms);

} // namespace cluster
