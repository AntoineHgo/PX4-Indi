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

#include <stdint.h>
#include <vector>

#include <drivers/drv_hrt.h>
#include <px4_platform_common/defines.h>
#include <px4_platform_common/module.h>
#include <px4_platform_common/px4_work_queue/WorkItem.hpp>
#include <uORB/Publication.hpp>
#include <uORB/Subscription.hpp>
#include <uORB/SubscriptionCallback.hpp>
#include <uORB/topics/offboard_control_mode.h>
#include <uORB/topics/sensor_gyro.h>
#include <uORB/topics/sim_schedule_applied.h>
#include <uORB/topics/trajectory_setpoint.h>
#include <uORB/topics/vehicle_command.h>
#include <uORB/topics/vehicle_status.h>

using namespace time_literals;

/**
 * SITL only. Plays a schedule file in simulation time (hrt = gz clock) on the sensor_gyro callback.
 *
 * File format, one row per line, '#' starts a comment, times in microseconds of hrt_absolute_time():
 *   t_sim_us arm
 *   t_sim_us disarm
 *   t_sim_us mode_offboard
 *   t_sim_us sp x y z yaw          NED position [m] and yaw [rad]; nan allowed per field
 * Rows must be sorted by time. Further kinds (manual_control, param steps, injector triggers) are added as new
 * keywords with their own field lists; an unknown kind makes the start fail.
 */
class SimScenarioPlayer : public ModuleBase, public px4::WorkItem
{
public:
	static Descriptor desc;

	SimScenarioPlayer(const char *path);
	~SimScenarioPlayer() override;

	static int task_spawn(int argc, char *argv[]);
	static int custom_command(int argc, char *argv[]);
	static int print_usage(const char *reason = nullptr);

	bool init();
	int print_status() override;

private:
	struct Row {
		uint64_t t_us{0};
		uint8_t kind{0};
		float f[4] {NAN, NAN, NAN, NAN};
	};

	static constexpr uint64_t SETPOINT_PERIOD_US = 20_ms; // 50 Hz offboard stream in simulation time

	void Run() override;
	bool load(const char *path);
	void apply(const Row &row, uint32_t index, hrt_abstime now);
	void publish_command(uint32_t command, float param1, float param2, hrt_abstime now);
	void publish_setpoint(hrt_abstime now);

	uORB::SubscriptionCallbackWorkItem _gyro_sub{this, ORB_ID(sensor_gyro)};
	uORB::Subscription _vehicle_status_sub{ORB_ID(vehicle_status)};

	uORB::Publication<vehicle_command_s> _cmd_pub{ORB_ID(vehicle_command)};
	uORB::Publication<offboard_control_mode_s> _offboard_control_mode_pub{ORB_ID(offboard_control_mode)};
	uORB::Publication<trajectory_setpoint_s> _trajectory_setpoint_pub{ORB_ID(trajectory_setpoint)};
	uORB::Publication<sim_schedule_applied_s> _applied_pub{ORB_ID(sim_schedule_applied)};

	std::vector<Row> _rows;
	uint32_t _next_row{0};

	bool _sp_held{false};
	float _sp[4] {NAN, NAN, NAN, NAN}; // x y z yaw
	hrt_abstime _next_sp_us{0};
};
