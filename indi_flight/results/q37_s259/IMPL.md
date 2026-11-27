# INDI refuses arming when the measured path is off, tests 6 and 7: implementation notes

Nothing is committed (working tree only). Commander, mc_rate_control, mc_att_control, mc_pos_control, control_allocator and
`src/lib/control_allocation` are untouched. The design of the arming check itself is in `../q36_s258/IMPL.md`.

## Design change
- `IndiErpmArmingCheck::evaluate`: while disarmed, `!measured.enabled()` (`MC_INDI_W_MAX` = 0, or no rotor geometry in the
  `CA_*` parameters) now returns `can_arm = false` with the new `Verdict::not_configured = true`. Still `can_arm = true`
  while armed (checked first). The telemetry criteria are unchanged.
- `McIndiRateControl::updateArmingCheck`: registration with the commander was already independent of `enabled()` (it only
  looks at `armed` and the registration state), so it also happens with W_MAX 0; nothing to change there. The pacing is
  shared with the existing event (first event after 2 s of refusal, then every 10 s). `not_configured` sends the new
  standalone event `mc_indi_rate_control_rpm_not_configured` ("Arming denied: set MC_INDI_W_MAX and the rotor geometry",
  description names `MC_INDI_W_MAX` and the `CA_ROTORn` geometry), otherwise the old `mc_indi_rate_control_erpm_missing`.
  Both are in `build/q36_sitl/events/px4.json`.
- `mc_indi_rate_control_params.yaml`: `MC_INDI_W_MAX` long text, "Set to 0 to disable, INDI then uses its actuator model and
  the rpm arming check is off." -> "Must be set: with 0, INDI refuses to arm."
- Module description (usage text in `McIndiRateControl.cpp`): says arming is refused while W_MAX / geometry is not set or a
  motor has no rpm telemetry.

## Files changed
- `src/modules/mc_indi_rate_control/IndiErpmArmingCheck.cpp`, `.hpp` (Verdict field, behaviour, comments)
- `src/modules/mc_indi_rate_control/IndiErpmArmingCheckTest.cpp` (test 6)
- `src/modules/mc_indi_rate_control/McIndiRateControl.cpp` (event choice, module description)
- `src/modules/mc_indi_rate_control/mc_indi_rate_control_params.yaml`
- `indi_flight/results/q37_s259/` (this folder: scripts, logs, runs)
- Not edited, now stale: `docs/en/config_mc/indi_control.md` lines 108 and 172 ("W_MAX 0: measured torque disabled, actuator
  model used"). The docs update belongs to the later docs step.

## Test 6 (unit) and break-check
`NotConfiguredRefusesWhileDisarmed` (x500 geometry, fresh telemetry on all 4 motors): W_MAX 0 -> disarmed refuses with
`not_configured`, armed allows; no rotor geometry (fresh `IndiMeasuredTorque`, W_MAX set) -> same; W_MAX set again -> allows,
`not_configured` false. `breakcheck.sh` / `breakcheck.log` (mutate `IndiErpmArmingCheck.cpp`, build, run, restore):

| Case | Mutation (one line) | Result |
|---|---|---|
| e (new behaviour reverted) | `if (!measured.enabled()) {` -> `if (false) {` | FAILED: only test 6 |
| a | `result.valid && fresh` -> `false && fresh` | FAILED: AllMotorsFreshCanArm, test 6 |
| b | drop the `result.valid` term | FAILED: MotorWithoutTelemetryRefuses, StaleSampleRefuses |
| c | drop the `isSampleFresh` term | FAILED: StaleSampleRefuses only |
| d | `if (armed) {` -> `if (false) {` | FAILED: NeverRefusesWhileArmed, test 6 |
| restored | none | 5/5 PASSED |

## Test 7 (SITL flight) and break-check
Script `arm_refusal_flight.py` (wraps `bench/run_scenario.py` `main()`, patches `Sim.cmd`). Why a script: the runner only
changes the telemetry at timed points inside a flight (after arming) and has no hook between boot and arm; here the runner's
own arm-retry loop drives the phases, and everything else (boot, params, takeoff, hover, metrics) is the unchanged runner.
It sets `rs.T_ARM_S = 15` so the 9 arm attempts (about 13 s of sim time) end near the usual 30 s and the hover timeline holds.
Phases (one arm command per ~1.5 s sim time):
1. attempts 1-4: `SIM_GZ_ERPM_LOSS = 15` (every eRPM frame of all 4 motors fails, samples go stale), must be refused;
2. attempts 5-8: loss cleared, `failure esc off -i 0` (ESC online flags cleared = missing), must be refused;
3. attempt 9: `failure esc ok -i 0`, must be accepted; then the runner takes off and hovers (hover scenario).
PASS needs 8 refusals, then acceptance at attempt 9, plus the flight completing (exit 0).

Result `sitl_refusal/` (seed 1, speed 3, INDI defaults with W_MAX 2700): `TEST7 PASS`, `metrics.json` status ok.

| Attempt | sim t (s) | telemetry | arm command |
|---|---|---|---|
| 1-4 | 22.7, 24.3, 25.8, 27.3 | stale (ERPM_LOSS 15) | refused |
| 5-8 | 28.8, 30.3, 31.8, 33.3 | missing (esc off) | refused |
| 9 | 34.8 | restored | accepted |

`sitl_refusal/px4.log`:
```
INFO  [mc_indi_rate_control] arming check registered, id 0
WARN  [commander] Arming denied: Resolve system health failures first      (x8, between "Ready for takeoff!" and the restore)
WARN  [failure_injection_manager] Injected: esc off, all instances
WARN  [failure_injection_manager] Cleared: esc, all instances
INFO  [commander] Armed by external command
INFO  [navigator] Using default takeoff altitude: 5.0 m
INFO  [commander] Takeoff detected
INFO  [commander] Landing detected
INFO  [commander] Disarmed by landing
```
From the ulog (`arm_refusal.json`, topics `arming_check_reply` and `event` were added to the logger list by the script): the
module's reply (registration id 0) was `can_arm_and_run` true until sim t 22.6 s, false from 22.6 s to 34.4 s, true after
(262 replies). One standalone event with argument mask 15 (all four motors) at 24.8 s (2 s after the refusal began; the next
would have been 10 s later, acceptance came first): id 0x1a56f1f, the only event with that argument; it was identified by its
argument and timing, the id hash was not computed. Neither event text appears in `px4.log` (events are not printed there).
The `flight.ulg` (130 MB) was deleted after reading; px4.log, metrics and arm_refusal.json are kept.

Break-check `breakcheck_sitl.sh` / `breakcheck_sitl.log`: `if (armed) {` -> `if (true) {` in `evaluate` (check always
allows), incremental SITL build, same flight: arming accepted at attempt 1 while the telemetry was stale, `TEST7 FAIL`
(`sitl_refusal_mutant/`). The source was put back and `build/q36_sitl` rebuilt from it (`sitl_build_restored.log`); the
unmutated flight above was flown on the same source before the mutation.

## Commands
```
indi_project/docker/run.sh -n q37ut -t 1500 'ninja -C build/px4_sitl_test functional-IndiErpmArmingCheck && build/px4_sitl_test/functional-IndiErpmArmingCheck'
indi_project/docker/run.sh -n q37bc -t 1500 'indi_flight/results/q37_s259/breakcheck.sh'
indi_project/docker/run.sh -n q37sitlb -t 5400 'ninja -C build/q36_sitl px4'
indi_project/docker/run.sh -n q37fly -t 1500 -e PX4_INDI_BUILD=$PWD/build/q36_sitl -- python3 indi_flight/results/q37_s259/arm_refusal_flight.py --scenario hover --controller indi --seed 1 --speed 3 --params indi_flight/results/q37_s259/sitl_params.params --out indi_flight/results/q37_s259/sitl_refusal
indi_project/docker/run.sh -n q37bcs -t 3000 -e PX4_INDI_BUILD=$PWD/build/q36_sitl 'indi_flight/results/q37_s259/breakcheck_sitl.sh'
indi_project/docker/run.sh -n q37fmt -t 300 'for f in <4 changed C++ files>; do Tools/astyle/check_code_style.sh $f; done'   # no output, clean; git diff --check clean
```
`sitl_params.params` is the q36 file (INDI defaults without `MC_INDI_DT_MAX`). `build/px4_sitl_default` was not touched.
`sitl_fly1.log` is a first attempt with the runner's default T_ARM_S: refusals worked (attempts 1-8) and attempt 9 was accepted
at 42.6 s, but the hover timeline (climb done by 46 s) no longer fitted, so the runner aborted; it motivated `T_ARM_S = 15`.

## Gate params with W_MAX 0 or absent and INDI on
- `indi_flight/bench/params/*.params` (2 files): both set `MC_INDI_W_MAX 2700`. None affected.
- All 412 params files under `indi_flight` with `MC_INDI_EN 1` or `MC_RATE_CTL_TYPE 1`: 384 set `MC_INDI_W_MAX` or `CA_R_W_MAX`
  (the runner maps the latter), 28 do not. All 28 are early stage 2/3/5 experiments (`results/stage2_s39..s48`,
  `stage3_s52..s57`, `stage5_s60`: injection, M3A, act-tc and yaw-lf/hf pretests), none a gate row, none in `freeze10_s193`,
  `freeze9_s183`, `actc_grid_s209` or a G5 params set.
- `run.json` of the gate result folders (`freeze10_s193`, `g3_refly_s121`, `g5_g55_s139`): the 138 runs of `freeze10_s193`
  all have W_MAX except 4 PID references (no INDI). INDI runs without W_MAX in `run.json`: `g3_refly_s121` (run_000,
  run_021, run_049: S121 G3 re-fly, early, before the measured path was in the gate configuration) and
  `g5_g55_s139/o2_failed_attempt1_s3x` (a failed attempt). The overlay is the only parameter source recorded in `run.json`;
  these would not arm on the new firmware, but they are historic and superseded by the later G3/G5 rows. The final gate
  configs (`quad5in_indi_defaults`, `quad5in_indi_g1`) set W_MAX 2700.

## Unverified / limits (Q37 limits (1)-(5) as they stand now)
1. Check off at W_MAX 0: closed in firmware and unit-tested (test 6). Not flown in SITL (no flight with W_MAX absent); the
   new event text was checked in `events/px4.json` only. `docs/en/config_mc/indi_control.md` still says W_MAX 0 disables the
   measured torque (stale, not edited here).
2. Ungated windows: unchanged and untested. About 1-1.5 s at boot before the first reply, about 1-2 s after the commander
   drops a silent registration, and silently none if the commander has no free external-check slot. An unconfigured airframe
   could still arm in such a window. The SITL flight shows the registration and reply path in one run (seed 1) only.
3. ESC driver must publish rpm while disarmed at about 50 Hz or more per motor: unverified on hardware (bring-up item). In
   SITL telemetry is present at standstill.
4. Frozen values are not detected while disarmed (the detection is armed-only): unchanged. SITL "stale" is CRC loss
   (`SIM_GZ_ERPM_LOSS`: the held value keeps its old timestamp), "missing" is the failure-injection ESC off; a frozen-value
   injection (`SIM_GZ_ERPM_FRZ`) was not flown and cannot refuse arming.
5. Refusal in running SITL: now flown once (stale, then missing, then accepted, takeoff, hover, landing), plus its break-check.
   Not covered: real hardware, GCS display of the events (the reply carries no events; the reason is the standalone event
   next to the generic "Resolve system health failures first"), an arm command that races the 300 ms reply cache (the
   decision uses a reply at most one request period old), a single seed, motors failing one at a time.
