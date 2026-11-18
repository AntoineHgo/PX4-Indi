# Route check 103 (S103 start, 2026-11-18)
Read: STATE, DECISIONS (headings, D-GAP/D-RATE-LEAD pointers), ANOMALIES (A-37 + head), JOURNAL tail (S98-S102), route_check_98,
GATES (headings, G2 section). No source code, nothing flown.

## 1) Shortest path?
Mostly yes, with two off-path items. Since RC98 the plan was followed: coverage stopped, hooks built (seed, IMU noise, delay
A1/A2), all 24 INDI v2/model-only rate cells flown, keyed (K100, K101) and passing (worst GM 10.1 dB, PM 68-71, DM 39.7 ms).
- On path: hook B (GNSS delay, G3 text needs 80-250 ms) and G5 pre-tests (first G5 evidence, validates D-ALTCTL-Z).
- G2 table: INDI rate (24) done; attitude 6 cells done (S91/S92); z/xy accel and velocity/position cells mostly done (xy 16
  cells S87, z S83). Still open for a verdict: PID M1 reference (F-5, reference only, NOT a pass criterion), linear
  cross-check (iii), yaw outside rate cells, hole-reporter extension, attitude-break with new setpoint path (vi).
- Off path / defer: (a) A-37 closure beyond a cheap check: it blocks only DLY_ACT use in G3, not G2 and not G5; (b) PID M1
  hook build (no recipe, reference only); (c) MARGIN lowest-priority T78 model extras. The A-37 boot lines are benign
  (disarmed sparse mixer calls); this is the second anomaly session at most, so cap it (see 4).
- G2 table item (vi) is cheap to defer: final cells are re-flown on the frozen pair in stage 6 anyway.

## 2) Decision behind the difficulty
D-SCHED / D-SIM-STEP era choice of a gz bridge with free-running actuator publishing (esc_rpm ~12/s, irregular mixer calls)
means actuator latency cannot be observed from existing telemetry, so A-37 cannot be closed from logs. Delay in the hover
excitation is also below observability. Underlying: D-RATE-LEAD / ACT_TC (S53) makes the actuator lag a model parameter
that G3 must later test, so "delay hook correct" has to be shown by a step, not by inference. Higher up, the owner rule
"no PID fallback, all modes" plus D-GAP (see RC98) is still what keeps G5 expensive.

## 3) Fresh start on this stage
Build the delay hooks with a self-reporting counter in the hook (per-call t_in, release age, drop count into a logged
topic or px4.log summary at disarm) so verification needs no extra flights, and decide that G3 delay robustness is tested
at the IMU path plus a motor-command offset measured by that counter. Interleave: build every injector with its G1.5 check
as one deliverable, and write the G2 verdict note as soon as the cell table is complete instead of leaving it for stage 6.

## 4) Next actions, ranked
1. A-37 as one time-boxed cheap test (<= $0.5, this is its 2nd and last session): add counter output or use truth rotor
   speed at 800 Hz in a d0 vs d5 step run; if not conclusive, PARK with bound "IMU exact, actuator hook UNVERIFIED, G3 does
   not use DLY_ACT until closed", reopen when G3 delay campaign needs actuator delay.
2. G5 pre-test (v): s5_gap085 POSCTL + stick ALTCTL gap + EN/AT_EN start check; host runs, metric bench/s5_gap_check.py.
   Reason: first G5 evidence, highest risk of a D-GAP/D-ALTCTL-Z surprise that costs sessions later.
3. G2 verdict note (iii + hole reporter + per-axis table compiled in GATES.md): cross-check margins_models.py for v2 path vs
   measured; reason: G2 is the closest gate and only needs this paperwork plus stage-6 refly.
4. Hook B GNSS delay (one sonnet task + G1.5 check, ~$1.5): needed before the G3 campaign and G5 EKF-delay cases.
5. Defer: PID M1 hook (ii), attitude-break re-check (vi), A-4/A-6/A-30 parked anomalies, harness work.

## 5) Progress
Sessions since stage 3 opened: S49 to S102 = 54 sessions (S103 is the 55th). Gates passed: 1 of 8 (G1, S84).
G2 is closest: the measured rate/attitude/outer cells exist and are keyed on the preliminary pair; what is missing is a
written verdict (linear cross-check, PID reference marked reference-only, yaw/hole-reporter statement). It cannot formally
close before the stage-6 frozen-pair re-fly, but a "G2 ready except refly" note is closable in S103-S104. G3-G8: none close.
