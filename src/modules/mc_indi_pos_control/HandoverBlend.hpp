#pragma once

/**
 * Bumpless transfer of the commanded acceleration when the INDI stage takes over from the bypass (D-HANDOVER, A-45).
 * In bypass the stock velocity integrator runs; the stage zeroes it on its first cycle, so the reference acceleration
 * steps by the integrator value (2.7 m/s^2 at the end of the take-off ramp). On the first stage cycle the offset
 * o = a_bypass_last - a_ref is added to a_ref, then decays as exp(-t / tau). Header only, unit tested.
 */

#include <cmath>

#include <matrix/math.hpp>

class HandoverBlend
{
public:
	/** tau <= 0 disables the blend (offset always zero). */
	void setTimeConstant(float tau) { _tau = tau; }

	/** Bypass cycle: remember the acceleration the stock path commanded, its integrator included. */
	void bypass(const matrix::Vector3f &a_bypass)
	{
		_offset.zero(); // no stale offset survives a bypass, whatever the next capture does
		_pending = a_bypass.isAllFinite();

		if (_pending) {
			_a_bypass = a_bypass;
		}
	}

	/** Stage cycle: a_ref plus the decaying offset. The offset is captured on the first cycle after a bypass. */
	matrix::Vector3f apply(const matrix::Vector3f &a_ref, float dt)
	{
		if (_pending) {
			_pending = false;
			_offset = (_tau > 0.f && a_ref.isAllFinite()) ? matrix::Vector3f(_a_bypass - a_ref) : matrix::Vector3f{};

		} else if (_tau > 0.f && dt > 0.f && std::isfinite(dt)) {
			_offset *= expf(-dt / _tau);

		} else if (!(_tau > 0.f)) {
			_offset.zero();
		}

		return a_ref + _offset;
	}

	/** Stage cycle that does not reach apply() (Hold): the offset decays in time, a pending capture waits. */
	void decay(float dt)
	{
		if (!_pending && _tau > 0.f && dt > 0.f && std::isfinite(dt)) {
			_offset *= expf(-dt / _tau);
		}
	}

	/** The stage is not run at all (module outside position control): drop the capture and the offset. */
	void clear()
	{
		_pending = false;
		_offset.zero();
	}

	const matrix::Vector3f &offset() const { return _offset; }

private:
	matrix::Vector3f _a_bypass{};
	matrix::Vector3f _offset{};
	float _tau{0.5f};
	bool _pending{false};
};
