# Route check 40 (sonnet, 2026-11-16, session 40)
Read: MISSION (Gates, Order of work), STATE, DECISIONS (D-G2-BREAK, D-G2-INJ, heads), ANOMALIES, JOURNAL tail, route_check_35.
No source, no logs, nothing flown. Numbers below are the ones STATE records.

## 1. On the shortest path to G2..G8?
Partly. The rate-loop slice of G2 is on the path; everything around it is not scheduled.
- rc35 plan vs actual: S37 injection player -> estimator + model; S38 "first margin flights" -> models only; S39 "G2 verdict
  draft" -> M3a plumbing + 1 hover; S40 "G3 task spec" -> unit tests. Slip: first G2 flight is S41, 3 sessions late; no
  G3 spec exists. Gates passed after 40 sessions: 0 (G1 frozen with 5 evidence limits, provisional under Q4-A).
- Process hole: MISSION says GATES.md must hold G2's exact tests and thresholds, committed, BEFORE the first G2 test. The S41
  flights are that test. STATE still says "decide in GATES.md before the first G2 test" (GM near-180 deg plateau rule). Do it first.
- Done that no gate needs (cheap, but stop): PID-on-x500 and archived indi_v3 margin table (G2 is the reference airframe;
  only A-1 uses them); M3b store points; 267 Hz analytic tables beyond what flights give; reading `_thrust_prev`; extra
  second keys on the same equations (T79 "AGREE" shares the model, STATE admits 4a is coding consistency only).
- Needed by a gate, nobody working toward it:
  * G2 other breaks: attitude, velocity, position, INDI acceleration loops. No break point is specified anywhere (note covers
    the rate loop only). Existing `McIndiPosControl`/`indi_accel_control` can be measured now, before stage 5.
  * G2 PM at code defaults is 42.7 deg < 45 (model, roll, 800 Hz): the pass needs ACT_TC identified and defaults changed
    = stage 3/4, not started. Margins of unfixed code are method validation only.
  * G3: none of the injectors (motor tc asymmetry, delay, mass/inertia, thrust sag/weak motor, telemetry loss/freeze,
    vibration, GNSS latency, wind) has a task; no randomised runner; no 20-run pre-test.
  * G4: three noise profiles from public logs: no source recorded, no task.
  * G5/G6/stage 5: outer loop for all modes, 0 sessions, owner-confirmed architecture A waiting since S13. It is the
    longest item (estimate 8-12 sessions) and G2 (outer breaks), G3 (no loss of control with no PID fallback), G5, G6 all sit behind it.
  * G7 beyond the new unit tests, G8: nothing yet; fine until stage 6.

## 2. Main difficulty is a consequence of which decision?
Pace, not a single bug: stage 2 spent S36-S40 on one loop because of D-G2-BREAK (r1 BLOCKING: gyro break misses INDI's model
and rotor-speed paths) -> D-G2-INJ (firmware change in our module, params, 7 new log fields, unit tests, a build) -> two
keys on each. The break choice is right; its cost was not planned (rc35 gave it one session). Underneath it: the
session shape from S1: one sonnet "big task" per session at a $3 cap (lessons S26, S35, S37, S39), a haiku second key per task, and
flights as the last step. Stage 1 (D-SIM-STEP, D-SCHED, A-14..A-20) used 35 sessions the same way; the stage order
(2 before 3) is the third cause: the PM < 45 finding is on code that stage 3 must change anyway.

## 3. Fresh start on stage 2 would
- Write GATES G2 first (tests, thresholds, GM rule), then fly at the end of the session that builds the injector, not two sessions later.
- Put the injector in the first inner-loop edit with ACT_TC identification and the stage 3 fixes (landed trim torque,
  timeout, frozen telemetry), so one set of margins is measured on the code that stays.
- One CPU-only estimator self-test plus one flown multisine per axis per rate, driven by a script over the whole matrix
  (host bash is free); no analytic second key where the key shares equations; flights are the second key.
- Specify all G2 break points in one note (rate, attitude, velocity, position, accel) before coding any of them.
- Run G3/G4 harness tasks in the same sessions as stage 2 and 3 (disjoint files, CPU-heavy, token-light).

## 4. Recommendations (gate gain per session)
1. GATES G2 text + S41-S42 flights: write G2 in GATES.md (half a session), fly roll/pitch/yaw, M3a model-only and measured,
   at 800/400/267 Hz, with the fault/landed assertions of the second key; compare with the model; apply the D-G2-BREAK overturn
   test. Gain: first measured G2 numbers on 3 of the ~8 breaks, validated method. ~2 sessions (S41-S42).
2. Stage-3 slice with ACT_TC: identify ACT_TC from a rotor step, set defaults so PM >= 45 at 400/800 Hz, then the listed
   stage 3 fixes and re-measure with the same script. Gain: rate-loop G2 pass, G5 landed handling, G7 tests, start of G6.
   ~3 sessions (S43-S45). In the same sessions run the G2 outer-break note (attitude/velocity/position/accel on existing
   modules), 1 session of a parallel sonnet task.
3. G3/G4 harness as parallel tasks (two sonnet tasks per session when files are disjoint, raise the cap to $4-5 for those
   sessions): plant-variant injectors with a G1.5 check each, randomised runner, noise profiles with recorded sources, 20-run
   pre-test on the rate/attitude stack. 3 sessions, S43-S45 in parallel with item 2. Then start stage 5 at S46 (8-12 sessions).
Honest projection: G2 rate loops ~S45, G3/G4 pre-test ~S46, stage 5 done ~S56, validation ~S62, packaging ~S66. Escalate to the
owner that "40 sessions, 0 gates" is stage 1 cost and that 25 more are likely; ask for the Q2-Q4 answers so G1 can be marked passed.
