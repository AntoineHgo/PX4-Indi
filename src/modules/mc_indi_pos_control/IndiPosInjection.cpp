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

#include "IndiPosInjection.hpp"

#include <math.h>

void IndiPosInjection::setParameters(int axis, float amplitude, float period, float f_min, float f_max, int n_periods, float delay)
{
	if (axis < 0 || axis > 3) {
		axis = 0;
	}

	// unchanged parameters (values come from the parameter system, not computed): the stored copy compares bit-exact
	if (axis == _axis && !(amplitude < _amp) && !(amplitude > _amp) && !(period < _period) && !(period > _period)
	    && !(f_min < _f_min) && !(f_min > _f_min) && !(f_max < _f_max) && !(f_max > _f_max) && n_periods == _n_periods
	    && !(delay < _delay) && !(delay > _delay)) {
		return;
	}

	_axis = axis;
	_amp = amplitude;
	_period = period;
	_f_min = f_min;
	_f_max = f_max;
	_n_periods = n_periods;
	_delay = (delay > 0.f) ? delay : 0.f;
	_started = false;
	_num = 0;

	if (_axis == 0 || !(period > 0.f) || !(f_min > 0.f) || !(f_max > f_min) || n_periods < 1) {
		return;
	}

	// log-spaced bins, 10 per decade, rounded to integer multiples k of the base frequency 1 / Tp
	const double df = 1.0 / (double)period;
	const int per_decade = 10;
	const int n = (int)ceil(log10((double)f_max / (double)f_min) * per_decade) + 1;
	int last_k = 0;

	for (int i = 0; i < n && _num < MAX_COMPONENTS; i++) {
		const double f = (double)f_min * pow(10.0, (double)i / per_decade);
		const int k = (int)round(f / df);

		// np.unique keeps each bin once (k is non-decreasing), then k >= 1 and k * df <= fmax * (1 + 0.5 * df / fmax)
		if (k < 1 || k == last_k || k * df > (double)f_max + 0.5 * df) {
			continue;
		}

		last_k = k;
		_freq[_num++] = k * df;
	}

	// Schroeder phases for equal power p = 1 / K: phi_k = -2 pi sum_{l<k} (k - l) p_l  (k = 0 .. K - 1)
	for (int k = 0; k < _num; k++) {
		double s = 0.0;

		for (int l = 0; l < k; l++) {
			s += (k - l) * (1.0 / _num);
		}

		_phase[k] = -2.0 * M_PI * s;
	}
}

double IndiPosInjection::waveform(double t) const
{
	double d = 0.0;

	for (int i = 0; i < _num; i++) {
		d += (double)_amp * cos(2.0 * M_PI * _freq[i] * t + _phase[i]);
	}

	return d;
}

float IndiPosInjection::update(uint64_t timestamp_sample_us, bool armed, bool landed)
{
	if (_axis == 0 || _num == 0) {
		return 0.f;
	}

	if (!armed) {
		reset(); // a new flight restarts the excitation
		return 0.f;
	}

	if (landed) {
		return 0.f;
	}

	if (!_started) {
		_started = true;
		_t0_us = timestamp_sample_us + (uint64_t)(_delay * 1e6f);
	}

	if (timestamp_sample_us < _t0_us) {
		return 0.f;
	}

	const double t = (double)(timestamp_sample_us - _t0_us) * 1e-6;

	if (t >= (double)_n_periods * (double)_period) {
		return 0.f;
	}

	return (float)waveform(t);
}
