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

#pragma once

#include <AttitudeControl.hpp>
#include <lib/indi_accel_control/indi_accel_control.hpp>
#include <lib/indi_rate_control/indi_rate_control.hpp>
#include <lib/matrix/matrix/math.hpp>
#include <lib/perf/perf_counter.h>
#include <px4_platform_common/defines.h>
#include <px4_platform_common/module.h>
#include <px4_platform_common/module_params.h>
#include <px4_platform_common/px4_work_queue/ScheduledWorkItem.hpp>
#include <uORB/Publication.hpp>
#include <uORB/Subscription.hpp>
#include <uORB/SubscriptionCallback.hpp>
#include <uORB/topics/arming_check_reply.h>
#include <uORB/topics/arming_check_request.h>
#include <uORB/topics/esc_status.h>
#include <uORB/topics/indi_pos_status.h>
#include <uORB/topics/parameter_update.h>
#include <uORB/topics/register_ext_component_reply.h>
#include <uORB/topics/register_ext_component_request.h>
#include <uORB/topics/sensor_combined.h>
#include <uORB/topics/setpoint_config.h>
#include <uORB/topics/trajectory_setpoint.h>
#include <uORB/topics/unregister_ext_component.h>
#include <uORB/topics/vehicle_attitude.h>
#include <uORB/topics/vehicle_land_detected.h>
#include <uORB/topics/vehicle_local_position.h>
#include <uORB/topics/vehicle_rates_setpoint.h>
#include <uORB/topics/vehicle_status.h>

using namespace time_literals;

/**
 * Outer-loop (acceleration) INDI position controller, registered as an external flight mode.
 * Library: IndiAccelControl. Attitude loop: a module-owned AttitudeControl configured like mc_att_control.
 * Output: vehicle_rates_setpoint (TYPE_RATES), consumed by the rate controller (PID or INDI).
 */
class McIndiPosControl : public ModuleBase, public ModuleParams, public px4::ScheduledWorkItem
{
public:
	static Descriptor desc;

	McIndiPosControl();
	~McIndiPosControl() override;

	/** @see ModuleBase */
	static int task_spawn(int argc, char *argv[]);

	/** @see ModuleBase */
	static int custom_command(int argc, char *argv[]);

	/** @see ModuleBase */
	static int print_usage(const char *reason = nullptr);

	bool init();

private:
	static constexpr uint64_t EXT_COMPONENT_REQUEST_ID = 4711;
	static constexpr int kNumMotors = 4;
	/// Inputs older than this are stale (hold rule)
	static constexpr hrt_abstime kStaleTimeout = 100_ms;
	/// Cycles the last rates setpoint is repeated before level rates are published
	static constexpr int kMaxHoldCycles = 3;
	/// The ESC sample is used for the mean thrust only while younger than this
	static constexpr hrt_abstime kEscMaxAge = 50_ms;
	/// Samples used to measure the mean cycle rate for the low pass filters
	static constexpr int kRateSamples = 50;
	static constexpr float kMinDt = 0.002f;
	static constexpr float kMaxDt = 0.05f;
	/// Period of the backup schedule that serves the arming check and the stale detection
	static constexpr hrt_abstime kBackupPeriod = 20_ms;

	void Run() override;

	void parameters_updated();
	void applyFilterConfig();

	/** Registration reply and arming check request handling */
	void updateExternalMode();
	void registerMode();

	/** Latest accelerometer, ESC based mean thrust. */
	void updateSensors(hrt_abstime now);

	/** One controller cycle. new_position is true if vehicle_local_position delivered a new sample. */
	void runCycle(hrt_abstime now, bool new_position);

	/** Rate / thrust setpoint publication */
	void publishRates(const matrix::Vector3f &rates, float thrust);

	/** Repeat the last setpoint (up to kMaxHoldCycles cycles), then level rates with the last thrust */
	void hold(hrt_abstime now);


	void measureRate(hrt_abstime t);

	void publishStatus(const IndiAccelControl::Output &out, float mean_u, bool mean_u_valid);

	// ----- subscriptions / publications
	uORB::SubscriptionCallbackWorkItem _local_position_sub{this, ORB_ID(vehicle_local_position)};
	uORB::Subscription _vehicle_attitude_sub{ORB_ID(vehicle_attitude)};
	uORB::Subscription _sensor_combined_sub{ORB_ID(sensor_combined)};
	uORB::Subscription _esc_status_sub{ORB_ID(esc_status)};
	uORB::Subscription _trajectory_setpoint_sub{ORB_ID(trajectory_setpoint)};
	uORB::Subscription _land_detected_sub{ORB_ID(vehicle_land_detected)};
	uORB::Subscription _vehicle_status_sub{ORB_ID(vehicle_status)};
	uORB::Subscription _register_reply_sub{ORB_ID(register_ext_component_reply)};
	uORB::Subscription _arming_check_request_sub{ORB_ID(arming_check_request)};
	uORB::Subscription _parameter_update_sub{ORB_ID(parameter_update)};

	uORB::Publication<vehicle_rates_setpoint_s> _rates_setpoint_pub{ORB_ID(vehicle_rates_setpoint)};
	uORB::Publication<indi_pos_status_s> _status_pub{ORB_ID(indi_pos_status)};
	uORB::Publication<register_ext_component_request_s> _register_request_pub{ORB_ID(register_ext_component_request)};
	uORB::Publication<unregister_ext_component_s> _unregister_pub{ORB_ID(unregister_ext_component)};
	uORB::Publication<setpoint_config_s> _setpoint_config_pub{ORB_ID(setpoint_config)};
	uORB::Publication<arming_check_reply_s> _arming_check_reply_pub{ORB_ID(arming_check_reply)};

	// ----- latest inputs
	vehicle_local_position_s _local_position{};
	vehicle_attitude_s _attitude{};
	sensor_combined_s _sensor_combined{};
	trajectory_setpoint_s _trajectory_setpoint{};
	bool _have_local_position{false};
	bool _have_attitude{false};
	bool _have_sensor{false};
	bool _have_trajectory{false};
	bool _landed{true};

	// ESC based mean thrust
	float _mean_u{NAN};
	bool _mean_u_valid{false};
	hrt_abstime _esc_time{0};
	param_t _param_w_max_handle{PARAM_INVALID};
	float _rotor_w_max{0.f};	///< rad/s, 0 = unknown

	// ----- external mode
	enum class ModeState : uint8_t {
		UNREGISTERED,
		REGISTERED
	};

	ModeState _mode_state{ModeState::UNREGISTERED};
	int8_t _arming_check_id{-1};
	int8_t _mode_id{-1};
	bool _active{false};
	vehicle_status_s _vehicle_status{};

	// ----- control
	IndiAccelControl _indi{};
	AttitudeControl _attitude_control{};
	bool _filter_ready{false};
	float _filter_rate_hz{0.f};
	int _rate_count{0};
	hrt_abstime _rate_t0{0};
	hrt_abstime _last_cycle_time{0};
	float _last_thrust{0.f};
	matrix::Vector3f _last_rates{};
	int _hold_count{0};
	bool _failure_reported{false};
	bool _needs_reset{true};

	perf_counter_t _loop_perf;

	DEFINE_PARAMETERS(
		(ParamBool<px4::params::MC_INDIP_OFFB>) _param_offb,
		(ParamFloat<px4::params::MC_INDIP_LPF_CUT>) _param_lpf_cut,
		(ParamFloat<px4::params::MC_INDIP_G_T>) _param_g_t,
		(ParamFloat<px4::params::MC_INDIP_K_CMD>) _param_k_cmd,
		(ParamInt<px4::params::MC_INDIP_DLY>) _param_dly,
		(ParamBool<px4::params::MC_INDIP_FF>) _param_ff,

		// shared with the stock position controller
		(ParamFloat<px4::params::MPC_XY_P>) _param_mpc_xy_p,
		(ParamFloat<px4::params::MPC_Z_P>) _param_mpc_z_p,
		(ParamFloat<px4::params::MPC_XY_VEL_P_ACC>) _param_mpc_xy_vel_p_acc,
		(ParamFloat<px4::params::MPC_Z_VEL_P_ACC>) _param_mpc_z_vel_p_acc,
		(ParamFloat<px4::params::MPC_XY_VEL_MAX>) _param_mpc_xy_vel_max,
		(ParamFloat<px4::params::MPC_Z_VEL_MAX_UP>) _param_mpc_z_vel_max_up,
		(ParamFloat<px4::params::MPC_Z_VEL_MAX_DN>) _param_mpc_z_vel_max_dn,
		(ParamFloat<px4::params::MPC_TILTMAX_AIR>) _param_mpc_tiltmax_air,
		(ParamFloat<px4::params::MPC_THR_MIN>) _param_mpc_thr_min,
		(ParamFloat<px4::params::MPC_THR_MAX>) _param_mpc_thr_max,
		(ParamFloat<px4::params::MPC_THR_HOVER>) _param_mpc_thr_hover,

		// shared with the stock attitude controller
		(ParamFloat<px4::params::MC_ROLL_P>) _param_mc_roll_p,
		(ParamFloat<px4::params::MC_PITCH_P>) _param_mc_pitch_p,
		(ParamFloat<px4::params::MC_YAW_P>) _param_mc_yaw_p,
		(ParamFloat<px4::params::MC_YAW_WEIGHT>) _param_mc_yaw_weight,
		(ParamFloat<px4::params::MC_ROLLRATE_MAX>) _param_mc_rollrate_max,
		(ParamFloat<px4::params::MC_PITCHRATE_MAX>) _param_mc_pitchrate_max,
		(ParamFloat<px4::params::MC_YAWRATE_MAX>) _param_mc_yawrate_max,
		(ParamFloat<px4::params::MC_REF_W_N>) _param_mc_ref_w_n,
		(ParamFloat<px4::params::MC_REF_FF>) _param_mc_ref_ff,
		(ParamFloat<px4::params::MC_REF_FF_MAX>) _param_mc_ref_ff_max
	)
};
