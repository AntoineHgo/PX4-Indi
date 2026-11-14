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

#include <lib/indi_rate_control/indi_rate_control.hpp>
#include <lib/matrix/matrix/math.hpp>
#include <lib/perf/perf_counter.h>
#include <px4_platform_common/defines.h>
#include <px4_platform_common/module.h>
#include <px4_platform_common/module_params.h>
#include <px4_platform_common/px4_work_queue/WorkItem.hpp>
#include <uORB/Publication.hpp>
#include <uORB/Subscription.hpp>
#include <uORB/SubscriptionCallback.hpp>
#include <uORB/SubscriptionInterval.hpp>
#include <uORB/topics/actuator_controls_status.h>
#include <uORB/topics/actuator_motors.h>
#include <uORB/topics/actuator_torque_measured.h>
#include <uORB/topics/control_allocator_status.h>
#include <uORB/topics/esc_status.h>
#include <uORB/topics/indi_rate_status.h>
#include <uORB/topics/manual_control_setpoint.h>
#include <uORB/topics/parameter_update.h>
#include <uORB/topics/vehicle_angular_velocity.h>
#include <uORB/topics/vehicle_control_mode.h>
#include <uORB/topics/vehicle_land_detected.h>
#include <uORB/topics/vehicle_rates_setpoint.h>
#include <uORB/topics/vehicle_status.h>
#include <uORB/topics/vehicle_thrust_setpoint.h>
#include <uORB/topics/vehicle_torque_setpoint.h>

#include <ActuatorEffectivenessMultirotor.hpp>

#include "IndiMeasuredTorque.hpp"

using namespace time_literals;

/**
 * Multicopter rate controller using incremental nonlinear dynamic inversion (IndiRateControl).
 * Alternative to mc_rate_control (PID), only one of the two is started (see rc.mc_apps, MC_INDI_EN).
 */
class McIndiRateControl : public ModuleBase, public ModuleParams, public px4::WorkItem
{
public:
	static Descriptor desc;

	McIndiRateControl();
	~McIndiRateControl() override;

	/** @see ModuleBase */
	static int task_spawn(int argc, char *argv[]);

	/** @see ModuleBase */
	static int custom_command(int argc, char *argv[]);

	/** @see ModuleBase */
	static int print_usage(const char *reason = nullptr);

	bool init();

private:
	void Run() override;

	/**
	 * initialize some vectors/matrices from parameters
	 */
	void parameters_updated();

	/**
	 * Load the rotor geometry of the control allocator (CA_ROTOR*) for the measured torque
	 */
	void updateMeasuredTorqueEffectiveness();

	/**
	 * Torque produced by the ESC rotor speeds, published as actuator_torque_measured and used by the next cycle
	 */
	void updateMeasuredTorque();

	void updateActuatorControlsStatus(const vehicle_torque_setpoint_s &vehicle_torque_setpoint, float dt);

	/**
	 * Run the INDI rate law, publishes indi_rate_status
	 * @return normalised torque setpoint
	 */
	matrix::Vector3f runIndiRateControl(const matrix::Vector3f &rates, const matrix::Vector3f &angular_accel, float dt,
					    bool landed);

	IndiRateControl _indi; ///< INDI rate law

	ActuatorEffectivenessMultirotor _effectiveness{this}; ///< rotor geometry, same parameters as the control allocator
	IndiMeasuredTorque _measured_torque_model;

	uORB::Subscription _control_allocator_status_sub{ORB_ID(control_allocator_status)};
	uORB::Subscription _esc_status_sub{ORB_ID(esc_status)};
	uORB::Subscription _manual_control_setpoint_sub{ORB_ID(manual_control_setpoint)};
	uORB::Subscription _vehicle_control_mode_sub{ORB_ID(vehicle_control_mode)};
	uORB::Subscription _vehicle_land_detected_sub{ORB_ID(vehicle_land_detected)};
	uORB::Subscription _vehicle_rates_setpoint_sub{ORB_ID(vehicle_rates_setpoint)};
	uORB::Subscription _vehicle_status_sub{ORB_ID(vehicle_status)};

	uORB::SubscriptionInterval _parameter_update_sub{ORB_ID(parameter_update), 1_s};

	uORB::SubscriptionCallbackWorkItem _vehicle_angular_velocity_sub{this, ORB_ID(vehicle_angular_velocity)};

	uORB::Publication<actuator_controls_status_s>	_actuator_controls_status_pub{ORB_ID(actuator_controls_status_0)};
	uORB::Publication<actuator_torque_measured_s>	_actuator_torque_measured_pub{ORB_ID(actuator_torque_measured)};
	uORB::Publication<indi_rate_status_s>		_indi_rate_status_pub{ORB_ID(indi_rate_status)};
	uORB::Publication<vehicle_rates_setpoint_s>	_vehicle_rates_setpoint_pub{ORB_ID(vehicle_rates_setpoint)};
	uORB::Publication<vehicle_thrust_setpoint_s>	_vehicle_thrust_setpoint_pub{ORB_ID(vehicle_thrust_setpoint)};
	uORB::Publication<vehicle_torque_setpoint_s>	_vehicle_torque_setpoint_pub{ORB_ID(vehicle_torque_setpoint)};

	vehicle_control_mode_s	_vehicle_control_mode{};
	vehicle_status_s	_vehicle_status{};

	bool _landed{true};
	bool _maybe_landed{true};

	// last measured actuator torque (ESC rpm), all zero and invalid until one is computed
	actuator_torque_measured_s _torque_measured{};

	// previous torque setpoint publication and allocator feedback, for the INDI actuator model
	matrix::Vector3f _prev_torque_setpoint{};
	hrt_abstime _prev_torque_setpoint_time{0};
	matrix::Vector3f _unallocated_torque{};
	hrt_abstime _unallocated_torque_time{0};

	param_t _param_imu_gyro_cutoff{PARAM_INVALID};
	param_t _param_imu_dgyro_cutoff{PARAM_INVALID};

	hrt_abstime _last_run{0};

	perf_counter_t	_loop_perf;			/**< loop duration performance counter */

	// keep setpoint values between updates
	matrix::Vector3f _acro_rate_max;		/**< max attitude rates in acro mode */
	matrix::Vector3f _rates_setpoint{};
	matrix::Vector3f _thrust_setpoint{};

	float _energy_integration_time{0.0f};
	float _control_energy[4] {};

	DEFINE_PARAMETERS(
		(ParamFloat<px4::params::MC_ACRO_R_MAX>) _param_mc_acro_r_max,
		(ParamFloat<px4::params::MC_ACRO_P_MAX>) _param_mc_acro_p_max,
		(ParamFloat<px4::params::MC_ACRO_Y_MAX>) _param_mc_acro_y_max,
		(ParamFloat<px4::params::MC_ACRO_EXPO>) _param_mc_acro_expo,			/**< expo stick curve shape (roll & pitch) */
		(ParamFloat<px4::params::MC_ACRO_EXPO_Y>) _param_mc_acro_expo_y,				/**< expo stick curve shape (yaw) */
		(ParamFloat<px4::params::MC_ACRO_SUPEXPO>) _param_mc_acro_supexpo,		/**< superexpo stick curve shape (roll & pitch) */
		(ParamFloat<px4::params::MC_ACRO_SUPEXPOY>) _param_mc_acro_supexpoy,		/**< superexpo stick curve shape (yaw) */

		(ParamFloat<px4::params::MC_INDI_W_MAX>) _param_mc_indi_w_max,
		(ParamFloat<px4::params::MC_INDI_G1_R>) _param_mc_indi_g1_r,
		(ParamFloat<px4::params::MC_INDI_G1_P>) _param_mc_indi_g1_p,
		(ParamFloat<px4::params::MC_INDI_G1_Y>) _param_mc_indi_g1_y,
		(ParamFloat<px4::params::MC_INDI_G2_Y>) _param_mc_indi_g2_y,
		(ParamFloat<px4::params::MC_INDI_K_R>) _param_mc_indi_k_r,
		(ParamFloat<px4::params::MC_INDI_K_P>) _param_mc_indi_k_p,
		(ParamFloat<px4::params::MC_INDI_K_Y>) _param_mc_indi_k_y,
		(ParamFloat<px4::params::MC_INDI_ACT_TC>) _param_mc_indi_act_tc,
		(ParamInt<px4::params::MC_INDI_DELAY>) _param_mc_indi_delay,
		(ParamInt<px4::params::MC_INDI_ERPM_DLY>) _param_mc_indi_erpm_dly,
		(ParamFloat<px4::params::MC_INDI_ERPM_TO>) _param_mc_indi_erpm_to,
		(ParamFloat<px4::params::MC_INDI_DT_MAX>) _param_mc_indi_dt_max,
		(ParamFloat<px4::params::MC_INDI_YAW_CUT>) _param_mc_indi_yaw_cut
	)
};
