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
 * @file indi_accel_control.cpp
 */

#include "indi_accel_control.hpp"

#include <float.h>
#include <px4_platform_common/defines.h>

using namespace matrix;

void IndiAccelControl::setGains(const Vector3f &k_pos, const Vector3f &k_vel)
{
	for (int i = 0; i < 3; i++) {
		if (PX4_ISFINITE(k_pos(i)) && (k_pos(i) >= 0.f)) {
			_k_pos(i) = k_pos(i);
		}

		if (PX4_ISFINITE(k_vel(i)) && (k_vel(i) >= 0.f)) {
			_k_vel(i) = k_vel(i);
		}
	}
}

void IndiAccelControl::setLimits(float vel_xy_max, float vel_z_up_max, float vel_z_down_max, float tilt_max_rad,
				 float thr_min, float thr_max)
{
	if (!PX4_ISFINITE(vel_xy_max) || !PX4_ISFINITE(vel_z_up_max) || !PX4_ISFINITE(vel_z_down_max)
	    || !PX4_ISFINITE(tilt_max_rad) || !PX4_ISFINITE(thr_min) || !PX4_ISFINITE(thr_max)
	    || (vel_xy_max <= 0.f) || (vel_z_up_max <= 0.f) || (vel_z_down_max <= 0.f)
	    || (thr_min < 0.f) || (thr_max > 1.f) || (thr_min > thr_max)) {
		return;
	}

	_vel_xy_max = vel_xy_max;
	_vel_z_up_max = vel_z_up_max;
	_vel_z_down_max = vel_z_down_max;
	_tilt_max = math::constrain(tilt_max_rad, 0.f, kMaxTiltLimit);
	_thr_min = thr_min;
	_thr_max = thr_max;
}

void IndiAccelControl::setFilter(float sample_freq_hz, float cutoff_hz)
{
	_lpf_f.set_cutoff_frequency(sample_freq_hz, cutoff_hz);
	_lpf_u.set_cutoff_frequency(sample_freq_hz, cutoff_hz);
	_lpf_um.set_cutoff_frequency(sample_freq_hz, cutoff_hz);
	_lpf_j.set_cutoff_frequency(sample_freq_hz, cutoff_hz);

	// set_cutoff_frequency() zeroes the delay elements (output would fall to 0 and take the filter time to
	// come back): re-seed every filter from its last output instead
	_lpf_f.reset(_last_f_b);
	_lpf_u.reset(_last_u);
	_lpf_um.reset(_last_um);
	_lpf_j.reset(_j_diff_f);
}

void IndiAccelControl::setThrustModel(float g_t, float k_cmd)
{
	if (PX4_ISFINITE(g_t) && (g_t > FLT_EPSILON)) {
		_g_t = g_t;
	}

	if (PX4_ISFINITE(k_cmd) && (k_cmd > FLT_EPSILON)) {
		_k_cmd = k_cmd;
	}
}

void IndiAccelControl::setBlendTimeConstant(float tb_s)
{
	if (PX4_ISFINITE(tb_s) && (tb_s > FLT_EPSILON)) {
		_tb = tb_s;

	} else {
		_tb = 0.f;
		_b = 0.f;
	}
}

void IndiAccelControl::reset(const Vector3f &f_b, float coll_cmd, float mean_u)
{
	const Vector3f f = allFinite(f_b) ? f_b : Vector3f(0.f, 0.f, -kGravity);
	const float c = PX4_ISFINITE(coll_cmd) ? math::max(coll_cmd, 0.f) : kGravity / (_g_t * _k_cmd);

	// D-GAP: model path = commanded collective (u_model = c * k_cmd). Measured path = the measured mean u when it is
	// given, else its steady relation to the model path, u_model - b. Either way u_meas + b = u_model at the
	// restart (no collective step at the edge, no innovation for b; A16: b is held, never reset)
	const float u_model = c * _k_cmd;
	const float u = PX4_ISFINITE(mean_u) ? mean_u : (u_model - _b);

	_lpf_f.reset(f);
	_lpf_u.reset(u);
	_lpf_um.reset(u_model);
	_last_f_b = f;
	_last_u = u;
	_last_um = u_model;

	for (int i = 0; i <= kMaxDelaySamples; i++) {
		_u_buf[i] = u;
		_um_buf[i] = u_model;
	}

	_u_idx = 0;
	_thrust_prev = c;

	_time = 0.f;
	_a_ref_prev.zero();
	_j_diff.zero();
	_lpf_j.reset(_j_diff);

	for (int i = 0; i < 3; i++) {
		_t_a_ref_prev[i] = 0.f;
		_a_ref_prev_valid[i] = false;
	}
}

void IndiAccelControl::updateJerkDifference(const Vector3f &a_ref, const bool a_valid[3], float dt)
{
	_time += dt;

	for (int i = 0; i < 3; i++) {
		if (!a_valid[i]) {
			// no reference: no jerk, forget the history so that the return does not create a spike
			_a_ref_prev_valid[i] = false;
			_j_diff(i) = 0.f;
			continue;
		}

		if (!_a_ref_prev_valid[i]) {
			_a_ref_prev(i) = a_ref(i);
			_t_a_ref_prev[i] = _time;
			_a_ref_prev_valid[i] = true;
			_j_diff(i) = 0.f;
			continue;
		}

		if (fabsf(a_ref(i) - _a_ref_prev(i)) > 0.f) {
			const float dt_change = math::max(_time - _t_a_ref_prev[i], kMinDt);
			_j_diff(i) = math::constrain((a_ref(i) - _a_ref_prev(i)) / dt_change, -kMaxJerk, kMaxJerk);
			_a_ref_prev(i) = a_ref(i);
			_t_a_ref_prev[i] = _time;
		}

		// else: a_ref unchanged, hold the last difference
	}

	// A setpoint stream slower than the loop makes the held difference a staircase: smooth it with the
	// measurement filter cut-off so that its steps do not reach the rate setpoint.
	_j_diff_f = _lpf_j.apply(_j_diff);
}

Quatf IndiAccelControl::bodyzToAttitude(Vector3f body_z, const float yaw_sp)
{
	// zero vector, no direction, set safe level value
	if (body_z.norm_squared() < FLT_EPSILON) {
		body_z(2) = 1.f;
	}

	body_z.normalize();

	// vector of desired yaw direction in XY plane, rotated by PI/2
	const Vector3f y_C{-sinf(yaw_sp), cosf(yaw_sp), 0.f};

	// desired body_x axis, orthogonal to body_z
	Vector3f body_x = y_C % body_z;

	// keep nose to front while inverted upside down
	if (body_z(2) < 0.f) {
		body_x = -body_x;
	}

	if (fabsf(body_z(2)) < 0.000001f) {
		// desired thrust is in XY plane, set X downside to construct correct matrix
		body_x.zero();
		body_x(2) = 1.f;
	}

	body_x.normalize();

	// desired body_y axis
	const Vector3f body_y = body_z % body_x;

	Dcmf R_sp;

	for (int i = 0; i < 3; i++) {
		R_sp(i, 0) = body_x(i);
		R_sp(i, 1) = body_y(i);
		R_sp(i, 2) = body_z(i);
	}

	return Quatf(R_sp);
}

void IndiAccelControl::setAppliedThrust(float c_applied)
{
	if (PX4_ISFINITE(c_applied)) {
		_thrust_prev = math::constrain(c_applied / (_g_t * _k_cmd), _thr_min, _thr_max);
	}
}

bool IndiAccelControl::update(const Input &in, Output &out)
{
	// 9. required inputs, checked before any state is touched
	if ((!in.accel_only && (!allFinite(in.p) || !allFinite(in.v))) || !allFinite(in.f_b) || !PX4_ISFINITE(in.q(0)) || !PX4_ISFINITE(in.q(1))
	    || !PX4_ISFINITE(in.q(2)) || !PX4_ISFINITE(in.q(3)) || !PX4_ISFINITE(in.dt)
	    || (in.mean_u_valid && !PX4_ISFINITE(in.mean_u))) {
		return false;
	}

	if ((in.dt < kMinDt) || (in.dt > kMaxDt) || (in.q.norm() < 0.5f)) {
		return false;
	}

	const Quatf q = in.q.normalized();
	const Dcmf R(q);
	const Vector3f z_b = R.col(2);

	// 1. reference handling
	Vector3f p_term{};
	Vector3f v_ff{};
	Vector3f a_ref{};
	bool a_valid[3] {};

	for (int i = 0; i < 3; i++) {
		p_term(i) = (!in.accel_only && PX4_ISFINITE(in.p_ref(i))) ? _k_pos(i) * (in.p_ref(i) - in.p(i)) : 0.f;
		v_ff(i) = (!in.accel_only && PX4_ISFINITE(in.v_ref(i))) ? in.v_ref(i) : 0.f;
		a_valid[i] = PX4_ISFINITE(in.a_ref(i));
		a_ref(i) = a_valid[i] ? in.a_ref(i) : 0.f;
	}

	updateJerkDifference(a_ref, a_valid, in.dt);

	Vector3f j_used{};
	bool from_diff = false;

	for (int i = 0; i < 3; i++) {
		if (PX4_ISFINITE(in.j_ref(i))) {
			j_used(i) = math::constrain(in.j_ref(i), -kMaxJerk, kMaxJerk);

		} else {
			j_used(i) = _j_diff_f(i);
			from_diff = true;
		}
	}

	// 2. commanded acceleration
	Vector3f v_sp = p_term + v_ff;
	const float vxy = Vector2f(v_sp(0), v_sp(1)).norm();

	if (vxy > _vel_xy_max) {
		const float s = _vel_xy_max / vxy;
		v_sp(0) *= s;
		v_sp(1) *= s;
	}

	v_sp(2) = math::constrain(v_sp(2), -_vel_z_up_max, _vel_z_down_max);

	Vector3f a_c{};

	for (int i = 0; i < 3; i++) {
		a_c(i) = in.accel_only ? a_ref(i) : (_k_vel(i) * (v_sp(i) - in.v(i)) + a_ref(i));
	}

	// 3. measured acceleration
	const Vector3f f_bf = _lpf_f.apply(in.f_b);
	_last_f_b = f_bf;
	const Vector3f a_f = R * f_bf + Vector3f(0.f, 0.f, kGravity);

	// 4. measured thrust
	const float u_model = _thrust_prev * _k_cmd;
	// invalid telemetry: feed u_model - b so that u_meas_f + b stays continuous (no step at loss or recovery)
	const float u_in = in.mean_u_valid ? in.mean_u : (u_model - _b);
	_u_idx = (_u_idx + 1) % (kMaxDelaySamples + 1);
	_u_buf[_u_idx] = u_in;
	_um_buf[_u_idx] = u_model;
	const int i_d = (_u_idx + kMaxDelaySamples + 1 - _delay) % (kMaxDelaySamples + 1);
	const float u_meas_f = _lpf_u.apply(_u_buf[i_d]);
	const float u_model_f = _lpf_um.apply(_um_buf[i_d]);
	_last_u = u_meas_f;
	_last_um = u_model_f;

	// D-GAP blend: b = LP_tb(u_model - u_meas), held (never reset) on the ground, at bypass edges (hold flag),
	// while the telemetry is invalid and while the collective is clamped (anti-windup)
	// anti-windup also on the measured mean_u at its physical limit and on the allocator saturation report
	const bool u_at_limit = in.mean_u_valid && (in.mean_u >= kMeanUSatLimit);
	const bool blend_frozen = _blend_hold || !in.mean_u_valid || _coll_clamped || u_at_limit || in.alloc_saturated;

	if ((_tb > 0.f) && !blend_frozen) {
		_b += (in.dt / (_tb + in.dt)) * ((u_model_f - u_meas_f) - _b);
		_b = math::constrain(_b, -kMaxBlend, kMaxBlend);
	}

	// u_f = u_meas_f + b also with invalid telemetry (the measured path was fed u_model - b)
	const float u_f = (_tb > 0.f) ? (u_meas_f + _b) : u_meas_f;
	const Vector3f t_f = z_b * (-_g_t * u_f);

	// 5. INDI increment
	Vector3f t_c = t_f + (a_c - a_f);

	// 6. saturation, vertical priority
	const float c_min = _g_t * _k_cmd * _thr_min;
	const float c_max = _g_t * _k_cmd * _thr_max;

	if (!PX4_ISFINITE(t_c(0)) || !PX4_ISFINITE(t_c(1)) || !PX4_ISFINITE(t_c(2))) {
		return false;
	}

	if (t_c(2) > -kMinUpThrust) {
		t_c(2) = -math::max(c_min, kMinUpThrust);
	}

	// tilt: angle between t_c and -e3 (up in NED), scale the horizontal part keeping t_c,z
	const float h_max = -t_c(2) * tanf(_tilt_max);
	const float h = Vector2f(t_c(0), t_c(1)).norm();

	if (h > h_max) {
		const float s = (h > FLT_EPSILON) ? h_max / h : 0.f;
		t_c(0) *= s;
		t_c(1) *= s;
	}

	float c = t_c.norm();

	bool clamped = false;

	if (c > c_max) {
		clamped = true;
		// keep the vertical component, shrink the horizontal part first
		const float z_abs = -t_c(2);

		if (z_abs < c_max) {
			const float h_allowed = sqrtf(math::max(c_max * c_max - z_abs * z_abs, 0.f));
			const float h_now = Vector2f(t_c(0), t_c(1)).norm();
			const float s = (h_now > FLT_EPSILON) ? h_allowed / h_now : 0.f;
			t_c(0) *= s;
			t_c(1) *= s;

		} else {
			t_c = Vector3f(0.f, 0.f, -c_max);
		}

		c = t_c.norm();

	} else if (c < c_min) {
		clamped = true;
		// below the minimum thrust: scale the whole vector, direction (tilt) unchanged
		t_c *= c_min / c;
		c = t_c.norm();
	}

	const float thrust = math::constrain(c / (_g_t * _k_cmd), _thr_min, _thr_max);
	const bool coll_clamped = clamped || (thrust <= _thr_min) || (thrust >= _thr_max);

	// 7. attitude
	const float yaw = PX4_ISFINITE(in.yaw_ref) ? in.yaw_ref : Eulerf(q).psi();
	const Vector3f body_z_d = -t_c / c;
	const Quatf q_d = bodyzToAttitude(body_z_d, yaw);

	// 8. rate feedforward
	Vector3f omega_ff{};

	if (_jerk_ff && (c >= kMinThrustForFf)) {
		const Dcmf R_d(q_d);
		const Vector3f x_b = R_d.col(0);
		const Vector3f y_b = R_d.col(1);
		omega_ff(0) = math::constrain(j_used.dot(y_b) / c, -kMaxOmegaFf, kMaxOmegaFf);
		omega_ff(1) = math::constrain(-j_used.dot(x_b) / c, -kMaxOmegaFf, kMaxOmegaFf);
	}

	if (!PX4_ISFINITE(thrust) || !allFinite(omega_ff) || !PX4_ISFINITE(q_d(0)) || !PX4_ISFINITE(q_d(1))
	    || !PX4_ISFINITE(q_d(2)) || !PX4_ISFINITE(q_d(3))) {
		return false;
	}

	_thrust_prev = thrust;
	_coll_clamped = coll_clamped;

	out.q_d = q_d;
	out.yawspeed_ff = PX4_ISFINITE(in.yawspeed_ref) ? in.yawspeed_ref : 0.f;
	out.thrust = thrust;
	out.omega_ff = omega_ff;
	out.a_c = a_c;
	out.a_f = a_f;
	out.t_f = t_f;
	out.t_c = t_c;
	out.j_used = j_used;
	out.jerk_from_difference = from_diff;
	out.blend = _b;
	out.blend_frozen = blend_frozen;
	return true;
}
