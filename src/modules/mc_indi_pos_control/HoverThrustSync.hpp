#pragma once

#include <cmath>
#include <px4_platform_common/defines.h>
#include "PositionControl/PositionControl.hpp"

/**
 * T9: hand the hover thrust to the stock PositionControl as MulticopterPositionControl does. A change of the value
 * goes through updateHoverThrust(), which shifts the vertical velocity integrator so the stock (bypass path) thrust
 * does not step; the first value and an unchanged value use setHoverThrust(). The INDI stage keeps its own ht.
 * `last` is the value given to the PositionControl so far (NAN before the first call).
 */
inline void syncHoverThrust(PositionControl &control, float &last, const float ht)
{
	if (PX4_ISFINITE(last) && fabsf(ht - last) > 1e-6f) {
		control.updateHoverThrust(ht);

	} else {
		control.setHoverThrust(ht);
	}

	last = ht;
}
