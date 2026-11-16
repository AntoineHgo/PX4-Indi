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

#include "SimScenarioPlayer.hpp"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <px4_platform_common/getopt.h>
#include <uORB/topics/sensor_gyro.h>

ModuleBase::Descriptor SimScenarioPlayer::desc{task_spawn, custom_command, print_usage};

SimScenarioPlayer::SimScenarioPlayer(const char *path) :
	WorkItem(MODULE_NAME, px4::wq_configurations::hp_default)
{
	_rows.reserve(256);

	if (!load(path)) {
		_rows.clear();
	}
}

SimScenarioPlayer::~SimScenarioPlayer()
{
	_gyro_sub.unregisterCallback();
}

bool SimScenarioPlayer::load(const char *path)
{
	FILE *fp = fopen(path, "r");

	if (!fp) {
		PX4_ERR("cannot open %s", path);
		return false;
	}

	char line[256];
	int lineno = 0;
	bool ok = true;
	uint64_t t_prev = 0;
	bool after_anchor = false;

	while (ok && fgets(line, sizeof(line), fp)) {
		lineno++;
		char *hash = strchr(line, '#');

		if (hash) {
			*hash = '\0';
		}

		char *save = nullptr;
		char *tok = strtok_r(line, " \t\r\n", &save);

		if (!tok) {
			continue;
		}

		Row row;
		char *end = nullptr;
		row.t_us = strtoull(tok, &end, 10);
		row.rel = after_anchor;

		if (*end != '\0') {
			PX4_ERR("%s:%d bad time '%s'", path, lineno, tok);
			ok = false;
			break;
		}

		if (row.t_us < t_prev) {
			PX4_ERR("%s:%d rows not sorted by time", path, lineno);
			ok = false;
			break;
		}

		t_prev = row.t_us;
		tok = strtok_r(nullptr, " \t\r\n", &save);

		if (!tok) {
			PX4_ERR("%s:%d missing kind", path, lineno);
			ok = false;
			break;
		}

		if (strcmp(tok, "arm") == 0) {
			row.kind = sim_schedule_applied_s::KIND_ARM;

		} else if (strcmp(tok, "disarm") == 0) {
			row.kind = sim_schedule_applied_s::KIND_DISARM;

		} else if (strcmp(tok, "mode_offboard") == 0) {
			row.kind = sim_schedule_applied_s::KIND_MODE_OFFBOARD;

		} else if (strcmp(tok, "sp") == 0) {
			row.kind = sim_schedule_applied_s::KIND_SP;

			for (int i = 0; i < 4; i++) {
				tok = strtok_r(nullptr, " \t\r\n", &save);

				if (!tok) {
					PX4_ERR("%s:%d sp needs x y z yaw", path, lineno);
					ok = false;
					break;
				}

				row.f[i] = strtof(tok, nullptr);
			}

		} else if (strcmp(tok, "sp_hold") == 0) {
			row.kind = sim_schedule_applied_s::KIND_SP_HOLD;

			for (int i = 0; i < 3; i++) { // optional offsets dx dy dz, default 0
				tok = strtok_r(nullptr, " \t\r\n", &save);
				row.f[i] = tok ? strtof(tok, nullptr) : 0.f;

				if (!tok) {
					for (int j = i + 1; j < 3; j++) {
						row.f[j] = 0.f;
					}

					break;
				}
			}

		} else if (strcmp(tok, "takeoff") == 0) {
			row.kind = sim_schedule_applied_s::KIND_TAKEOFF;
			tok = strtok_r(nullptr, " \t\r\n", &save);
			row.f[0] = tok ? strtof(tok, nullptr) : NAN; // param7 (altitude as the command defines it)

		} else if (strcmp(tok, "land") == 0) {
			row.kind = sim_schedule_applied_s::KIND_LAND;

		} else if (strcmp(tok, "anchor") == 0) {
			row.kind = sim_schedule_applied_s::KIND_ANCHOR;
			tok = strtok_r(nullptr, " \t\r\n", &save);

			if (!tok || strncmp(tok, "nav_state=", 10) != 0) {
				PX4_ERR("%s:%d anchor needs nav_state=<N>", path, lineno);
				ok = false;
				break;
			}

			row.f[0] = strtof(tok + 10, nullptr);
			after_anchor = true;
			t_prev = row.t_us; // checked above; the order restarts at 0 for the rows after the anchor
			_rows.push_back(row);
			t_prev = 0;
			continue;

		} else {
			PX4_ERR("%s:%d unknown kind '%s'", path, lineno, tok);
			ok = false;
		}

		if (ok) {
			_rows.push_back(row);
		}
	}

	fclose(fp);

	if (ok) {
		PX4_INFO("loaded %u rows from %s", (unsigned)_rows.size(), path);
	}

	return ok;
}

bool SimScenarioPlayer::init()
{
	if (_rows.empty()) {
		return false;
	}

	return _gyro_sub.registerCallback();
}

void SimScenarioPlayer::publish_command(uint32_t command, float param1, float param2, hrt_abstime now, float param3,
					float param4, float param5, float param6, float param7)
{
	// as MavlinkReceiver::handle_message_command_long for a COMMAND_LONG of the Python runner (sysid 255, comp 0)
	vehicle_status_s status{};
	_vehicle_status_sub.copy(&status);

	vehicle_command_s vcmd{};
	vcmd.timestamp = now;
	vcmd.param1 = param1;
	vcmd.param2 = param2;
	vcmd.param3 = param3;
	vcmd.param4 = param4;
	vcmd.param5 = param5;
	vcmd.param6 = param6;
	vcmd.param7 = param7;
	vcmd.command = command;
	vcmd.target_system = status.system_id ? status.system_id : 1;
	vcmd.target_component = 1;
	vcmd.source_system = 255;
	vcmd.source_component = 0;
	vcmd.confirmation = 0;
	vcmd.from_external = true;
	_cmd_pub.publish(vcmd);
}

void SimScenarioPlayer::publish_setpoint(hrt_abstime now)
{
	// as MavlinkReceiver::handle_message_set_position_target_local_ned (position + yaw, rest ignored)
	trajectory_setpoint_s setpoint{};
	setpoint.position[0] = _sp[0];
	setpoint.position[1] = _sp[1];
	setpoint.position[2] = _sp[2];

	for (int i = 0; i < 3; i++) {
		setpoint.velocity[i] = NAN;
		setpoint.acceleration[i] = NAN;
	}

	setpoint.yaw = _sp[3];
	setpoint.yawspeed = NAN;

	offboard_control_mode_s ocm{};
	ocm.position = PX4_ISFINITE(_sp[0]) || PX4_ISFINITE(_sp[1]) || PX4_ISFINITE(_sp[2]);
	ocm.velocity = false;
	ocm.acceleration = false;
	ocm.attitude = PX4_ISFINITE(_sp[3]);
	ocm.body_rate = false;

	if (!ocm.position) {
		return;
	}

	ocm.timestamp = now;
	_offboard_control_mode_pub.publish(ocm);

	vehicle_status_s status{};
	_vehicle_status_sub.copy(&status);

	if (status.accepts_offboard_setpoints) {
		setpoint.timestamp = hrt_absolute_time();
		_trajectory_setpoint_pub.publish(setpoint);
	}
}

void SimScenarioPlayer::apply(const Row &row, uint32_t index, hrt_abstime now, hrt_abstime t_sched)
{
	sim_schedule_applied_s applied{};
	applied.sp[0] = applied.sp[1] = applied.sp[2] = applied.sp[3] = NAN;

	switch (row.kind) {
	case sim_schedule_applied_s::KIND_ARM:
		publish_command(vehicle_command_s::VEHICLE_CMD_COMPONENT_ARM_DISARM, 1.f, 0.f, now);
		break;

	case sim_schedule_applied_s::KIND_DISARM:
		publish_command(vehicle_command_s::VEHICLE_CMD_COMPONENT_ARM_DISARM, 0.f, 0.f, now);
		break;

	case sim_schedule_applied_s::KIND_MODE_OFFBOARD:
		// DO_SET_MODE: param1 = 1 (custom mode), param2 = PX4_CUSTOM_MAIN_MODE_OFFBOARD (6), param3 = 0
		publish_command(vehicle_command_s::VEHICLE_CMD_DO_SET_MODE, 1.f, 6.f, now);
		break;

	case sim_schedule_applied_s::KIND_SP:
		memcpy(_sp, row.f, sizeof(_sp));
		_sp_held = true;
		_next_sp_us = now; // publish at once, then every SETPOINT_PERIOD_US
		memcpy(applied.sp, _sp, sizeof(_sp));
		break;

	case sim_schedule_applied_s::KIND_SP_HOLD: {
			vehicle_local_position_s lpos{};
			_local_pos_sub.copy(&lpos);

			if (lpos.xy_valid && lpos.z_valid && PX4_ISFINITE(lpos.heading)) {
				_sp[0] = lpos.x + row.f[0];
				_sp[1] = lpos.y + row.f[1];
				_sp[2] = lpos.z + row.f[2];
				_sp[3] = lpos.heading;
				_sp_held = true;
				_next_sp_us = now;
				memcpy(applied.sp, _sp, sizeof(_sp));

			} else {
				PX4_ERR("sp_hold row %u: local position invalid, setpoint unchanged", (unsigned)index);
			}

			break;
		}

	case sim_schedule_applied_s::KIND_TAKEOFF:
		// as the runner's MAV_CMD_NAV_TAKEOFF: pitch, yaw, lat, lon NAN (take off here), param7 = altitude
		publish_command(vehicle_command_s::VEHICLE_CMD_NAV_TAKEOFF, NAN, 0.f, now, 0.f, NAN, NAN, NAN, row.f[0]);
		break;

	case sim_schedule_applied_s::KIND_LAND:
		// as the runner's MAV_CMD_NAV_LAND: abort alt 0, land mode 0, yaw/lat/lon NAN, altitude 0
		publish_command(vehicle_command_s::VEHICLE_CMD_NAV_LAND, 0.f, 0.f, now, 0.f, NAN, NAN, NAN, 0.f);
		break;

	case sim_schedule_applied_s::KIND_ANCHOR: // published by Run() when the anchor is reached
		break;
	}

	applied.timestamp = hrt_absolute_time();
	applied.t_sched_us = t_sched;
	applied.anchor_us = _anchor_us;
	applied.row_index = index;
	applied.kind = row.kind;
	_applied_pub.publish(applied);
}

void SimScenarioPlayer::Run()
{
	if (should_exit()) {
		_gyro_sub.unregisterCallback();
		exit_and_cleanup(desc);
		return;
	}

	const hrt_abstime now = hrt_absolute_time();

	while (_next_row < _rows.size()) {
		const Row &row = _rows[_next_row];

		if (_anchor_wait) {
			vehicle_status_s status{};
			_vehicle_status_sub.copy(&status);

			if (status.nav_state != _anchor_nav_state || status.arming_state != vehicle_status_s::ARMING_STATE_ARMED) {
				break;
			}

			// the anchor is the instant of the vehicle_status message that carries the state (never before activation)
			_anchor_us = status.timestamp > _anchor_start_us ? status.timestamp : _anchor_start_us;
			_anchor_wait = false;
			apply(row, _next_row, now, row.t_us + (row.rel ? _prev_anchor_us : 0));
			_next_row++;
			continue;
		}

		const hrt_abstime t_sched = row.t_us + (row.rel ? _anchor_us : 0);

		if (t_sched > now) {
			break;
		}

		if (row.kind == sim_schedule_applied_s::KIND_ANCHOR) { // activate: suspend until the state is observed
			_anchor_wait = true;
			_anchor_nav_state = (uint8_t)row.f[0];
			_anchor_start_us = now;
			_prev_anchor_us = _anchor_us;
			continue;
		}

		apply(row, _next_row, now, t_sched);
		_next_row++;
	}

	if (_sp_held && now >= _next_sp_us) {
		publish_setpoint(now);

		do {
			_next_sp_us += SETPOINT_PERIOD_US;
		} while (_next_sp_us <= now);
	}
}

int SimScenarioPlayer::print_status()
{
	PX4_INFO("rows applied %u of %u, setpoint held %d", (unsigned)_next_row, (unsigned)_rows.size(), (int)_sp_held);
	return PX4_OK;
}

int SimScenarioPlayer::task_spawn(int argc, char *argv[])
{
	const char *path = nullptr;
	int ch;
	int myoptind = 1;
	const char *myoptarg = nullptr;

	while ((ch = px4_getopt(argc, argv, "f:", &myoptind, &myoptarg)) != EOF) {
		if (ch == 'f') {
			path = myoptarg;

		} else {
			return print_usage("unknown option");
		}
	}

	if (!path) {
		return print_usage("missing -f <schedule file>");
	}

	SimScenarioPlayer *instance = new SimScenarioPlayer(path);

	if (instance) {
		desc.object.store(instance);
		desc.task_id = task_id_is_work_queue;

		if (instance->init()) {
			return PX4_OK;
		}

	} else {
		PX4_ERR("alloc failed");
	}

	delete instance;
	desc.object.store(nullptr);
	desc.task_id = -1;

	return PX4_ERROR;
}

int SimScenarioPlayer::custom_command(int argc, char *argv[])
{
	return print_usage("unknown command");
}

int SimScenarioPlayer::print_usage(const char *reason)
{
	if (reason) {
		PX4_WARN("%s\n", reason);
	}

	PRINT_MODULE_DESCRIPTION(
		R"DESCR_STR(
### Description
Simulation only. Plays a scenario schedule file in simulation time on uORB: arm/disarm and mode commands
(vehicle_command, as MavlinkReceiver publishes them) and offboard setpoints (offboard_control_mode and
trajectory_setpoint at 50 Hz). Each applied row is published on sim_schedule_applied.

Rows: `t_sim_us arm|disarm|mode_offboard`, `t_sim_us sp x y z yaw`.
)DESCR_STR");

	PRINT_MODULE_USAGE_NAME("sim_scenario_player", "system");
	PRINT_MODULE_USAGE_COMMAND("start");
	PRINT_MODULE_USAGE_PARAM_STRING('f', nullptr, "<file>", "Schedule file", false);
	PRINT_MODULE_USAGE_DEFAULT_COMMANDS();

	return 0;
}

extern "C" __EXPORT int sim_scenario_player_main(int argc, char *argv[])
{
	return ModuleBase::main(SimScenarioPlayer::desc, argc, argv);
}
