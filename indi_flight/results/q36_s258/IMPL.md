# INDI arming refusal on missing eRPM telemetry: implementation notes

Nothing is committed. Working tree only. No change outside `src/modules/mc_indi_rate_control/` and this folder
(`git diff main` on commander, mc_rate_control, mc_att_control, mc_pos_control, control_allocator and
`src/lib/control_allocation` is empty).

## Design
1. `IndiErpmArmingCheck::evaluate(measured, now, timeout_s, armed)` (new, pure, in the `IndiMeasuredTorque` library) returns
   `can_arm` plus a motor bit mask. It runs the existing `IndiMeasuredTorque::compute(now)` and applies the in-flight
   criteria unchanged: `Result.valid` (every motor online, has a value, plausible, not frozen, younger than
   `SAMPLE_MAX_AGE_US` = 20 ms) and `isSampleFresh(now, oldest sample, MC_INDI_ERPM_TO)`. No new parameter.
2. Not enforced when the measured torque is not in use (`MC_INDI_W_MAX` = 0 or no rotor geometry: `enabled()` false).
   Motor count is `IndiMeasuredTorque::numRotors()` (new getter), i.e. the CA_* geometry the module already uses.
3. While armed `evaluate` returns `can_arm = true` without computing anything.
4. `McIndiRateControl::updateArmingCheck()` (called once per gyro cycle) registers once with the commander
   (`register_arming_check = true` only, no mode, no executor, fixed `request_id`, `px4_ros2_api_version` = latest, name
   "INDI rpm telemetry"), keeps `arming_check_id`, and answers every `arming_check_request` with an `arming_check_reply`
   (same `request_id`, own `registration_id`, `can_arm_and_run` = verdict, no events in the reply).
5. On refusal a standalone event `mc_indi_rate_control_erpm_missing` (Error, argument: motor bit mask) is sent after the
   refusal lasted 2 s, then every 10 s while it lasts (same pattern as mc_nn_control). Registration is retried every 1 s
   while disarmed and not registered; it is never published while armed. Unregistered on module stop.

## Files changed
- `src/modules/mc_indi_rate_control/IndiErpmArmingCheck.hpp`, `.cpp` (new)
- `src/modules/mc_indi_rate_control/IndiErpmArmingCheckTest.cpp` (new, 4 tests)
- `src/modules/mc_indi_rate_control/IndiMeasuredTorque.hpp`, `.cpp`: `Result::motor_unusable_mask` (filled in the existing
  not-fresh branch, nothing else in `compute()` touched), `numRotors()` getter
- `src/modules/mc_indi_rate_control/McIndiRateControl.hpp`, `.cpp`: `updateArmingCheck()`, `unregisterArmingCheck()`,
  subscriptions/publications, one call after the `vehicle_control_mode` update, one call in the exit path
- `src/modules/mc_indi_rate_control/CMakeLists.txt`: new source in `IndiMeasuredTorque`, new gtest
- No yaml change (no parameter added).

## Commander behaviour (read from source, not changed)
- Handshake (`ModeManagement::checkNewRegistrations`): `register_mode` needs `register_arming_check`; a request with only
  `register_arming_check` creates a generic registration (`nav_mode_id` = -1, `ExternalChecks::addRegistration`). The reply
  (`register_ext_component_reply`) echoes `request_id` and `name`, carries `success` and `arming_check_id`; the match key
  is `request_id`. A request whose `request_id` is already registered is answered again with the same id (idempotent, so
  re-sending is safe, also after the module restarts). `name` is char[25] and is forced NUL-terminated by the commander.
  `px4_ros2_api_version` is not validated by the commander, it only echoes the latest one. The reply topic queue is 2 and
  is shared with other components, so the module filters on its own `request_id`. Up to 8 registrations
  (`MAX_NUM_REGISTRATIONS`); no free slot gives `success = false`.
- While armed, with `COM_MODE_ARM_CHK` = 0 (default), registration requests are rejected (`success = false`) and
  unregistrations are not processed. Hence the module never publishes a request while armed, and unregistration while armed
  does nothing (the commander drops the entry itself, below).
- Requests: `ExternalChecks::update()` publishes an `arming_check_request` every 300 ms (also while armed), only while at
  least one registration exists. Replies are matched on `registration_id` valid, `request_id` equal to the current one and
  reply age < 300 ms; the latest reply per registration is cached. `Commander::arm()` re-runs the checks on the cached
  replies (`update(false, true)`), so the arming decision uses a reply at most one request period (300 ms) old.
- Reply queue length assertion: `static_assert(arming_check_reply_s::ORB_QUEUE_LENGTH >= ExternalChecks::MAX_NUM_REGISTRATIONS)`
  (8 >= 8). One reply per request per component is published here, so the queue cannot overflow because of this module.
- Missing replies: no reply to a request within 50 ms counts as one miss; for a generic registration (`nav_mode_id` = -1)
  after more than 10 misses (first reply not yet received) or more than 3 misses (afterwards), i.e. about 1.2 s without
  answers, the registration is removed outright (`removeRegistration`, "No response from %i, removing"), not flagged
  unresponsive (that flag exists only for modes). A removed registration stops gating arming. The module then sees no
  request for 3 s while disarmed, forgets its id and registers again.
- Effect of a failing arming-only check: `can_arm_and_run = false` on a generic registration only clears the arming bits
  for all modes (`clearArmingBits(NavModes::All)`); it does not touch `can_run`, `mode_req_other` or any failsafe flag.
  `Commander` uses `canArm` for `pre_flight_checks_pass`, the arm command, auto-arm and LED/`ready_to_arm`
  (`ready_to_arm = pre_flight_checks_pass || isArmed()`); nothing reads it as a flight-time failsafe trigger. Even so, the
  module replies `true` while armed, so it cannot matter.
- Reply events: events in the reply must follow the arming-check event layout (modes, health component index, then the
  arguments) and the source-scanner for event metadata only knows `events::send` and `reporter.*` calls, so the reason is a
  standalone event (like mc_nn_control) and the reply carries `num_events = 0`. GCS therefore shows the denial through the
  generic "Arming denied: Resolve system health failures first" plus the module's own event.

## Tests (5 in total: 4 unit + 1 SITL)
Unit: `functional-IndiErpmArmingCheck` (x500 geometry, 4 motors). Break-check = temporary one-line mutation of
`IndiErpmArmingCheck.cpp`, build, run, restore (script `breakcheck.sh`, output `breakcheck.log`; restored file passes 4/4).

| Test | What it shows | Mutation | Result |
|---|---|---|---|
| AllMotorsFreshCanArm | 4 fresh samples: arming allowed, empty mask | `result.valid && fresh` -> `false && fresh` | FAILED (only this test) |
| MotorWithoutTelemetryRefuses | motor never reported, and motor reported then flagged offline: refused, mask = that motor | drop the `result.valid` term | FAILED (this test, and StaleSampleRefuses) |
| StaleSampleRefuses | one sample 50 ms old: refused, mask = that motor; samples 5 ms old with a 2 ms timeout: refused, mask = all motors | drop the `isSampleFresh` term | FAILED (only this test) |
| NeverRefusesWhileArmed | no telemetry and stale telemetry while armed: arming check true | drop `armed ||` | FAILED (only this test) |

The frozen-value case is not a separate test: the frozen detection only runs while armed (`setArmed(false)` clears it,
`compute` ignores it when disarmed), and while armed the check always allows. A stuck rpm value therefore cannot refuse arming
with the existing criteria; the frozen path is covered by the existing `IndiFrozenRpmTest` tests.

SITL (1): hover scenario with the INDI defaults, separate build directory `build/q36_sitl` (`px4_sitl_default` config;
`build/px4_sitl_default` untouched). Params: `sitl_params.params` = `bench/params/quad5in_indi_defaults.params` minus
`MC_INDI_DT_MAX` (not a parameter of this tree; the run aborted on it). `MC_INDI_EN 1` is what starts the module here
(`rc.mc_apps`); the harness maps it to `MC_RATE_CTL_TYPE 1`. Result (`sitl_hover/px4.log`, `metrics.json` status ok):
`mc_indi_rate_control: arming check registered, id 0` at boot, then `Ready for takeoff!`, `Armed by external command`,
takeoff, landing, `Disarmed by landing`; no "Arming denied", no `rpm telemetry` event. So with telemetry present the
vehicle arms and flies. (`flight.ulg` of that run was deleted, 131 MB.) The refusal path in SITL was not run (see below).

## Commands
Unit tests (existing configured build `build/px4_sitl_test`, filter in its cache includes `Indi`; ninja is used directly so
the Makefile's NuttX-target stamp is not touched):
```
indi_project/docker/run.sh -n q36ut -t 1500 'ninja -C build/px4_sitl_test test_results'
```
Single binary: `build/px4_sitl_test/functional-IndiErpmArmingCheck`. Break-checks:
```
indi_project/docker/run.sh -n q36bc -t 1500 'indi_flight/results/q36_s258/breakcheck.sh'
```
SITL build and flight:
```
indi_project/docker/run.sh -n q36sitl -t 5400 'cmake -S . -B build/q36_sitl -GNinja -DCONFIG=px4_sitl_default -DCMAKE_BUILD_TYPE=RelWithDebInfo && ninja -C build/q36_sitl px4'
indi_project/docker/run.sh -n q36fly -t 1000 -e PX4_INDI_BUILD=$PWD/build/q36_sitl -- python3 indi_flight/bench/run_scenario.py --scenario hover --controller indi --seed 1 --speed 3 --params indi_flight/results/q36_s258/sitl_params.params --out indi_flight/results/q36_s258/sitl_hover
```
Format: `Tools/astyle/check_code_style.sh <file>` on the 7 changed/new C++ files and `git diff --check`, all clean
(`format_check.log`). Whole-repo `make format` was not run.

## Unverified / limits
- Refusal in a running SITL or on hardware was not exercised (no test budget left; unit tests cover the decision, the SITL
  flight covers registration, reply and the allow path). Registration, reply wiring and the commander side were checked by
  reading source plus the registration line in the log, not by logging the reply stream.
- Arming before registration completes is not blocked: the module registers on its first cycles (about boot), until then
  and while the commander has dropped the registration (about 1.2 s of missed replies) the check does not gate.
- Real ESC hardware: whether telemetry (DShot eRPM) is reported while disarmed and motors are stopped was not verified. If a
  driver reports nothing at standstill, arming would be refused on that vehicle; the 20 ms sample age limit is applied to the
  disarmed samples as well.
- Frozen rpm cannot refuse arming (see above). `MC_INDI_W_MAX` = 0 disables the check by design.
- The event is not an arming-check-group event (no modes/health arguments), see commander findings.
- `COM_MODE_ARM_CHK` = 1 would let registrations through while armed; the module still never publishes one while armed.
- Existing reply `arming_check_reply` while armed is published every 300 ms (one small message); the per-cycle cost is one
  `updated()` poll and one registration-reply poll.
