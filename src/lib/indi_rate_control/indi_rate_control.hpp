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
 *   dt_cmd = G1^-1 (nu - angular_accel)            roll, pitch
 *   t_cmd  = t_f + dt_cmd                          bounded to [-1, 1]
 *
 * An optional extra low-pass on the yaw axis is applied to both angular_accel and t_f, so the
 * pair stays synchronised while the yaw noise is reduced. The same cut-off also filters the
 * yaw rate error used in nu (nu_yaw = K_Y * lpf(rate_sp - rate)), setpoint included, as the PID
 * yaw torque output filter (MC_YAW_TQ_CUTOFF) does for the whole PID yaw command.
 *
 * Yaw adds the rotor spin-up term G2 (Smeur 2016, torque space form):
 *   (G1 + G2/dt) dt_cmd = nu - angular_accel + (G2/dt) (t_f - t_f_prev)
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
	 */
	void setDelaySamples(int delay_samples) { _delay_samples = math::constrain(delay_samples, 0, kMaxDelaySamples); }

	/**
	 * Set the per axis limit of the torque increment, non finite or <= 0 values select 1.
	 */
	void setMaxIncrement(float max_increment)
	{
		_max_increment = (math::isFinite(max_increment) && (max_increment > 0.f)) ? max_increment : 1.f;
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
	 *        model and its filters keep running)
	 * @return [-1,1] normalised torque vector to apply to the vehicle. On invalid inputs the last valid output is
	 *         held for kFaultHoldCycles consecutive cycles, then the states are reset and the output is zero
	 */
	matrix::Vector3f update(const matrix::Vector3f &rate, const matrix::Vector3f &rate_sp,
				const matrix::Vector3f &angular_accel, const matrix::Vector3f &torque_allocated_prev,
				float dt, bool landed);

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

	static constexpr float kMinG1 = 1e-3f;      ///< smallest valid control effectiveness
	static constexpr float kMinDt = 0.000125f;  ///< shortest valid cycle time (8 kHz)
	static constexpr float kMaxDt = 0.02f;      ///< longest valid cycle time (50 Hz)

private:
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
	int _delay_samples{0};
	float _max_increment{1.f};
	float _yaw_cutoff_hz{0.f}; ///< 0 = yaw low pass disabled

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
	math::LowPassFilter2p<float> _lpf[3];
	AlphaFilter<float> _alpha[3];
	math::LowPassFilter2p<float> _yaw_lpf_accel; ///< yaw low pass on the angular acceleration
	math::LowPassFilter2p<float> _yaw_lpf_torque; ///< same design on the filtered torque
	math::LowPassFilter2p<float> _yaw_error_lpf; ///< same design on the yaw rate error in nu
	matrix::Vector3f _t_f_prev; ///< filtered torque of the previous cycle (yaw spin-up term)
	matrix::Vector3f _t_cmd_last; ///< last valid output, held on rejected cycles
	int _fault_cycles{0}; ///< consecutive rejected cycles

	// Outputs for logging
	matrix::Vector3f _nu;
	matrix::Vector3f _a_f;
	matrix::Vector3f _t_f;
	matrix::Vector3f _dt_cmd;
	bool _fault{false};
};
