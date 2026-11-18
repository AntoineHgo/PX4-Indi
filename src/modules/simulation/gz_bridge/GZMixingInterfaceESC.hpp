/****************************************************************************
 *
 *   Copyright (c) 2023 PX4 Development Team. All rights reserved.
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

#include <lib/failure_injection/FailureInjection.hpp>
#include <lib/mathlib/mathlib.h>
#include <lib/mixer_module/mixer_module.hpp>

#include <gz/msgs.hh>
#include <gz/transport.hh>

#include <uORB/PublicationMulti.hpp>
#include <uORB/topics/esc_status.h>


// GZBridge mixing class for ESCs.
// It is separate from GZBridge to have separate WorkItems and therefore allowing independent scheduling
// All work items are expected to run on the same work queue.
class GZMixingInterfaceESC : public OutputModuleInterface
{
public:
	static constexpr int MAX_ACTUATORS = MixingOutput::MAX_ACTUATORS;

	GZMixingInterfaceESC(gz::transport::Node &node) :
		OutputModuleInterface(MODULE_NAME "-actuators-esc", px4::wq_configurations::rate_ctrl),
		_node(node)
	{
		int32_t signed_mask = 0;
		param_get(param_find("SIM_GZ_EC_SIGNED"), &signed_mask);
		_signed_mask = static_cast<uint32_t>(signed_mask);

		param_get(param_find("SIM_GZ_ESC_FB"), &_esc_feedback);
		param_get(param_find("SIM_GZ_ERPM_POL"), &_erpm_poles);
		param_get(param_find("SIM_GZ_ERPM_DRP"), &_erpm_drop_probability);
		param_get(param_find("SIM_GZ_ERPM_LAT"), &_erpm_latency);
		int32_t seed = 0;
		param_get(param_find("SIM_GZ_SEED"), &seed);

		if (seed != 0) { // splitmix32 of the seed, never 0 for xorshift
			uint32_t z = static_cast<uint32_t>(seed) + 0x9e3779b9u;
			z = (z ^ (z >> 16)) * 0x85ebca6bu;
			z = (z ^ (z >> 13)) * 0xc2b2ae35u;
			z ^= z >> 16;
			_random_state = (z != 0) ? z : 0x12345678u;
		}

		int32_t dly_act_ms = 0;
		param_get(param_find("SIM_GZ_DLY_ACT"), &dly_act_ms);
		_act_delay_us = (uint32_t)math::constrain(dly_act_ms, (int32_t)0, (int32_t)10) * 1000u;

		_erpm_latency = math::constrain(_erpm_latency, (int32_t)0, (int32_t)ERPM_DELAY_LEN - 1);
		_erpm_poles = math::max(_erpm_poles, (int32_t)2);
		updateParams();
	}

	void updateParams() override
	{
		OutputModuleInterface::updateParams();

		// Runtime plant changes for the benchmark, read on every parameter update
		int32_t loss_mask = 0;
		param_get(param_find("SIM_GZ_ERPM_LOSS"), &loss_mask);
		_erpm_loss_mask = static_cast<uint32_t>(loss_mask);

		float thrust_scale = 1.f;
		param_get(param_find("SIM_GZ_THR_SC"), &thrust_scale);
		_motor_speed_scale = sqrtf(math::constrain(thrust_scale, 0.f, 1.f)); // thrust ~ rotor speed squared
	}

	bool updateOutputs(float outputs[MAX_ACTUATORS], unsigned num_outputs, unsigned num_control_groups_updated) override;

	MixingOutput &mixingOutput() { return _mixing_output; }

	bool init(const std::string &world_name, const std::string &model_name);

	void stop()
	{
		_mixing_output.unregister();
		ScheduleClear();
	}

private:
	friend class GZBridge;

	void Run() override;

	bool publishDelayed(const gz::msgs::Actuators &msg);

	void motorSpeedCallback(const gz::msgs::Actuators &actuators);
	void jointStateCallback(const gz::msgs::Model &model);

	// Bidirectional DShot eRPM telemetry as decoded by the PX4 DShot driver, from a true rotor speed [rpm]
	int32_t erpmTelemetry(float rotor_rpm) const;
	float uniformRandom();

	// MulticopterMotorModel spins the rotor joint at the motor speed divided by rotorVelocitySlowdownSim
	// (10 in all PX4 gz multicopter models) and computes thrust from joint velocity times that factor.
	static constexpr float ROTOR_VELOCITY_SLOWDOWN_SIM = 10.f;

	uint32_t _signed_mask{0};

	int32_t _esc_feedback{0}; // SIM_GZ_ESC_FB: 0 = echo motor command, 1 = rotor joint velocity, 2 = eRPM model
	float _rotor_rpm[esc_status_s::CONNECTED_ESC_MAX] {};
	bool _rotor_rpm_valid{false};

	int32_t _erpm_poles{14};
	float _erpm_drop_probability{0.f};
	uint32_t _erpm_loss_mask{0}; // SIM_GZ_ERPM_LOSS: motors whose every eRPM frame fails
	float _motor_speed_scale{1.f}; // sqrt(SIM_GZ_THR_SC), applied to motor outputs
	float _erpm_reply_rpm[esc_status_s::CONNECTED_ESC_MAX] {}; // speed sampled at the previous frame
	static constexpr int ERPM_DELAY_LEN = 9; // SIM_GZ_ERPM_LAT up to 8 frames
	int32_t _erpm_latency{0};
	float _erpm_delay[ERPM_DELAY_LEN][esc_status_s::CONNECTED_ESC_MAX] {};
	int _erpm_delay_idx{0};
	int32_t _erpm_last_rpm[esc_status_s::CONNECTED_ESC_MAX] {}; // last decoded value, held on a dropped frame
	uint32_t _erpm_errors[esc_status_s::CONNECTED_ESC_MAX] {};
	uint32_t _random_state{0x12345678u}; // SIM_GZ_SEED 0: fixed, dropouts repeatable run to run

	// SIM_GZ_DLY_ACT delay line (hook A1). Only touched from updateOutputs(), which runs inside Run() under
	// _node_mutex. 0 = bypassed. Size: 10 ms at up to 3.2 kHz output calls (PX4 rate loop at most 800 Hz).
	static constexpr int ACT_DELAY_LEN = 32;
	struct ActDelayEntry {
		uint64_t t_in{0};
		unsigned count{0};
		double vel[MAX_ACTUATORS] {};
	};
	uint32_t _act_delay_us{0};
	ActDelayEntry _act_delay[ACT_DELAY_LEN] {};
	int _act_delay_head{0}; // oldest entry
	int _act_delay_n{0};    // entries stored
	uint32_t _act_dropped{0}; // due entries skipped (latest wins)
	uint32_t _act_overflow{0};
	bool _act_first_logged{false};

	gz::transport::Node &_node;
	pthread_mutex_t _node_mutex;

	MixingOutput _mixing_output{"SIM_GZ_EC", MAX_ACTUATORS, *this, MixingOutput::SchedulingPolicy::Auto, false, false};

	gz::transport::Node::Publisher _actuators_pub;

	uORB::Publication<esc_status_s> _esc_status_pub{ORB_ID(esc_status)};
	failure_injection::Config _failure_config;

};
