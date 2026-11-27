# Review of "refuse arming when the rpm path is off" (reading only, no builds, no source edits)

Scope: `git diff -- src/modules/mc_indi_rate_control` against the Q37 specification, plus the test 6 unit test and the test 7 SITL evidence in this directory.

Verdict: no BLOCKER. The behaviour matches the specification. 2 MAJOR (both test coverage) and 5 MINOR remain.

## 1. Logic (IndiErpmArmingCheck::evaluate, McIndiRateControl::updateArmingCheck)

Correct against the spec:
- `IndiErpmArmingCheck.cpp:45-52`: armed returns the default verdict (can_arm true). Disarmed with `!enabled()` returns can_arm false and not_configured true. Otherwise the old rpm logic is unchanged (`:54-67` is byte-identical to before).
- Registration when disabled: `updateArmingCheck()` is called unconditionally from the gyro callback (`McIndiRateControl.cpp:436`). It has no `enabled()` gate, and the registration, retry and request-timeout code is untouched. The unconditional call is what makes the check register with `W_MAX = 0`.
- Runtime parameter change: `parameters_updated()` (`:142`) calls `setRotorSpeedMax(W_MAX)` and `updateMeasuredTorqueEffectiveness()` on every `parameter_update`. `enabled()` is `_omega_max > 0 && _num_rotors > 0` (`IndiMeasuredTorque.hpp:109`), so it follows W_MAX to 0 and back. `evaluate` reads it fresh on every request, so the verdict flips at the next commander request (about 300 ms) with no latch. `_erpm_refused_since` is reset when can_arm becomes true (`:278`).
- Re-enabling at runtime: `updateMeasuredTorque()` returns early while disabled, so no samples are collected then. After W_MAX is set again the verdict is "refused, missing rpm" for a few ms, then "can arm". This is correct.
- Armed path: `evaluate` returns early, so there is no in-flight effect. W_MAX changed to 0 while armed gives can_arm true. Matches the spec.
- motor_mask on the new path is 0 (default). The event takes the not_configured branch (`:287`) and never reads the mask. The commander reply does not carry a mask either. No bug.
- Event pacing: it shares `_erpm_refused_since`, `_last_erpm_event`, EVENT_DELAY 2 s and EVENT_INTERVAL 10 s with the old event. Switching between the two reasons is harmless.
- `events::send(id, levels, message)` without arguments is valid (`platforms/common/include/px4_platform_common/events.h:131`). The `<param>` tag in an event description has upstream precedent (`navigator_main.cpp:1168`). `CA_ROTOR0_PX` exists (`src/modules/control_allocator/module.yaml:139`).

Findings:
- MINOR `McIndiRateControl.hpp:122-123`: the doc comment still says "arming is refused while a motor has no fresh rpm telemetry". Fix: add "or while the measured torque is not configured (MC_INDI_W_MAX or rotor geometry)".
- MINOR `McIndiRateControl.cpp:159` and `mc_indi_rate_control_params.yaml:165-168`: stale wording. The `:159` comment "no valid rotor geometry: no measured torque, INDI uses its actuator model" is now followed by an arming refusal. The ERPM_TO text "Only used when MC_INDI_W_MAX is set" is acceptable, but it implies that W_MAX = 0 is a supported mode. Fix: change the `:159` comment to "no valid rotor geometry: no measured torque, arming is refused". Optionally reword the yaml, for example "W_MAX must be set".
- MINOR `McIndiRateControl.cpp:286`: the not-configured event waits 2 s (EVENT_DELAY) after the first refusal. The delay exists for telemetry start-up and does not apply to a static misconfiguration. An operator who presses arm in the first 2 s sees only the generic "Resolve system health failures first". Fix: skip the delay when `verdict.not_configured` (optional, cosmetic).
- MINOR (docs, outside the diff) `docs/en/config_mc/indi_control.md:108` and `:172`: they still say W_MAX 0 "disables the measured torque, the controller then uses its actuator model". The documentation work is already listed in STATE.md as the next step. Fix: update both before commit, or confirm they are in the pending docs diff.

## 2. Test 6 `NotConfiguredRefusesWhileDisarmed` (IndiErpmArmingCheckTest.cpp:156-179)

It asserts the behaviour and would fail if the behaviour broke. The assertions are real:
- Case W_MAX = 0 with fresh telemetry: can_arm false, not_configured true, and armed gives can_arm true.
- Case no geometry: the same three assertions.
- Recovery: can_arm true and not_configured false.

`breakcheck.log` confirms it. Mutation e (`if (!measured.enabled())` replaced by `if (false)`) fails test 6 only. Mutation d (armed branch disabled) fails test 6 and NeverRefusesWhileArmed. Mutations a, b and c fail the old tests as before. The restored build passes 5 of 5.

Findings:
- MINOR `IndiErpmArmingCheckTest.cpp:162-166`: the test does not assert `motor_mask == 0` on the new path. A mutant that sets a mask on this path would survive, but it would be harmless. Fix: add `EXPECT_EQ(verdict.motor_mask, 0)`.
- MINOR: the test never sets `not_configured` true while the rpm path itself refuses. That combination is unreachable by construction (the early return), so it is fine.

## 3. Test 7 `arm_refusal_flight.py` and its result

`sitl_refusal/arm_refusal.json` has pass true. Attempts 1-8 were refused (4 with SIM_GZ_ERPM_LOSS = 15, 4 with `failure esc off`) and attempt 9 was accepted after `failure esc ok`. The script also raises `RunError` if any early attempt is accepted. The flight then continued through takeoff and hover (`sitl_fly2.log` shows TEST7 PASS). `sitl_fly1.log` is an earlier climb-timing failure, fixed by `T_ARM_S`.

Attribution to this module is sound, but not from `px4.log`:
- `px4.log` shows only the generic "Arming denied: Resolve system health failures first" (x8), which any commander check could produce.
- The attribution comes from three other pieces of evidence.
  - The ulog `arming_check_reply` stream of registration id 0 flips to false at 22.6 s and back to true at 34.38 s. That brackets exactly the refused attempts (22.74 to 33.3 s) and the accepted attempt (34.81 s).
  - The mutant run (`breakcheck_sitl.log`) has the module always reply true. Arming is then accepted at attempt 1 while the telemetry is stale. That shows no other commander check blocked arming in that state, so the refusal in the real run comes from this module.
  - A standalone event with arg0 = 15 (mask of all 4 motors) appears at 24.8 s.

Findings:
- MAJOR `arm_refusal_flight.py` / `IMPL.md:78`: the new behaviour is not covered in SITL at all. The flight uses W_MAX = 2700, so only the old rpm-missing path runs. Nothing exercises registration with W_MAX = 0, the can_arm false reply, or the new event. Registration while disabled is an explicit spec item. Fix: add a short second scenario with `MC_INDI_W_MAX 0` that asserts `arming_check_reply` false, the arm refusal and the new event; then set W_MAX to 2700 at runtime and assert acceptance. This also covers the runtime parameter change.
- MAJOR `IMPL.md:78`: the event id 0x1a56f1f is identified only "by its argument and timing"; the hash was not computed and the id is not asserted in the script. Fix: compute the id of `mc_indi_rate_control_erpm_missing` (and of the new `mc_indi_rate_control_rpm_not_configured`) with the events tooling, or take it from `all_events.json`, and assert it in `ulog_summary`/`verdict`. As it stands, the event part of test 7 is anecdotal.
- MINOR `arm_refusal_flight.py:80-84`: the `verdict()` pass condition ignores `arming_check_reply`. It checks only attempts and the "Armed by" line. Fix: require `reply_changes_t_reg_can_arm` to contain a false that precedes the accepted attempt and a true after it. This makes the attribution part of PASS.

## 4. Upstream style

- No project ids (D-, Q37, S259, gate, owner, indi_flight) appear in the source or yaml diff. `git grep` on `IndiErpmArmingCheck.*`, `IndiErpmArmingCheckTest.cpp`, `McIndiRateControl.cpp` and the yaml found none.
- Comments are short. The event naming follows the `module_reason` pattern (`mc_indi_rate_control_rpm_not_configured`).
- The new `not_configured` struct field has a doc comment that is slightly long (one line, 130 columns). MINOR `IndiErpmArmingCheck.hpp:53`: wrap it to under 120 columns, or run `make format` to confirm. `format_check.log` is empty, so the run produced no output and I could not tell pass from fail; check the exit status.
- yaml text accuracy: W_MAX "Must be set: with 0, INDI refuses to arm." is accurate. The module description (`McIndiRateControl.cpp:654-656`) is accurate.

## 5. Stock modules zero diff

`git diff main --stat -- src/modules/commander src/modules/mc_rate_control src/modules/mc_att_control src/modules/mc_pos_control src/modules/control_allocator src/lib/control_allocation` is empty (zero diff).

## Disposition (orchestrator, S259)
- MAJOR SITL W_MAX 0 not flown: accepted as a limit. The new branch is unit-tested and break-checked (test 6); the
  reply path to commander is the same as test 7 (flown, break-checked); registration has no `enabled()` gate (read).
  Owner budget of 3 more tests not spent on it.
- MAJOR event id not asserted: accepted as a limit; the event is a log aid, the refusal itself is asserted.
- MINOR: comments, test-6 mask assert, format log fixed (FIXES.md). Docs lines fixed by the text update. Event delay
  and script pass condition: kept.
