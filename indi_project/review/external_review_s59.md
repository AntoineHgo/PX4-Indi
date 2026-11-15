# External review after session 59: from "benchmark report" to flight-ready INDI

Date 2026-11-15. Reviewer: an independent Claude session asked by the owner to challenge everything (criteria,
methodology, results, implementation, report, agent management) with one goal: **inner-loop and outer-loop INDI
controllers that are ready to fly on the owner's hardware** (AM32 ESCs, bidirectional DShot). Scope read: report
ch. 5-10, `bench/scenarios.md`, `bench/metrics.py`, `bench/run_scenario.py`, the four firmware sources, the frozen
parameter files, `results/vprime.md`, `results/s8n_oset.md`, and 160 raw ULogs of set O and the hover batch,
recomputed with scripts written for this review. Not done: no new flight, no firmware change.

Status of this file: advice to the owner. Sections 7 and 8 are **proposals**; they bind the orchestrator only once
the owner copies them into `OWNER_GUIDANCE.md` and removes `indi_project/DONE`.

Each finding is marked **[verified]** (reproduced from code or raw data in this review), **[derived]** (follows from
the code by analysis, not flown), or **[judgement]**.

## 0. Owner decisions taken after reading this review (2026-11-15)

These override the matching proposals below.

- **No PID fallback.** INDI must be robust enough to run alone. Gate 6 (sec. 7), item 7 of sec. 4 and the fallback
  part of step 4 (sec. 8) are withdrawn. The robustness evidence of gates 2 and 3 has to carry that weight.
- **INDI serves every flight mode** and must be able to replace the PID stack entirely. The offboard-only external
  mode of stage 8 is not the end state (sec. 5.2).
- **Generic target.** The architecture is to be offered to all quadcopter configurations with eRPM telemetry, with
  robust default tuning and a fine-tuning method. There is no target airframe and no real flight log; default PX4
  simulation airframes are the reference. Gate 4 and gate 7 (sec. 7) must be restated accordingly, and the "owner
  inputs" at the end of sec. 8 no longer apply.
- **Fresh start** on the reusable code, with the existing report, results and tests preserved as an archive.

## 1. Summary

1. The project answered "does INDI outperform PID under four pre-registered criteria" three times with "no". That
   question is no longer the useful one. Nothing in the criteria, the scenario sets or the report measures flight
   readiness: stability margins, robustness envelope, mode and failsafe coverage, behaviour at hardware loop rates,
   a loadable parameter set, a fallback. Section 7 proposes gates that do.
2. The primary metric of stage 8 is computed wrongly (sec. 2.1). The outer loop is much better than reported on
   nominal paths, and the baseline is much worse than reported. The verdict text, tables and abstract need redoing.
3. The criterion that fails stages 2b and 8 (hover effort) measures a difference of 0.1 % of full-scale motor command
   in a simulator that is far quieter than a real vehicle (sec. 2.2). It says nothing about hardware either way.
4. The final inner loop (`indi_v3`) and the final outer loop (`indi_pos_v3`) were each validated on a narrow set
   built around the previous version's weakness. Neither has flown the full matrix (sec. 3.3).
5. The outer loop very probably has the same structural flaw that sank v2 (no integral action against a
   command/output thrust gap), now on the thrust axis, and set O contains no entry that would show it (sec. 5.1).
6. Several implementation properties are unsafe for a first flight: no in-flight fallback to PID, `maybe_landed`
   handling, a failure path that only prints, firmware defaults that are not a validated configuration (sec. 5, 6).

## 2. Defects in the evidence

### 2.1 Trajectory metric: 5 Hz reference held between samples [verified]

`bench/metrics.py:309-317` computes the trajectory error as `vehicle_local_position` minus a zero-order hold of the
logged `trajectory_setpoint`. The logger records that topic at 5 Hz (median sample period 0.200 s in every set-O log;
the runner streams 50 Hz). The held reference is on average 100 ms behind the true one, about 0.3-0.4 m at the speeds
flown. A vehicle that lags by about 100 ms is therefore scored better than a perfect tracker, and a vehicle that tracks
well is scored as "ahead".

Recomputed from the 140 set-O logs (mean of 10 seeds, m). "ZOH" reproduces the reported value to three digits.
"Interp" uses a cubic Hermite reference built from the logged position and velocity. "Truth" replaces the EKF
position by `vehicle_local_position_groundtruth` with the mean frame offset removed.

| entry | PID reported (ZOH) | INDI reported (ZOH) | ratio | PID interp | INDI interp | ratio | PID truth | INDI truth | ratio |
|---|---|---|---|---|---|---|---|---|---|
| O1 lemniscate | 0.456 | 0.316 | 0.69 | 0.643 | 0.147 | 0.23 | 0.719 | 0.236 | 0.33 |
| O2 circle + z | 0.585 | 0.421 | 0.72 | 0.725 | 0.121 | 0.17 | 0.811 | 0.208 | 0.26 |
| O3 lemniscate + gust | 0.409 | 0.277 | 0.68 | 0.565 | 0.150 | 0.26 | 0.623 | 0.215 | 0.34 |
| O4 lemniscate + payload | 0.783 | 0.217 | 0.28 | 0.906 | 0.253 | 0.28 | 0.919 | 0.264 | 0.29 |
| O5 z-sine + CoM shift | 0.163 | 0.079 | 0.49 | 0.144 | 0.057 | 0.40 | 0.146 | 0.064 | 0.44 |
| O6 z-sine, mass x1.15 | 0.101 | 0.097 | 0.96 | 0.031 | 0.031 | 0.99 | 0.041 | 0.041 | 1.00 |
| O7 lemniscate, tau x2 | 0.456 | 0.320 | 0.70 | 0.642 | 0.145 | 0.23 | 0.706 | 0.227 | 0.32 |

Consequences:
- Every trajectory number in the report is affected: T5, H1, H4 (ch. 8.4, 8.6) and O1-O7 (8.11, 9.6, 10.6).
- O6's "significantly better, 4 %, p = 0.010" is an artefact: three quarters of both numbers was the held reference.
- The session-54/55 puzzle "INDI POS runs ahead of the reference" and part of the GNSS-delay investigation were
  chasing this artefact. The GNSS-delay finding itself is real (the EKF-vs-truth lag was measured separately).
- EKF-vs-truth disagreement is 0.06-0.14 m RMS after the delay fix, the same size as INDI POS's tracking error. The
  ground-truth topic is stamped at reception and logged at 59 Hz, so the "truth" columns carry roughly 0.1 m of
  timing uncertainty at these speeds. The metric must use ground truth with the simulator's own pose time stamp.
- Reproduce: `review/external_review_s59_notes/remetric.py` (method in sec. 9).

Why it was missed: every review in the project checked report text against `results/*.md`. None recomputed a result
from raw logs with independently written code (sec. 6.4).

### 2.2 Hover-effort criterion [verified]

Decomposition of the 10-seed hover batch (`results/s8m_smoke_gnss0/hover`), motor command resampled to 250 Hz:

| | reported motor-rate RMS (1/s) | command std (fraction of full scale) | derivative RMS 0-5 Hz | 5-30 Hz | above 30 Hz | true rotor speed std (rpm) |
|---|---|---|---|---|---|---|
| pid_tuned (10) | 0.043 (0.021-0.075) | 0.0011 | 0.008 | 0.009 | 0.033 (0.018-0.068) | 6.9 |
| indi_v3 under stock outer loop (2) | 0.053 | 0.0012 | 0.010 | 0.023 | 0.043 | 7.0 |
| indi_pos_v3 (10) | 0.088 (0.067-0.118) | 0.0020 | 0.027 | 0.047 | 0.055 | 9.1 |

- The whole dispute is 0.11 % against 0.20 % of full-scale command, and 6.9 against 9.1 rpm of rotor speed (1.3x). A
  real quadcopter shows command noise one to two orders of magnitude above this. The criterion measures the
  simulator's noise floor through a derivative, which weights the least physical band most.
- The metric differentiates a log that samples a 500 Hz command at an irregular 290-330 Hz without anti-aliasing.
- Most of `pid_tuned`'s flight-to-flight spread sits above 30 Hz (0.018-0.068), where the 2.57 Hz roll mode blamed in
  8.10 cannot contribute directly. The explanation in the report is incomplete; the cause is still open.
- The INDI POS excess is mainly below 30 Hz, in both collective and differential command. That is why the 5 Hz
  filter variant changed nothing. The cause is unidentified (candidates in sec. 5.3).
- A ratio against a baseline whose own value varies 3.5x between flights cannot carry a pass/fail decision.

### 2.3 Other errors found [verified]

- Report 8.10 mislabels V': the row called "W3 tau x2 + motor 2 at 0.8" is W5 (`vp_tau2_loss2_att`), and the row
  called "W5 eRPM gain 0.3" is W3 (`vp_gain03_att`, motors 0 and 3 at 0.85 thrust). No entry has an eRPM gain error.
- "1 kHz gyro" (10.5) and "1000 Hz IMU" (7.7): the IMU is 1 kHz, but `IMU_GYRO_RATEMAX` is 800, so the rate loop runs
  at 500 Hz (minimum `timestamp_sample` step 2 ms in the logs). INDI POS and its attitude loop run at 125 Hz, the
  stock attitude loop at 250 Hz.
- Context arms B and C of set O (`scenarios.md` sec. 10) were never flown. The feedforward share is unknown.
- `bench/params/indi_v3.params` sets `MC_RATE_CTL_TYPE` and `CA_R_W_MAX`, which no longer exist; the runner
  translates them (`run_scenario.py:420-424`). The frozen file cannot be loaded on a vehicle. It also repeats
  keys with different values (later lines win), which hides the actual configuration.
- Firmware defaults are no validated configuration: G1 320/210/30 (v1 units, first open-loop estimate),
  `MC_INDI_W_MAX` 0 (measured torque off), `MC_INDI_ACT_BLD` 0 (the v2 behaviour that settles at 13 deg of tilt on a
  motor fault), `MC_INDI_YAW_CUT` 0 (the 8x hover effort configuration).

## 3. Criteria and methodology

### 3.1 The acceptance criteria [judgement]

- They are a conjunction of ratio tests against PID. They cannot say "safe to fly" and they made a 3x tracking gain
  a "loss" on a noise-floor metric.
- Criterion 1 counts scenarios that no controller can fly (H4, W1, W4) as INDI failures.
- "Median improvement >= 10 % with p < 0.05 over 10 seeds" is pseudo-replication. Seeds change sensor noise only, the
  plant and scenario are deterministic, so p = 0.002 is the floor of the test and carries no information about
  generalisation. The run-to-run non-determinism of the co-simulation is larger than the seed effect in hover.
- The verdicts stand as history (O-2). They should stop steering the work.

### 3.2 The baseline [judgement, partly verified]

- `pid_tuned` has a lightly damped 2.57 Hz closed-loop roll mode in hover. A baseline with a lightly damped mode is a
  tuning defect that the cost function did not penalise, because the cost was dominated by hover position noise.
- The outer loop of the baseline was never tuned (stock `MPC_*`), and neither was INDI POS's. Set O compares two
  untuned outer loops.
- On nominal paths the stock pipeline lags by roughly 200 ms (0.64 m at 3.2 m/s RMS), which matches the attitude-loop
  time constant 1/`MC_ROLL_P`. The jerk feedforward cancels exactly that lag. The single FF-off flight was worse than
  PID. The nominal-path gain is therefore probably feedforward, and the O4/O5 gain INDI feedback. This has to be
  measured (arm C), with the corrected metric.

### 3.3 Coverage of the final controllers [verified]

| | flown at 10 seeds | never flown |
|---|---|---|
| `indi_v3` rate loop | V' (5 actuator-fault entries), hover | gusts, CoM shift, payload, nominal steps, rate pulses, tau x2 alone, eRPM latency and drops, vibration x3, any trajectory under the stock outer loop |
| `indi_pos_v3` | set O (7 path entries), hover | position hold under gust/payload, position steps, thrust gap (sag, weak motor), eRPM loss, realistic GNSS latency, EKF resets, take-off, landing, engaging the mode in motion |

Held-out sets were rebuilt after each loss around the weakness just found (H, V, V', O). No single matrix has been
flown by the final pair, so the report cannot say whether v3 kept v1's disturbance rejection (H3 0.16x, V 0.43x).

### 3.4 Unexplained anomalies that were accepted [verified from the project's own records]

The mission rule is "when a run is surprising, find the cause". Still open: the blend at Tb 0.1 s lost altitude and
was pruned unexplained, one factor of 3 from the frozen 0.3 s (`results/v3_screen.md:22`); the cause of the PID
hover spread; the sporadic vertical excursions in hover; INDI's sensitivity to the simulation speed factor; one
failed candidate in v2 tuning (c12); the cause of the outer-loop hover effort. Each of these is a possible stability
problem seen from the side.

### 3.5 Simulator [judgement, partly verified]

- Noise is not calibrated against any real log. All effort and noise conclusions depend on it.
- Rotor reaction torque in gz is about one tenth of physical (project's own O-4 result), so the yaw design and the
  decision to leave G2 at 0 do not transfer to hardware.
- The GNSS has zero latency and `SENS_GNSS0_DELAY` was set to 0. The right fix is a delayed GNSS in the simulator
  with a matching parameter, because the real EKF runs on a delayed horizon.
- No battery model: effectiveness and the command-to-thrust map do not move with voltage.
- Disturbance injectors are world-fixed wrenches (payload without inertia, CoM shift valid near level only).
- One airframe, one loop rate.

## 4. Inner loop (`mc_indi_rate_control`, `indi_rate_control`)

1. **No stability analysis exists [verified].** The report has no loop transfer function, no margin, no delay
   margin for any version. H5's limit cycle was explained by a "candidate mechanism, not reproduced numerically".
   Gains were chosen by random search on a noisy cost. Before flight the loop gain must be measured (chirp or
   multisine injected at the torque command in SITL, loop transfer estimated from the logs) for roll, pitch and yaw,
   and mapped over G1 error, actuator time constant, added delay and loop rate.
2. **The blend is a patch whose margin is unknown [verified].** `t_f = t_meas + LP_Tb(t_model - t_meas)` restores the
   model-based integral action below 0.53 Hz. It works on V'. But Tb 0.1 crashed, unexplained. Derive the closed-loop
   transfer function with the blend, explain that crash, and show the margin at 0.3 s. Alternative worth one design
   note: keep pure measured feedback and close the command-to-output gap per motor (slow correction of the
   command-to-omega^2 map), which also absorbs battery sag.
3. **Battery voltage [derived].** `MC_INDI_W_MAX` is a constant. On hardware full-throttle speed falls with voltage,
   so measured and commanded omega^2 diverge by tens of percent over a flight. The blend hides the steady part; the
   high-frequency gain error remains and no flight has tested it (V6/W4 are thrust ramps on attitude steps only).
4. **Yaw [verified].** Yaw bandwidth is K_Y 2.7 rad/s behind a 3 Hz filter, 1.15-1.3x worse than PID on every
   commanded-yaw result, and G2 is unused. With measured rotor speed the spin-up torque can be computed from the
   measured rotor acceleration instead of a tuned G2 on differenced filtered torque. Fix the simulator's rotor
   inertia first, otherwise yaw is being designed against the wrong plant.
5. **`maybe_landed` zeroes the feedback torque [verified, `indi_rate_control.cpp:373`].** A false `maybe_landed` in
   flight removes the whole trim torque for its duration (PID only freezes its integrator). `MC_INDI_DT_MAX` defaults
   to 1, so nothing bounds the step. Hold the state instead of zeroing it and test with an injected false flag.
6. **Filter matching at hardware rates [derived].** The synchronisation filters are designed at the controller rate,
   the gyro chain at the sensor rate (up to 8 kHz), and notch filters (the dynamic ESC notch is on in v2) are not
   mirrored on the torque path. Quantify the phase mismatch at 400 and 800 Hz controller rate with the notches a real
   vehicle uses.
7. **No in-flight fallback [verified].** `MC_INDI_EN` is a boot parameter. A first flight needs a pilot-operated
   revert. One way that keeps `mc_rate_control` at zero diff: the INDI module also links the stock
   `src/lib/rate_control` law and switches to it on an RC/parameter flag or on its own fault and oscillation
   detector, initialising the PID integrator from the filtered torque so the switch is bumpless.
8. **Robustness evidence is thin [verified].** G1 error was tested at inertia x0.8 and x1.3 only; delay was never
   varied for v3; time constant x2 only in combination. Needed: a grid or randomised campaign (sec. 7, gate 3).

## 5. Outer loop (`mc_indi_pos_control`, `indi_accel_control`)

### 5.1 Thrust-gap standing error [derived, not flown]

`t_c = t_f + (a_c - a_f)` with `t_f` from measured rotor speed and `thrust = |t_c| / (G_T k_cmd)`. If the motors
deliver a fraction s of the commanded thrust (battery sag, wrong `THR_MDL_FAC`, weak motor), the fixed point requires
`a_c - a_f = (1 - s) |t_c|`. In hover `a_f = 0`, so the law needs a standing acceleration command, which only a
standing velocity and position error can supply: about `(1 - s) g / (MPC_Z_P MPC_Z_VEL_P_ACC)`. With the logged gains
(1.0 and 4.0) that is 0.37 m at s = 0.85, 0.61 m at 0.75. This is the v2 mechanism of report 8.9 on the thrust axis.
The law has no integrator and no blend. Set O has no command/output gap entry (O4 payload and O6 mass are external
forces, which the accelerometer sees). A flight test was attempted in this review and blocked by the Docker wrapper
(no mount outside the repository); it is the first flight of the next session (sec. 8, step 2).

### 5.2 Safety and integration [verified in code]

- `_landed = landed || maybe_landed` gives zero rates and `MPC_THR_MIN` (`McIndiPosControl.cpp:294, 466`). A false
  `maybe_landed` in flight cuts thrust. The mode also cannot take off.
- The failure path levels the vehicle with the last thrust and prints an error. Nothing tells commander to leave the
  mode; the arming-check reply is always `can_arm_and_run = true`. On hardware there is no benchmark watchdog.
- The mode replaces OFFBOARD entirely and consumes only position/velocity/acceleration trajectory setpoints. It
  serves no pilot mode, no hold, RTL or land. For flight readiness decide whether INDI POS stays an offboard-only
  experiment or becomes the acceleration-to-attitude stage behind the flight-task setpoints.
- EKF reset counters are ignored; a position or velocity reset becomes a step in `a_c`.
- No module-level test exists (scheduling, window average, bias, hold, landed).

### 5.2b Further items from a line-by-line comparison with the stock modules

Found by a delegated code read (file:line in `review/external_review_s59_notes/module_parity.md`). Items 1-2 above were confirmed independently by it.
The rest are **not traced by the reviewer**: check each before acting.

Outer loop:
- Take-off from the ground looks impossible in this mode (minimum thrust while landed, no ramp), and there is no
  landing handling.
- `setpoint_config` is published once on mode entry and its reply is never read, while commander's default setpoint
  type is trajectory: the stock chain may publish `vehicle_rates_setpoint` alongside for a short time at entry.
- Offboard attitude, rate and actuator setpoints are silently ignored once the mode replaces OFFBOARD; after 100 ms
  without a trajectory setpoint the vehicle holds level.
- The arming check does not refuse when `MC_INDI_W_MAX` or rotor telemetry is missing; thrust then silently uses the
  open-loop fallback.

Inner loop:
- Both rate modules can be started by hand at the same time (separate module descriptors, the exclusion is only in
  the start-up script). O-11 asked for a refusal in the module.
- The last rate setpoint and thrust are held forever if the publisher dies (same as stock, but INDI POS is a new
  publisher that can stop). Add a setpoint-age timeout.
- `mc_autotune_attitude_control` still starts with `MC_INDI_EN` 1 and would tune PID parameters that INDI ignores.
- Real DShot driver: `esc.timestamp` is refreshed on every publication, and on a failed frame the previous rpm is
  republished with a fresh time stamp. The module's error-counter test catches CRC failures, but a channel without
  capture or a frame replaced by extended telemetry freezes the rpm with no error and no stale time stamp. The
  staleness logic validated in simulation therefore does not cover the real failure mode. Add a per-motor
  "last new value" time.
- `esc[j]` index and online-flag bit are assumed equal (true only for contiguous motors); the pole-count parameter
  scales `esc_rpm`, so `MC_INDI_W_MAX` must be identified from the same telemetry; one stale motor invalidates the
  whole measurement.
- No reset of the INDI states on a rising edge of `flag_control_rates_enabled`; no battery scaling.

### 5.3 Design questions [judgement]

- Hover noise source unknown. Ablate by signal substitution in simulation: ground-truth acceleration for `a_f`,
  unquantised rotor speed for `u_f`, ground-truth velocity for `v`. One of the three will show the path.
- `G_T` and `k_cmd` were identified in hover only (R^2 0.34-0.93). Validate over thrust level and airspeed from the
  set-O logs before trusting them at 35 deg of tilt.
- No snap feedforward and a differenced, filtered jerk. Measure what the feedforward contributes before extending it.
- Sensitivity to GNSS latency and to EKF velocity noise is untested.

## 6. Report and process

### 6.1 Report structure [verified]

The report is a chronological log, and a reader cannot find the final controllers in it.
- Ch. 5.1-5.8 describe in the present tense code that no longer exists (`MC_RATE_CTL_TYPE`, selection inside
  `mc_rate_control`, latching while disarmed). The measured-torque path and the blend have no design section; they
  appear only in the tuning chapter (7.7, 7.8).
- No table of the final parameter values, no block diagram, no frequency-domain figure. All nine figures are v1.
- Ch. 8.1-8.8 and 10.1-10.4 present the superseded v1 result as "the main finding of this thesis".
- Drafting residue is still in the text ("Unverified: ... tests were not re-run for this chapter", a section
  "Inconsistencies and unverified claims", "had not been evaluated when this section was written").

A delegated line audit (`review/external_review_s59_notes/report_audit.md`, file:line for each) adds: `MC_RATE_CTL_TYPE`
is cited as current in ch. 1, 5, 7, 9 and 11; "`esc_rpm` echoes the command" in ch. 4, 5, 6 and 9; the test count is
given as 18 and 19 where the tree has 40; "stage 2" names three different things in ch. 5; 9.5 item 6 still says the
outer loop is "not implemented"; 10.6 says "every one of 10 seeds" where O6 is 8 of 10; 9.6 uses O6 as the undisturbed
reference for O5 although the two differ in mass; the W1/W2 metric was changed from the frozen "roll and pitch
attitude RMS" to tilt RMS without an amendment in `scenarios.md`; hover-effort ratios are quoted as 1.7x, "about 2x"
and 2.14x for the same configuration.

Proposed shape: Part A the final design (both loops, one block diagram, final parameters, analysis with margins);
Part B the validation of the final pair against the gates of sec. 7; Part C the history (v1, v2, verdicts) as an
appendix, unchanged.

### 6.2 Reviews checked the wrong interface [verified]

`report/review_s8.md` verified every number of 8.11 against `results/s8n_oset.md` and found them consistent. The
numbers were consistent and wrong. Add a standing rule: before any verdict, each primary metric is recomputed from
raw logs by code written independently of `bench/metrics.py`, and metrics are computed against ground truth.

### 6.3 Agent management

See sec. 10 (filled from a transcript audit).

## 7. Proposed flight-readiness gates (replace "outperforms PID")

Each gate has a number, a test and a pass threshold fixed before the test. PID flies the same tests as a reference,
not as a pass condition.

1. **Evidence integrity.** Setpoints logged at full rate; tracking against simulator ground truth with interpolated
   reference; every primary metric recomputed by a second script; `metrics.py` unit-tested on a synthetic log.
2. **Measured stability margins.** Loop transfer functions identified in SITL by injection at each loop-break point
   (rate x3, attitude, velocity, position, and the INDI acceleration loops). Pass: gain margin >= 6 dB, phase margin
   >= 45 deg, delay margin >= 2 control periods plus the identified eRPM latency, at 400 and 800 Hz controller rate.
3. **Robustness envelope.** Randomised campaign (plant drawn per run): G1 x[0.5, 2], motor time constant x[0.5, 3]
   with asymmetry, added loop delay 0-10 ms, mass and inertia +-30 %, thrust scale 1.0-0.7, eRPM latency 0-3 frames
   and loss, vibration x[1, 5], GNSS latency 80-250 ms with matching and mismatched compensation. Pass: no failure,
   no sustained oscillation (spectral peak detector on rates), in at least 300 runs per controller.
4. **Noise.** Simulator gyro and accelerometer spectra matched to a real hover log of the target airframe. Pass:
   absolute limits on rotor-speed ripple and on command RMS, chosen from that log, not a ratio to PID.
5. **Flight envelope and modes.** Take-off, landing, land-detector transitions including injected false
   `maybe_landed`, every pilot mode on the INDI rate loop, mode switches in motion, RC loss, offboard loss, kill and
   re-arm, sustained saturation, EKF reset. Pass: no failure, bounded transients with stated limits.
6. **Fallback.** In-flight revert to PID on a switch and on a detected fault, bumpless, demonstrated in SITL from
   an induced limit cycle (the H5 case).
7. **Target hardware.** Builds for the target board; CPU load and stack measured; loop timing at the real rate;
   bench test with propellers off measuring eRPM rate, latency and error counters from the real DShot driver;
   written identification procedure and script for `MC_INDI_W_MAX`, `THR_MDL_FAC`, G1, actuator time constant, eRPM
   delay, `G_T`, `k_cmd` from one PID flight log; one airframe parameter file with the real parameter names.
8. **Code.** Module-level tests; all items of `review/control_law_review_s16.md` and of this file closed or
   justified; safe firmware defaults (measured torque and blend consistent, or INDI refuses to arm unidentified);
   documentation page in `docs/en`.

## 8. Proposed order of work (CPU-heavy, token-light first)

1. Fix the evidence: logger rate for `trajectory_setpoint`, ground-truth pose time stamp, `metrics.py` trajectory
   and effort metrics, a metric self-test. Re-score the existing set-O, T5, H1 logs (no flight needed). Correct
   report 8.4, 8.10, 8.11, 9.6, 10.6.
2. Thrust-gap test of INDI POS: hover and O1 with thrust scale 0.85 and with one motor at 0.8, both controllers,
   3 seeds. Predicted altitude offset 0.37 m at 0.85. If confirmed, design the remedy before anything else on the
   outer loop.
3. Loop-gain identification tooling (gate 2) and the margin table for `indi_v3` and `pid_tuned`. Explain Tb 0.1.
4. Safety items: fallback law in the INDI module, `maybe_landed` handling in both modules, failure signalling to
   commander, EKF reset handling, safe defaults, real parameter file.
5. Simulator: calibrated noise (needs a real log from the owner), rotor inertia, delayed GNSS, battery model.
6. Arm C and arm B on set O with the corrected metric; outer-loop hover-noise ablation.
7. Robustness campaign (gate 3) and mode coverage (gate 5) for the final pair.
8. Hardware bench items (gate 7), then the report restructured as in 6.1.

Owner inputs needed: a hover log from the target airframe, the board and ESC/motor/propeller data, whether INDI POS
must serve pilot modes or stays offboard-only, and whether a runtime PID fallback inside the INDI module is
acceptable under O-11.

## 9. Reproduction of sec. 2.1 and 2.2

Scripts: `review/external_review_s59_notes/remetric.py` and `hover.py` (host Python with `pyulog` and `numpy`).
Unit tests re-run for this review at HEAD 353c017971: 40 + 19 + 4 pass (`unit_tests.md` in the same folder). For each set-O run: take `t_window_start_us`/`t_window_end_us` from
`run.json`; reference = cubic Hermite through the logged `trajectory_setpoint` position and velocity samples;
estimate = `vehicle_local_position` x, y, z interpolated to the same times; truth =
`vehicle_local_position_groundtruth` plus the mean (estimate - truth) offset over the window; RMS of the 3D norm.
The zero-order-hold variant reproduces `metrics.json` `trajectory.rms_3d_m` to three digits, which validates the
window and the data selection. Effort: `actuator_motors` control[0..3] in the window, linearly resampled to 250 Hz,
Welch spectrum (1024-sample Hann), band-integrated with a (2 pi f)^2 weight for the derivative columns.

## 10. Agent management

Numbers below come from a delegated audit of `logs/run-*.jsonl`; the reviewer did not recount them, and the audit
marks its cost estimates for `STATE.md` as assumptions.

| | |
|---|---|
| Sessions logged / total spend | 62 / $156 |
| Spend by model | orchestrator (opus) $112 (72 %), sonnet $26.5, fable $17, haiku $0.8 |
| Subagent launches | 63: sonnet 40, haiku 15, fable 8; `model` passed on every one |
| Outcome | 47 completed, 5 failed (all in session 1), 10 killed by a session ending or the cap: 24 % did not finish |
| Task size | median 16 tool calls; 6 agents above the 30-call guideline (max 59) |
| Concurrency | above 3 only once (5, session 1) |
| Orchestrator context | 2,496 calls at 77k tokens average; `STATE.md` is 131 KB (about 35k tokens), read in 61 of 62 sessions |

What worked: the model was always explicit and matched to the task; after session 1 tasks were small; the
orchestrator re-ran gtests in Docker and read diffs for firmware changes; a reproduced bug got a regression test
that fails without the fix; little spend went to polling (5 % of calls).

Weaknesses, in order of consequence:
1. **Delegation was light, and the expensive model did the cheap work.** 72 % of the spend is the orchestrator's own
   context, on about one subagent per session. Log crunching, result tables and chapter drafts ran largely in the
   orchestrator. The scarce resource was spent re-reading history.
2. **`STATE.md` was never pruned.** It grew from 4 KB to 131 KB and is re-read at every launch. The ledger it is
   supposed to hold has 21 rows for 59 sessions.
3. **Verification stopped one layer short.** Firmware from subagents was checked. The benchmark tooling was not:
   `bench/metrics.py` was written and self-validated by one sonnet agent and never cross-checked, and it decides
   every verdict (sec. 2.1 is the result). Chapter drafts were accepted after a word count and a grep.
4. **Reviews came late and looked at the wrong interface.** The control-law review ran after the v1 freeze and found
   a bug that had been in the frozen firmware for eight sessions. The owner's stage-8 code review found four defects
   (accelerometer aliasing, delay direction, bias, fallback) in code that had passed its unit tests. The fable
   reviews of results compared report text with result files.
5. **Long reviews were scheduled against the spend cap.** The control-law review was launched six times and killed
   three times by session end; it cost about $14.

Proposed rules for the next stage (to add to `ORCHESTRATOR_PROMPT.md` if the owner agrees):
- Keep `STATE.md` under 150 lines: status, next actions, open problems, ledger of the current stage. Move history to
  `STATE_ARCHIVE.md`, which is never read at launch.
- The orchestrator does not process logs or draft chapters. Those go to haiku/sonnet with an output file.
- Two-key rule for anything that decides a verdict or enters flight code: metric code, identification scripts and
  control-law changes get an independent second implementation or review **before** the result is used, by an agent
  that does not see the first one's output.
- A review brief names the interface to check: raw data to result, result to report, code to spec. One brief, one
  interface.
- A review of safety-critical code happens before the freeze of the configuration that contains it.
- Launch a long agent only when the remaining session budget covers twice its expected cost, and have it write
  findings as it goes.
- Every unexplained anomaly gets an entry in an open-anomalies list with an owner and a closing test; a
  configuration with an open anomaly within a factor of 3 of its parameters is not frozen.

## 11. Follow-up reviews (identification scripts, simulator hooks, unit tests)

Three delegated reviews, done after the owner's decisions of section 0. Detail with file:line in the notes folder
(`ident_review.md`, `sim_review.md`, `test_review.md`). They are code reads; only the items marked "ran" were
executed. Treat each as a lead to confirm.

### 11.1 Identification scripts

| script | status | main reason |
|---|---|---|
| `identify_g1.py` | suspect | torque held at an irregular ~286 Hz onto 250 Hz gyro samples, mixes `timestamp` and `timestamp_sample`, filters assume exactly 250 Hz, fits one-sample increments (so its R^2 is not about acceleration), no treatment of closed-loop bias. Ran on synthetic data: open loop recovers 59.4 for 60; a crude closed loop gives 62.2 and the wrong delay |
| `ident_gt.py` | suspect | fit through the origin on a hover window: with no excitation it returns g divided by mean thrust, and the centred R^2 it prints means little. G_T 16.63 is therefore not an independent identification |
| `identify_g2.py` | suspect | interpolates through stale rpm samples, filter run at 1 kHz where the gyro chain ran at 250 Hz |
| `ident_s8_delay.py` | suspect | cross-correlates a controller-internal topic by logged cycle index, integer lags only |
| `accel_gain.py` | wrong | differentiates 59 Hz ground truth and reads a 30-80 Hz band from it, above its Nyquist rate. The hover-effort attribution of report 8.10 ("75 % of the excess in 30-80 Hz", gain 0.0065-0.0072) rests on this script |
| `identify_actuator.py`, `gt_lag.py`, `check_sync.py` | sound | handle stale and irregular samples; the first is tied to simulator parameters |

None has a self-test. All but two depend on this benchmark's step scenarios and `run.json` events, so none is yet a
method for an arbitrary airframe.

### 11.2 Simulator hooks

- **Run-to-run non-reproducibility has plausible causes, never tested.** Setpoints, parameter changes and wrenches
  are sent from Python over MAVLink or gz-transport: timed in simulation time but applied zero to several steps late
  under host load, and logged as commanded, not as applied. Rotor speed is read on a different thread from the
  telemetry sampling.
- The eRPM drop generator has a fixed seed: every "seed" sees the same drop pattern.
- Gust drag uses the world wind speed, not air-relative velocity, with a world-vertical lever arm; payload is weight
  without mass or inertia; the CoM-shift torque is world-fixed (known).
- Vibration is added after the IMU sample with no band limit, so its effect depends on the IMU rate; amplitudes have
  no source.
- The mass variant scales the base link only; the IMU-rate option also changes the physics step, so "rate" variants
  are confounded with solver changes.
- Ground truth is stamped at reception.
- Checked and consistent: thrust-scale, motor-fault and sag hooks scale the rotor speed itself, so telemetry agrees
  with the thrust produced; the eRPM encoding and held-value-on-drop match the real driver; the injector runs on the
  simulation clock.

### 11.3 Unit tests

- About 40 single-line mutations of the three libraries would survive the 63 tests (sign flips, removed clamps,
  broken fallback, broken blend among them).
- The only closed-loop plant is a roll-only model with the same time constant, G1, filters and rate as the
  controller, and no delay: a shared modelling error cannot show. The outer-loop library has no closed-loop test.
- Every outer-loop test uses a level or yaw-only attitude, so a rotation applied the wrong way round would pass.
- The measured-torque test inverts the production formula with the production allocator.
- The rate-loop test fixture is linear and can host a margin check (parametrise plant time constant, G1 scale,
  delay and sample rate).
- Caveat from the reviewer: two blocks of test code were judged from names only.
