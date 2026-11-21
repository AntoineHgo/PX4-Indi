# Pre-freeze review r2: stage-3 safety delta, firmware vs specification

Verdict: ACCEPT WITH FIXES (0 BLOCKING, 1 MAJOR, 7 MINOR)

Scope: `git diff 772e5fe72e HEAD` on `src/modules/mc_indi_rate_control`, `src/lib/indi_rate_control` and `rc.mc_apps`
(commits b7a171b4b5, 4385e8f56a, 5b70c50748, 4016a03ec8, 5d1d828af7, 7e58bea57c). Spec: DECISIONS F-1, O-11, D-S3-SPTO,
D-DEFAULTS-FW, D-STAGE-STALE, D-KY, D-A18-REOPEN, D-A18-SOURCE, plus `design/a18_jerk_ff_s141.md` (consumer section).
This was a read-only review at HEAD bbe3a452bd. Nothing was built, and no unit test or SITL was run (the unit-test
binaries are not built). Abbreviations: M = `src/modules/mc_indi_rate_control/McIndiRateControl.cpp`,
G = `IndiRateFeedforwardGate.{hpp,cpp}`, rc = `ROMFS/px4fmu_common/init.d/rc.mc_apps`.

O-11 check: `git diff --stat main -- mc_rate_control mc_att_control mc_pos_control control_allocator commander
control_allocation` is empty, so O-11 holds.

## Per change: what the spec asks and what the code does

| Commit | Spec | Code matches | Unit test that fails if broken |
|---|---|---|---|
| b7a171b4b5 autotune | S95 F1 / note 5c | yes, rc:31-40 | none (rc) |
| 4385e8f56a receipt time | S95 F2 | yes, M:374 | none: the watchdog tests take the time as an argument |
| 5b70c50748 ID_OK gate | D-DEFAULTS-FW | yes: K x0.5 unless ID_OK==1; G1/G2_Y defaults 1757/1640/205/27; W_MAX 0, ACT_TC 0.05 | pure function only (`EffectiveGainKIdentStatus`); the wiring at M:98-99 is untested |
| 4016a03ec8 no pos fallback | D-STAGE-STALE / D-start-fallback | yes, rc:57-63 | none (rc) |
| 5d1d828af7 K_Y 20 | D-KY | yes, yaml default 20 | n/a (default) |
| 7e58bea57c jerk FF | D-A18-REOPEN, a18 note | yes: valid, age < 50 ms, not landed, not acro, watchdog not stale, finite, roll/pitch only, not stored, a flip resets the lead | gate cases (`IndiRateFeedforwardGateTest`, 6 tests); the module wiring is untested |

D-A18-SOURCE rejected the drag term, and the delta adds none. Correct.

## rc.mc_apps start-up matrix

`MC_RATE_CTL_TYPE` is not a firmware parameter. It was removed in c1a700e7bb. It is only a bench alias that
`run_scenario.py` maps to `MC_INDI_EN`. `MC_INDI_EN` and `MC_INDI_POS_EN` both need a reboot.

| MC_INDI_EN | MC_INDI_POS_EN | Rate | Pos | Failure of the INDI module |
|---|---|---|---|---|
| absent/0 | absent/0 | PID | stock | n/a (stock) |
| 1 | 0 | INDI | stock | no rate controller, console PX4_ERR only (F1) |
| 1 | 1 | INDI | INDI | either one can be missing, console error only (F1) |
| 0 | 1 | PID | INDI | no position controller (F1). The INDI outer loop over the PID inner loop is a combination no decision covers (F8) |
| absent | 1 | PID | INDI | same as the row above (a board without the rate module) |

Autotune starts only when `MC_AT_EN > 0` and `MC_INDI_EN != 1`, including when the parameter is absent. That is correct.

## Findings

### F1. MAJOR: the vehicle can arm with no rate controller or no position controller
- Where: rc:17-24 and rc:57-63 (both have no `||` branch), M:67-87 (`init()` refusal paths).
- Evidence: commander has no presence check for any rate or position controller. A grep of
  `src/modules/commander` for torque/rates/attitude setpoint finds only `escCheck` (motor spin mask) and
  FailureDetector. The S95 F5 and D-STAGE-STALE UNVERIFIED item is now answered: arming is not refused. When the
  module fails to start, the only signal is a PX4_ERR on the console at boot. Whether it reaches the GCS before
  mavlink starts is UNVERIFIED.
- Consequence:
  - Missing rate controller: the vehicle arms and produces no torque or thrust setpoint. What the outputs do then
    is UNVERIFIED.
  - Missing position controller: the vehicle arms in a stabilized mode. A switch to Position/Auto in flight leaves
    mc_att_control holding its last attitude setpoint and thrust until a commander failsafe fires.
- F-1 is respected: there is no PID fallback. The brief requirement "must not arm with no rate controller" is not
  met. Stock PX4 has the same gap, and the probability is low (the `init()` refusal or a failed callback
  registration).
- Fix (commander is frozen by O-11):
  - In rc, add `mc_indi_*_control start || { echo "ERROR ..."; set STARTUP_TUNE 2 }` (the rcS error-tune
    pattern), or have a surviving module register an external arming check (`arming_check_reply`).
  - At minimum, record the gap as an accepted residual in D-start-fallback, with the owner's agreement.

### F2. MINOR: the FF age gate is fixed at 50 ms, so it chatters when the outer loop runs between 5 and 20 Hz
- Where: G.hpp:47 (`kMaxAgeUs = 50000`), M:389-404.
- Evidence: the outer stage stays in Indi mode, with `valid` set, down to 5 Hz (`kStageDtMax 0.2`). Between 5 and
  20 Hz, `omega_ff_on` is true for 50 ms of each period and false for the rest. Each flip resets the setpoint lead
  (sp_source bit 5) and steps the effective setpoint by up to |omega_ff| <= 3 rad/s (`kMaxOmegaFf`).
- Fix: tie the gate age to the stage hold limit (200 ms), or to the measured publish interval. Add a gate test at a
  60 ms period.

### F3. MINOR: up to 50 ms of FF is applied after the vehicle leaves an outer-loop mode
- Where: G.cpp:39. The gate excludes only the acro branch.
- Evidence: the publisher stops publishing when position control is inactive (McIndiPosControl.cpp:1100 sits
  inside the active branch). So after a switch to Stabilized or offboard body-rate, the last `valid` message is
  added to that mode's rate setpoint until it ages out. The a18 note matches this, so the code is spec-conformant.
- Fix: also require that the control mode has the outer loop active (`flag_control_velocity_enabled ||
  flag_control_acceleration_enabled`), or have the publisher send one `valid=false` message on exit.

### F4. MINOR: the FF gate trusts the publisher stamp, the pattern S95 F2 removed from the watchdog
- Where: G.cpp:44 (a future stamp gives `age = 0`), M:389.
- Evidence: the only publisher is internal and stamps in hrt (McIndiPosControl.cpp:1101), so the risk is low. A
  foreign or bridged publisher with a clock offset defeats the 50 ms age check. The rate module also does not clamp
  omega_ff and relies on the publisher's 3 rad/s clamp.
- Fix: stamp the receipt time when `_indi_rate_feedforward_sub.update()` returns true, as M:374 does, and constrain
  omega_ff to +-3 rad/s at the consumer.

### F5. MINOR: changing MC_INDI_ID_OK in flight steps the gains, and the wiring is untested
- Where: M:98-99, `indi_rate_control.hpp:392`.
- Evidence: `parameters_updated()` applies the change at once while armed. The parameter is not `reboot_required`
  and has no armed guard. K doubles or halves in one cycle, and so does `lead_gain = LEAD*K*ACT_TC`
  (indi_rate_control.cpp:452).
- The law is incremental, so there is no integrator jump. The torque step is ΔK·e/G1 plus the lead term, bounded
  by `MC_INDI_DT_MAX`. The step is small at hover errors and larger during a manoeuvre.
- Values other than 0/1 resolve to the halved gains, which is the safe side.
- No test fails if the module compares `!= 0` or skips the call.
- Fix: apply an ID_OK change only while disarmed or landed, or slew K. Also note in the yaml that the effective
  default K_Y is 10 at ID_OK 0, which is the G5.1 failure value of D-KY.

### F6. MINOR: no regression test for the receipt-time stamp (asked for in S95 F2)
- Where: M:374.
- Evidence: `IndiRateSetpointWatchdogTest` takes `last_rx` as an argument. If M:374 went back to
  `vehicle_rates_setpoint.timestamp`, all tests would still pass.
- Fix: extract the receipt step into the IndiSafety library, or add the future-stamp and zero-stamp test S95 asked
  for.

### F7. MINOR: the rc changes have no test, and the autotune notice is console-only
- Where: rc:31-40, rc:57-63.
- Evidence: the SITL rc test from S95 F1 / note 5e was not added. The `echo` is not sent to the GCS. The "once-only
  INDI warning when MC_AT_EN > 0" from note 5c is absent. A manual `mc_autotune_attitude_control start` is still
  possible.
- Fix: add a SITL boot check (`MC_INDI_EN 1 MC_AT_EN 1` -> autotune not running, INDI running), or accept the gap
  explicitly.

### F8. MINOR: MC_INDI_POS_EN 1 with MC_INDI_EN 0 starts silently
- Where: rc:57-63.
- Evidence: no decision covers the INDI outer loop over the PID inner loop. Under F-1 ("INDI runs alone") it is
  ambiguous. The module does not check `MC_INDI_EN`.
- Fix: decide the combination is allowed or refused. If refused, add `if MC_INDI_EN != 1 then echo, do not start`
  in rc, and refuse in `init()`.

## S95 findings status

| S95 | Severity | Status at HEAD | Evidence |
|---|---|---|---|
| F1 autotune with INDI | MAJOR | CLOSED | b7a171b4b5, rc:31-40. Residual F7 (no test, no GCS notice) |
| F2 watchdog uses the publisher stamp | MINOR | CLOSED in code | 4385e8f56a, M:374. The requested test is missing (F6). The same pattern is reintroduced in the FF gate (F4) |
| F3 thrust hold / 0.5 s default | MINOR | CLOSED (spec) | D-S3-SPTO chose the zero-rate thrust hold with a 0.5 s default; the code matches |
| F4 frozen-rpm residual gaps | MINOR | OPEN (unchanged, optional) | not touched by the delta |
| F5 start-up: no fallback, arming not refused | MINOR | OPEN, raised to MAJOR (F1) | commander has no controller-presence check (verified by grep). 4016a03ec8 extends the gap to the position controller, as specified |
| F6 item-1 checks | none | unchanged | n/a |

## UNVERIFIED
- The unit tests were neither built nor run. Test assertions were read only for the gate and the gain function.
- What the outputs do when armed with no torque setpoint. Whether a boot PX4_ERR reaches the GCS.
- Whether the outer-loop rate can fall into the 5-20 Hz band on real hardware (F2). SITL runs EKF2 at 100 Hz.
