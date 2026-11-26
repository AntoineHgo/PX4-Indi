#pragma once

/**
 * Detection of a change of the vehicle_local_position estimator reset counters. Pure, header only.
 * The first sample only latches the counters (a counter that is already non zero at start is not a reset).
 */

#include <cstdint>

struct EkfResetCounters {
	uint8_t xy{0};
	uint8_t z{0};
	uint8_t vxy{0};
	uint8_t vz{0};
	uint8_t heading{0};
};

class EkfResetDetector
{
public:
	/** @return true once for each sample in which any counter differs from the previous sample */
	bool update(const EkfResetCounters &c)
	{
		const bool changed = _initialized
				     && ((c.xy != _last.xy) || (c.z != _last.z) || (c.vxy != _last.vxy) || (c.vz != _last.vz)
					 || (c.heading != _last.heading));
		_last = c;
		_initialized = true;
		return changed;
	}

private:
	EkfResetCounters _last{};
	bool _initialized{false};
};
