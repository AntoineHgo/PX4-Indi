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
 * @file indi_rate_control.hpp
 *
 * INDI (Incremental Nonlinear Dynamic Inversion) 3 axis angular rate control.
 *
 * Control law in normalised torque space (see indi_project/plan/architecture.md):
 *
 *   nu     = K .* (rate_sp - rate)                 desired angular acceleration
 *   t_act  = first order lag of the allocated torque (actuator model)
 *   t_f    = H(delay(t_act))                       same filter chain as the gyro derivative
 *   c      = lead_scale K tau_c                    rate prediction lead, tau_c = actuator time constant,
 *                                                  c <= 2, 0 on ground
 *   r_dot  = low passed, clamped derivative of rate_sp (kSetpointLeadTc, kMaxRateSpDot), 0 on ground
 *   dt_cmd = G1^-1 (nu - (1 + c) angular_accel + c r_dot)   roll, pitch
 *   t_cmd  = t_f + dt_cmd                          bounded to [-1, 1]
 *
 * The same prediction on the setpoint path (decision D-S3-ATT-STEP) gives nu_eff = K (1 + tau_c s)(rate_sp - rate), so a
 * rate setpoint that moves (attitude loop output) is not followed with the actuator lag; no extra parameter,
 * MC_INDI_LEAD = 0 turns both terms off. r_dot is 0 at the first cycle, after reset() and resetSetpointLead(), on
 * ground and on rejected cycles, so that no derivative impulse enters the law.
 *
 * An optional extra low-pass on the yaw axis is applied to both angular_accel and t_f, so the
 * pair stays synchronised while the yaw noise is reduced. The same cut-off also filters the
 * yaw rate error used in nu (nu_yaw = K_Y * lpf(rate_sp - rate)), setpoint included, as the PID
 * yaw torque output filter (MC_YAW_TQ_CUTOFF) does for the whole PID yaw command.
 *
 * Yaw adds the rotor spin-up term G2, as a first order low pass on the increment (backward Euler of
 * (G1 + G2 s) Delta = nu - (1 + c) angular_accel), Delta_prev = increment applied in the previous cycle:
 *   (G1 + G2/dt) dt_cmd = nu - (1 + c) angular_accel + (G2/dt) Delta_prev
 * DC gain 1/G1, time constant G2/G1, independent of dt. G2 is the rotor inertia reaction per unit torque rate,
 * so G2/G1 is not the motor time constant.
 *
 * Measured torque path (optional, decision D-omega2): setMeasuredTorque() supplies tau_meas = B u from the ESC
 * rotor speeds. It runs through its own delay and its own copy of H in parallel to the model, and replaces
 * the modelled t_f after kMeasValidCycles consecutive valid cycles. Any invalid cycle falls back to the model
 * at once. While invalid, the measurement path is fed the model's t_act so that the switch back is bumpless.
 * Optional blend (setActuatorBlendTimeConstant()): t_f = t_f_meas + b, with b a first order low pass of
 * (t_f_model - t_f_meas). The measurement keeps the high frequencies and the model the low ones, which restores
 * the integral action of the model state against a steady command/output gap. b tracks the difference while the
 * measurement is not in use, the blend is disabled or on ground, so every switch is bumpless.
 *
 * There is no integrator. All memory is statically allocated.
 */

#pragma once

#include <stdint.h>

#include <matrix/matrix/math.hpp>

#include <mathlib/mathlib.h>
#include <mathlib/math/filter/AlphaFilter.hpp>
#include <mathlib/math/filter/LowPassFilter2p.hpp>

class IndiRateControl
{
public:
	IndiRateControl() { reset(); }
	~IndiRateControl() = default;

	/// Maximum supported synchronisation delay in controller cycles
	static constexpr int kMaxDelaySamples = 4;

	/// Consecutive rejected cycles during which the last valid output is held before a reset to zero torque
	static constexpr int kFaultHoldCycles = 3;

	/**
	 * Set the rate tracking bandwidth.
	 * @param gain_k per axis closed loop bandwidth in rad/s, >= 0 (0 stops rate tracking on that axis, the law
	 *        then only drives the angular acceleration to zero), negative or non finite values fault update()
	 */
	void setGainK(const matrix::Vector3f &gain_k) { _gain_k = gain_k; }

	/**
	 * Set the control effectiveness.
	 * @param g1 per axis angular acceleration per unit normalised torque in rad/s^2.
	 *        A component < kMinG1 or non finite makes update() fault and return zero.
	 */
	void setG1(const matrix::Vector3f &g1) { _g1 = g1; }

	/**
	 * Set the yaw rotor spin-up term, negative or non finite values are replaced by 0.
	 */
	void setG2Yaw(float g2_yaw) { _g2_yaw = (math::isFinite(g2_yaw) && (g2_yaw > 0.f)) ? g2_yaw : 0.f; }

	/**
	 * Set the time constant of the first order actuator model, clamped to [0.001, 0.2] s.
	 */
	void setActuatorTimeConstant(float actuator_tc);

	/**
	 * Set the time constant of the complementary blend between the measured (high frequency) and the modelled
	 * (low frequency) torque, clamped to <= kMaxBlendTimeConstant s. A value <= 0 or non finite disables the
	 * blend: the measured torque alone is used when it is in use.
	 */
	void setActuatorBlendTimeConstant(float tb_s);

	/**
	 * Set the scale of the rate prediction lead c = scale K tau_c on the angular acceleration feedback.
	 * 0 = off (law without lead), 1 = full. Non finite or negative values give 0, values above 1 give 1.
	 */
	void setLeadScale(float scale) { _lead_scale = math::isFinite(scale) ? math::constrain(scale, 0.f, 1.f) : 0.f; }

	/**
	 * Restart the rate setpoint derivative at the next update(): r_dot is 0 in that cycle. Call when the source of the
	 * rate setpoint changes (mode switch, setpoint timeout or recovery), where the setpoint may jump.
	 */
	void resetSetpointLead() { _sp_lead_reset = true; }

	/** Filtered and clamped derivative of the rate setpoint used in the last cycle (rad/s^2), for logging. */
	const matrix::Vector3f &getRateSpDot() const { return _rate_sp_dot; }

	/** Lead gain c applied per axis in the last cycle (0 when landed), for logging. */
	const matrix::Vector3f &getLeadGain() const { return _lead_gain; }

	/**
	 * Set the cutoffs of the synchronisation filter H, mirroring IMU_GYRO_CUTOFF (second order
	 * low pass) and IMU_DGYRO_CUTOFF (first order low pass). A value <= 0 or non finite
	 * makes the stage pass-through, as in the sensor chain.
	 */
	void setFilterCutoffs(float gyro_cutoff_hz, float dgyro_cutoff_hz);

	/**
	 * Set the cutoff of an extra second order low pass applied to the yaw component of both the
	 * angular acceleration and the filtered torque, and of the measured rate in nu. A value <= 0 or non finite disables it, as
	 * does a value above 0.45 x the controller sample rate. Roll and pitch are not affected.
	 */
	void setYawCutoff(float cutoff_hz) { _yaw_cutoff_hz = (math::isFinite(cutoff_hz) && (cutoff_hz > 0.f)) ? cutoff_hz : 0.f; }

	/**
	 * Set the pure delay applied to the actuator model output, clamped to [0, kMaxDelaySamples].
	 * A change is applied at once by reset(), and otherwise by one sample per update(), so that a change in
	 * flight moves t_f by at most one cycle of actuator history per cycle instead of jumping several cycles.
	 */
	void setDelaySamples(int delay_samples) { _delay_samples_target = math::constrain(delay_samples, 0, kMaxDelaySamples); }

	/**
	 * Set the pure delay applied to the measured torque, same clamping and one sample per update() slew as
	 * setDelaySamples(). A change is applied at once by reset().
	 */
	void setMeasurementDelaySamples(int delay_samples)
	{
		_meas_delay_samples_target = math::constrain(delay_samples, 0, kMaxDelaySamples);
	}

	/**
	 * Supply the measured normalised torque (B u, u_i = (omega_i / omega_max)^2, same units as the output of
	 * update()) for the next update() call only. Validity must be supplied every cycle: a cycle without a call
	 * counts as invalid, as does a non finite torque, which never enters the filters. The model path keeps
	 * running either way, the measurement replaces the modelled torque in the law after kMeasValidCycles
	 * consecutive valid cycles and is dropped at the first invalid one (decision D-omega2).
	 */
	void setMeasuredTorque(const matrix::Vector3f &tau_meas, bool valid)
	{
		_tau_meas = tau_meas;
		_meas_valid_pending = valid;
	}

	/**
	 * Normalised rotor thrust u = (rpm / rpm_max)^2 clamped to [0, 1], for building the measured torque.
	 * @param rpm measured rotor speed, rpm_max the speed at full thrust (same unit)
	 * @param u set only if the return value is true
	 * @return false (u untouched) for a non finite rpm or rpm_max, rpm_max <= 0, rpm < 0 or an implausible
	 *         rpm > kMaxRpmRatio x rpm_max
	 */
	static bool normalisedThrustFromRpm(float rpm, float rpm_max, float &u)
	{
		if (!math::isFinite(rpm) || !math::isFinite(rpm_max) || !(rpm_max > 0.f) || (rpm < 0.f)
		    || (rpm > kMaxRpmRatio * rpm_max)) {
			return false;
		}

		const float ratio = rpm / rpm_max;
		u = math::constrain(ratio * ratio, 0.f, 1.f);
		return true;
	}

	/**
	 * Set the per axis limit of the torque increment. Non finite or <= 0 values are ignored and the last valid
	 * limit is kept (1, the full torque range, until a valid value is set), so an invalid value never widens it.
	 */
	void setMaxIncrement(float max_increment)
	{
		if (math::isFinite(max_increment) && (max_increment > 0.f)) {
			_max_increment = max_increment;
		}
	}

	/**
	 * Set the slew of the feedback torque on both edges of landed, in normalised torque per second.
	 * Non finite or <= 0 values are ignored.
	 */
	void setLandedSlew(float slew)
	{
		if (math::isFinite(slew) && (slew > 0.f)) {
			_landed_slew = slew;
		}
	}

	/**
	 * Run one control loop cycle calculation
	 * @param rate current vehicle angular rate (rad/s)
	 * @param rate_sp desired vehicle angular rate (rad/s)
	 * @param angular_accel filtered angular acceleration (rad/s^2), same filter chain as H
	 *        (the yaw component additionally goes through the yaw low pass if enabled)
	 * @param torque_allocated_prev normalised torque the allocator actually produced from the previous command
	 * @param dt time since the previous call in s, valid range [kMinDt, kMaxDt]
	 * @param landed true if ground contact is assumed (the feedback torque is held out of the law, the actuator
	 *        model and its filters keep running); the feedback torque is ramped with the landed slew on both
	 *        edges of this flag instead of stepping
	 * @param maybe_landed true if ground contact is possible: the law runs in full, only the slow blend
	 *        integrator is frozen (no output slew limit, like the stock PID freezing only its integrator)
	 * @return [-1,1] normalised torque vector to apply to the vehicle. On invalid inputs the last valid output is
	 *         held for kFaultHoldCycles consecutive cycles, then the states are reset and the output is zero
	 */
	matrix::Vector3f update(const matrix::Vector3f &rate, const matrix::Vector3f &rate_sp,
				const matrix::Vector3f &angular_accel, const matrix::Vector3f &torque_allocated_prev,
				float dt, bool landed, bool maybe_landed = false);

	/**
	 * Set all dynamic states (actuator model, delay buffer, filters, previous filtered torque,
	 * held output, logged outputs) to zero. Parameters, filter design and the fault flag are kept.
	 */
	void reset();

	/// Logging getters, values of the last update() call
	const matrix::Vector3f &getNu() const { return _nu; }
	const matrix::Vector3f &getFilteredAngularAccel() const { return _a_f; }
	const matrix::Vector3f &getFilteredTorque() const { return _t_f; }
	const matrix::Vector3f &getTorqueIncrement() const { return _dt_cmd; }

	/// True if the last update() call rejected its inputs or parameters
	bool getFault() const { return _fault; }

	/// True if the last update() call used the measured torque as t_f instead of the actuator model
	bool measurementInUse() const { return _meas_in_use; }

	/// Blend state t_f_model - t_f_meas, low passed, of the last update() call
	const matrix::Vector3f &getActuatorBlend() const { return _blend; }

	/// Filtered torque of each path in the last update() call (not zeroed on ground, unlike getFilteredTorque())
	const matrix::Vector3f &getFilteredModelTorque() const { return _t_f_model; }
	const matrix::Vector3f &getFilteredMeasuredTorque() const { return _t_f_meas; }

	/// Time constant of the first order low pass on the rate setpoint derivative, s
	static constexpr float kSetpointLeadTc = 0.03f;

	/// Magnitude bound of the filtered rate setpoint derivative per axis, rad/s^2: an impulse guard against setpoint
	/// jumps that slip through the resets, not a shaping filter (a 5 rad/s step over one 1 kHz cycle would be 5000)
	static constexpr float kMaxRateSpDot = 1000.f;

	static constexpr float kMinG1 = 1e-3f;      ///< smallest valid control effectiveness
	static constexpr float kMinDt = 0.000125f;  ///< shortest valid cycle time (8 kHz)
	static constexpr float kMaxDt = 0.02f;      ///< longest valid cycle time (50 Hz)

	/**
	 * Consecutive valid measurement cycles before the measured torque replaces the model in the law (the
	 * counting cycle is the first to use it). About twice the worst case settling at 1 kHz: kMaxDelaySamples
	 * of delay slew plus roughly 6 cycles for the sync filters (LPF2p and alpha, tens of Hz) to converge from
	 * the model value they were fed while the measurement was invalid.
	 */
	static constexpr int kMeasValidCycles = 20;

	/// Measured rpm above this multiple of rpm_max is rejected as implausible by normalisedThrustFromRpm()
	static constexpr float kMaxRpmRatio = 1.5f;

private:
	static constexpr float kMaxLeadGain = 2.f; ///< upper limit of the lead gain c = scale K tau_c
	static constexpr float kMaxBlendTimeConstant = 10.f; ///< s, upper limit of the blend time constant
	static constexpr float kMaxBlend = 2.f; ///< bound of the blend state per axis, both torques are within [-1, 1]
	static constexpr int kDelayBufferSize = kMaxDelaySamples + 1;
	static constexpr float kRedesignRatio = 0.1f; ///< relative sample rate change that triggers a filter redesign
	static constexpr float kSampleFreqAlpha = 0.01f; ///< low pass on 1/dt for the design rate, so dt jitter does not redesign
	static constexpr float kMaxYawCutoffRatio = 0.45f; ///< yaw low pass is disabled above this fraction of the sample rate

	bool paramsValid() const;
	void designSyncFilters(float sample_freq, bool reset_states);
	void designYawFilters(float sample_freq);
	void resetStates();

	/// Output of a rejected cycle: the held last valid output, or zero with reset states once the hold expires
	matrix::Vector3f faultOutput(bool states_corrupted);

	// Parameters
	matrix::Vector3f _gain_k{20.f, 20.f, 10.f};
	matrix::Vector3f _g1{100.f, 100.f, 20.f};
	float _g2_yaw{0.f};
	float _actuator_tc{0.02f};
	float _gyro_cutoff_hz{30.f};
	float _dgyro_cutoff_hz{30.f};
	int _delay_samples_target{0};
	float _max_increment{1.f};
	float _landed_slew{5.f}; ///< feedback torque slew on the edges of landed (1/s)
	matrix::Vector3f _t_fb_prev{}; ///< feedback torque applied in the previous cycle
	bool _landed_prev{false}; ///< landed flag of the previous cycle (no edge at the first call in flight)
	bool _landed_ramp{false}; ///< a landed edge is being ramped
	float _yaw_cutoff_hz{0.f}; ///< 0 = yaw low pass disabled
	int _meas_delay_samples_target{0};
	float _blend_tc{0.f}; ///< 0 = blend disabled
	float _lead_scale{1.f}; ///< scale of the rate prediction lead, 0 = off
	matrix::Vector3f _lead_gain{}; ///< c applied in the last cycle, logging

	// Filter design bookkeeping
	float _design_sample_freq{0.f}; ///< sample rate the filters are designed for, 0 = not designed
	float _sample_freq_filtered{0.f}; ///< low-passed 1/dt, 0 = no sample yet
	float _design_gyro_cutoff_hz{0.f};
	float _design_dgyro_cutoff_hz{0.f};
	float _design_yaw_cutoff_hz{0.f};
	bool _yaw_filter_active{false};  ///< yaw low pass designed and in use
	bool _yaw_filter_reset_pending{false}; ///< settle the yaw low pass at the next unfiltered values

	// States
	matrix::Vector3f _t_act;   ///< actuator model output
	matrix::Vector3f _t_lpf;   ///< last output of the H low pass, restores it on a sample rate redesign
	matrix::Vector3f _t_delay_buffer[kDelayBufferSize]; ///< ring buffer of past _t_act
	int _delay_head{0};        ///< index of the most recent sample in the ring buffer
	int _delay_samples{0};     ///< delay in use, slewed toward _delay_samples_target by one sample per cycle
	math::LowPassFilter2p<float> _lpf[3];
	AlphaFilter<float> _alpha[3];

	// Measurement path, same structure and design as the model path above
	matrix::Vector3f _tau_meas;          ///< measured torque supplied for the next update()
	bool _meas_valid_pending{false};     ///< validity supplied for the next update(), cleared by every update()
	matrix::Vector3f _meas_t_lpf;        ///< last output of the measurement H low pass
	matrix::Vector3f _meas_delay_buffer[kDelayBufferSize]; ///< ring buffer of past measurement path inputs
	int _meas_delay_head{0};
	int _meas_delay_samples{0};          ///< slewed toward _meas_delay_samples_target by one sample per cycle
	math::LowPassFilter2p<float> _meas_lpf[3];
	AlphaFilter<float> _meas_alpha[3];
	int _meas_valid_cycles{0};           ///< consecutive valid cycles, saturates at kMeasValidCycles
	bool _meas_in_use{false};
	matrix::Vector3f _blend; ///< low passed t_f_model - t_f_meas, tracks it when the blend is not active

	math::LowPassFilter2p<float> _yaw_lpf_accel; ///< yaw low pass on the angular acceleration
	math::LowPassFilter2p<float> _yaw_lpf_torque; ///< same design on the filtered torque
	math::LowPassFilter2p<float> _yaw_error_lpf; ///< same design on the yaw rate error in nu
	math::LowPassFilter2p<float> _yaw_sp_lpf; ///< same design on the yaw rate setpoint, differentiated for r_dot
	matrix::Vector3f _rate_sp_prev; ///< rate setpoint (yaw: as it enters the yaw rate error) of the previous cycle
	bool _sp_lead_reset{true}; ///< r_dot restarts at 0 in the next update()
	float _yaw_inc_prev{0.f}; ///< yaw increment applied in the previous cycle, 0 on ground (yaw spin-up term)
	matrix::Vector3f _t_cmd_last; ///< last valid output, held on rejected cycles
	int _fault_cycles{0}; ///< consecutive rejected cycles

	// Outputs for logging
	matrix::Vector3f _nu;
	matrix::Vector3f _a_f;
	matrix::Vector3f _t_f;
	matrix::Vector3f _t_f_model;
	matrix::Vector3f _t_f_meas;
	matrix::Vector3f _dt_cmd;
	matrix::Vector3f _rate_sp_dot;
	bool _fault{false};
};

/**
 * Rate bandwidth gains K applied by the loop: the set gains while the physical parameters are identified,
 * half of them before (conservative identification configuration, D-DEFAULTS-FW).
 */
inline matrix::Vector3f indiEffectiveGainK(const matrix::Vector3f &k_set, bool identified)
{
	return identified ? k_set : k_set * 0.5f;
}
