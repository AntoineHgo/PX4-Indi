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
 * @file indi_accel_control.hpp
 *
 * Outer-loop (acceleration) INDI with jerk feedforward, see indi_project/plan/s8_impl_spec.md sec. 2.
 *
 * Frames: NED world, FRD body, R = R(q) body -> world. Specific thrust t = -c z_b (c > 0), g_vec = (0, 0, +g).
 * The accelerometer measures f_b = R^T (a - g_vec), so a_f = R f_b_filtered + g_vec.
 *
 *   a_c = K_vel (v_sp - v) + a_ref,   v_sp = K_pos (p_ref - p) + v_ref   (no integrator, INDI supplies it)
 *   t_f = -g_t u_f z_b                u_f = LPF(delay(mean_u)), same filter as f_b
 *   t_c = t_f + (a_c - a_f)           thrust vector with vertical priority saturation
 *   z_b,d = -t_c / |t_c|              q_d from z_b,d and the yaw reference
 *   omega_ff = (j.y_b, -j.x_b, 0) / c rate feedforward from the jerk reference (optional)
 *
 * Library only: no uORB, no parameters. All memory is statically allocated, there are no loops of variable bound.
 */

#pragma once

#include <stdint.h>

#include <matrix/matrix/math.hpp>

#include <mathlib/mathlib.h>
#include <mathlib/math/filter/LowPassFilter2p.hpp>

class IndiAccelControl
{
public:
	IndiAccelControl() { reset(matrix::Vector3f(0.f, 0.f, -kGravity), 0.f); }
	~IndiAccelControl() = default;

	/// Maximum supported delay of the mean rotor thrust sample in controller cycles
	static constexpr int kMaxDelaySamples = 4;

	static constexpr float kGravity = 9.80665f;
	/// Clamp of the jerk reference per axis in m/s^3
	static constexpr float kMaxJerk = 50.f;
	/// Clamp of the rate feedforward per axis in rad/s
	static constexpr float kMaxOmegaFf = 3.f;
	/// Below this thrust magnitude (m/s^2) the rate feedforward is zero
	static constexpr float kMinThrustForFf = 1.f;
	/// Smallest accepted upward vertical component of the commanded specific thrust (m/s^2)
	static constexpr float kMinUpThrust = 0.1f;
	/// Accepted range of the cycle time (s)
	static constexpr float kMinDt = 1e-4f;
	static constexpr float kMaxDt = 0.5f;
	/// Upper bound of the tilt limit (rad), keeps tan() finite
	static constexpr float kMaxTiltLimit = 1.5f;
	/// Bound of the collective blend state b (u units)
	static constexpr float kMaxBlend = 0.3f;

	struct Input {
		matrix::Vector3f p{};      ///< position NED (m)
		matrix::Vector3f v{};      ///< velocity NED (m/s)
		matrix::Quatf q{};         ///< attitude body -> world
		matrix::Vector3f f_b{};    ///< accelerometer specific force, body frame (m/s^2)
		float mean_u{NAN};         ///< mean normalised rotor thrust (only used if mean_u_valid)
		bool mean_u_valid{false};
		matrix::Vector3f p_ref{NAN, NAN, NAN};  ///< NaN component: no position term on that axis
		matrix::Vector3f v_ref{NAN, NAN, NAN};  ///< NaN component: 0 feedforward on that axis
		matrix::Vector3f a_ref{NAN, NAN, NAN};  ///< NaN component: 0
		matrix::Vector3f j_ref{NAN, NAN, NAN};  ///< NaN component: backward difference of a_ref
		float yaw_ref{NAN};        ///< NaN: keep the yaw of q
		float yawspeed_ref{NAN};   ///< NaN: 0
		float dt{0.f};             ///< time since the previous call (s), [kMinDt, kMaxDt]
		bool accel_only{false};    ///< start at a_ref (A14): no p/v terms, a_c = a_ref, p and v are not required
	};

	struct Output {
		matrix::Quatf q_d{};                  ///< desired attitude
		float yawspeed_ff{0.f};               ///< yaw rate reference (rad/s)
		float thrust{0.f};                    ///< normalised thrust command, >= 0
		matrix::Vector3f omega_ff{};          ///< body rate feedforward (rad/s), z = 0
		matrix::Vector3f a_c{};               ///< commanded acceleration (m/s^2)
		matrix::Vector3f a_f{};               ///< measured (filtered) acceleration
		matrix::Vector3f t_f{};               ///< measured (filtered) specific thrust vector
		matrix::Vector3f t_c{};               ///< commanded specific thrust vector after saturation
		matrix::Vector3f j_used{};            ///< jerk reference used for the feedforward
		bool jerk_from_difference{false};     ///< true if any axis of j_used came from the a_ref difference
		float blend{0.f};                     ///< collective blend state b (u units)
		bool blend_frozen{false};             ///< b was held this cycle (hold flag, invalid telemetry, clamp)
	};

	/**
	 * Per axis (x, y, z) position and velocity loop gains. Non finite or negative components are ignored
	 * (the previous value of that component is kept).
	 */
	void setGains(const matrix::Vector3f &k_pos, const matrix::Vector3f &k_vel);

	/**
	 * Limits. vel_*_max > 0, tilt_max_rad clamped to [0, kMaxTiltLimit], 0 <= thr_min <= thr_max <= 1 is
	 * required. If any argument is invalid the whole call is ignored.
	 */
	void setLimits(float vel_xy_max, float vel_z_up_max, float vel_z_down_max, float tilt_max_rad,
		       float thr_min, float thr_max);

	/**
	 * One filter for f_b (3D) and one for the mean thrust, same sample rate and cut-off (filter matching).
	 * cutoff_hz <= 0, non finite or >= sample_freq_hz / 2 disables both. Resets the filter states: call
	 * reset() afterwards.
	 */
	void setFilter(float sample_freq_hz, float cutoff_hz);

	/**
	 * Thrust model: g_t > 0 specific thrust (m/s^2) per unit mean u, k_cmd > 0 mean u per unit thrust command.
	 * Invalid values are ignored.
	 */
	void setThrustModel(float g_t, float k_cmd);

	/// Delay of the mean u sample in cycles, clamped to [0, kMaxDelaySamples]. Applied at once.
	void setMeasurementDelay(int samples) { _delay = math::constrain(samples, 0, kMaxDelaySamples); }
	int measurementDelay() const { return _delay; }

	/**
	 * D-GAP collective blend: u_f = u_meas + b, b = LP_tb(u_model - u_meas), so the collective is measured at
	 * high frequency and modelled (previous clamped command) at DC. tb <= 0 or non finite disables it and sets
	 * b = 0. b is also zero at construction; reset() leaves it alone.
	 */
	void setBlendTimeConstant(float tb_s);
	float blendTimeConstant() const { return _tb; }
	float blend() const { return _b; }

	/// Freeze b (landed, bypass, edges). Takes effect on the next update(); b is held, never reset.
	void setBlendHold(bool hold) { _blend_hold = hold; }

	/**
	 * Bench loop break at the stage output: the vehicle receives a thrust-acceleration magnitude c_applied (m/s^2)
	 * other than the one update() returned. Sets the previous thrust command to the clamped normalised value of it
	 * (same conversion and limits as update()), so the blend model path follows what the actuator was given.
	 * Non finite values are ignored.
	 */
	void setAppliedThrust(float c_applied);

	void setFeedforward(bool jerk_ff) { _jerk_ff = jerk_ff; }

	/**
	 * Initialise the filters and the delay buffer to these values (no increment step), forget the jerk
	 * difference history and set the previous thrust command to the model value mean_u / k_cmd.
	 * Non finite arguments are replaced by hover values.
	 */
	void reset(const matrix::Vector3f &f_b, float mean_u);

	/**
	 * Run one cycle.
	 * @return false (out untouched) if a required input is non finite or invalid (p, v, q, f_b, dt,
	 *         mean_u if mean_u_valid), so the caller can hold.
	 */
	bool update(const Input &in, Output &out);

	/**
	 * Same attitude construction as ControlMath::bodyzToAttitude() in
	 * src/modules/mc_pos_control/PositionControl/ControlMath.cpp (reimplemented to avoid linking a module
	 * target into a library): body z axis and yaw reference to quaternion.
	 */
	static matrix::Quatf bodyzToAttitude(matrix::Vector3f body_z, float yaw_sp);

private:
	static bool allFinite(const matrix::Vector3f &v)
	{
		return PX4_ISFINITE(v(0)) && PX4_ISFINITE(v(1)) && PX4_ISFINITE(v(2));
	}

	/// jerk reference from the a_ref difference, per axis, holds between changes of a_ref, then low-pass filtered
	void updateJerkDifference(const matrix::Vector3f &a_ref, const bool a_valid[3], float dt);

	// configuration
	matrix::Vector3f _k_pos{0.95f, 0.95f, 1.f};
	matrix::Vector3f _k_vel{1.8f, 1.8f, 4.f};
	float _vel_xy_max{12.f};
	float _vel_z_up_max{3.f};
	float _vel_z_down_max{1.5f};
	float _tilt_max{0.7854f};
	float _thr_min{0.12f};
	float _thr_max{1.f};
	float _g_t{19.6f};
	float _k_cmd{1.f};
	int _delay{0};
	bool _jerk_ff{true};

	// state
	math::LowPassFilter2p<matrix::Vector3f> _lpf_f{};
	math::LowPassFilter2p<float> _lpf_u{};
	float _u_buf[kMaxDelaySamples + 1] {};
	int _u_idx{0};
	// model path of the collective blend: previous clamped command through the same delay and filter
	math::LowPassFilter2p<float> _lpf_um{};
	float _um_buf[kMaxDelaySamples + 1] {};
	float _tb{0.f};
	float _b{0.f};
	bool _blend_hold{false};
	bool _coll_clamped{false};	///< collective was clamped in the previous update
	float _thrust_prev{0.f};

	// jerk backward difference state
	float _time{0.f};
	matrix::Vector3f _a_ref_prev{};
	float _t_a_ref_prev[3] {};
	bool _a_ref_prev_valid[3] {};
	matrix::Vector3f _j_diff{};
	math::LowPassFilter2p<matrix::Vector3f> _lpf_j{};
	matrix::Vector3f _j_diff_f{};	///< _j_diff low-pass filtered, used as the jerk reference
};
