/****************************************************************************
 *
 *   Copyright (c) 2026 PX4 Development Team. All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in
 *    the documentation and/or other materials provided with the
 *    distribution.
 * 3. Neither the name PX4 nor the names of its contributors may be
 *    used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 * COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
 * OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
 * AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 * ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 *
 ****************************************************************************/

/**
 * @file IndiInjection.hpp
 *
 * Bench-only loop-break excitation of mc_indi_rate_control (system identification, off by default).
 * A Schroeder-phase multisine d on one torque axis, added to the controller output c (u = c + d).
 * Frequencies are log-spaced (10 per decade) integer multiples of 1/Tp, phases are Schroeder phases for equal power.
 */

#pragma once

#include <stdint.h>

class IndiInjection
{
public:
	/** Maximum number of sine components. Bins above the 64th (highest frequencies) are dropped. */
	static constexpr int MAX_COMPONENTS = 64;

	/**
	 * Set the excitation. Rebuilds the frequency/phase tables and restarts the time origin only if a value changed.
	 * @param axis 0 off, 1 roll, 2 pitch, 3 yaw (anything else: off)
	 * @param amplitude amplitude of each sine component (normalised torque)
	 * @param period multisine period Tp (s), frequencies are k/Tp
	 * @param f_min lowest frequency (Hz)
	 * @param f_max highest frequency (Hz)
	 * @param n_periods number of periods flown
	 * @param delay start delay after the first airborne cycle (s), so the excitation starts in established flight
	 */
	void setParameters(int axis, float amplitude, float period, float f_min, float f_max, int n_periods, float delay);

	/** Torque axis index (0 roll, 1 pitch, 2 yaw) or -1 when off */
	int axis() const { return _axis - 1; }

	int numComponents() const { return _num; }

	/**
	 * Excitation of the current cycle. Not evaluated (returns exactly 0) when off, disarmed, landed or outside
	 * [0, n_periods * period) after the origin, which is delay after the first cycle that is on, armed and not landed.
	 * @param timestamp_sample_us cycle time (gyro sample time), microseconds
	 */
	float update(uint64_t timestamp_sample_us, bool armed, bool landed);

	/** Restart the sequence (delay first) at the next update, e.g. when the break point changes */
	void restart() { _started = false; }

	/** Multisine at time t (s) after the origin, without the enable logic of update() */
	double waveform(double t) const;

private:
	int _axis{0};
	float _amp{0.f};
	float _period{0.f};
	float _f_min{0.f};
	float _f_max{0.f};
	int _n_periods{0};
	float _delay{0.f};

	int _num{0};
	double _freq[MAX_COMPONENTS] {};	///< Hz
	double _phase[MAX_COMPONENTS] {};	///< rad

	bool _started{false};
	uint64_t _t0_us{0};
};
