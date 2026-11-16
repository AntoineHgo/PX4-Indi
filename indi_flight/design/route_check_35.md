# Route check 35 (sonnet, 2026-11-16, session 35)
Read: STATE, DECISIONS (heads), ANOMALIES A-14/A-19/A-20, QUESTIONS Q4, GATES G1 status, JOURNAL tail, route_check_30.
No source, no logs. S35 batch (`results/a20a19_s35/`) was still flying when this was written: its numbers are NOT used.

## 1. Still on the shortest path to G1..G8?
No, bluntly. 35 sessions, G1 has no item marked passed (GATES G1 status s33), G2..G8 and stages 2-7 have 0 sessions.
Route check 30 (rc30 section 4) said: freeze G1 by end of S31, "do not open another anomaly", escalate if not frozen.
What happened: S31 A-14 bridge fix, S32 A-20 fix + re-fly + A-19 reopened, S33 A-19 mechanism, S34 A-19/A-20 pre-test,
S35 A-20 15-run set + A-19 pre-test. Five sessions, zero gate progress, and the escalation (Q4, S32) was sent but then ignored:
work continued on stage 1 as if Q4 were B. rc30 item 3 (G1.5) and item 4 (freeze) still not done.
Do the open items touch a gate? A-20 (0.72 m baro bias in 2/30 at start, hover height 0.17 m off in 1/30) and A-19 (EKF yaw
0.4-1.5 deg) are simulator-estimator artifacts. Neither is in the rate loop, which is what G2 (margins), G3, G4 score. A-19
only matters for a yaw-on-truth threshold, which can be stated on the estimate with the heading error beside it. G1.6(c) is
met in the sense that matters (tracking spreads <= 2.5 %, causes named and bounded in GATES).

## 2. Which decision is this a consequence of?
- Immediate: the ANOMALIES:3 rule "nothing is frozen with an open anomaly that touches it" + G1.6(c) "cause identified". Together they
  make every simulator oddity a freeze blocker. It is not in DECISIONS as a decision, it is a table header; it overrode rc30.
- Mechanical: D-A14 (S28): once the bridge baro was made consistent, the stock baro-GNSS offset calibration (`CAL_BARO0_OFF`,
  VehicleAirData) became visible, hence A-20's residual 2/30. Each fix of the sim's sensors exposes the next stock estimator behaviour.
- A-19: G1.2 "tracking metrics read truth" (right) exposes the EKF heading error; the sim EKF is not the object under test.
- Root as in rc30: D-SCHED/D-SIM-STEP chose "same seed gives the same flight" as the standard, which for a full EKF in the loop
  is unbounded work (every unseeded init, mag, baro calibration, thread order is a new anomaly).

## 3. A fresh start on stage 1 would
- Fix the estimator configuration in the bench params at day 1 (SENS_BAR_AUTOCAL 0, mag heading-only or a fixed init yaw, baro
  ref set once), because the INDI/PID rate loop is the object under test, not the sim EKF. S34-35 found exactly these lines.
- Define G1.6(c) on controller and truth quantities with written bounds, not on the EKF; freeze G1 at a fixed session with bounds.
- Make the ANOMALIES rule "an open anomaly blocks only the verdicts that read it" (as rc30 recommended, not applied).
- Run stage 2 (CPU-only linear margins, A-1) from session ~4, in parallel; it never depended on the simulator.
- One sensor-consistency check in the first pre-test flight (would have found A-14 at S10, not S28).

## 4. Recommendation S36-S40
Park A-19 by mechanism now. Wording for ANOMALIES: "per-run EKF2 heading error 0.4-1.5 deg set at yaw alignment from magnetometer
fusion (3-axis field/bias states), constant within a run (std <= 0.05 deg), varies across runs, not a frame error (roll/pitch
<0.02 deg, setpoint follows the EKF within 0.02 deg), declination mismatch candidate refuted 3/3 (S34). Bound: <= 1.6 deg in SITL;
yaw verdicts quoted on the estimate, heading error reported beside; rate/INDI gates do not read absolute heading." The only S36
action on A-19: read the S35 EKF2_MAG_TYPE 1 pre-test once (30 min). If < 0.3 deg in both runs, adopt the param line in the bench
set and close; otherwise park as written. No further A-19 runs either way (6+ sessions spent).
A-20: read the S35 15-run closing check once. If it closes, close. If not, park with the measured bound (bias0 and hover z).
No new bridge change, no new runs for either.
Stage 2 starts in parallel immediately (S36), no owner answer needed (Q4 is non-blocking; mark results "provisional under Q4-A",
as Q2/Q3, owner-reviewable, reopened if the owner says B):
- S36: (a) write G1 FINAL in GATES (per item pass or bound; evidence limits A-7, A-10, A-13, A-14, A-17, A-19, A-20; G1.5 per
  injector at its first use); (b) sonnet: stage-2 design note: linear rate-loop model with blend, answer A-1 (CPU only).
- S37: loop-gain injection player row kind (sim-only, frame/sign/2 %/applied-time G1.5 test, A-13 rule: no sensor_gyro gap in the
  identified window or FRF unchanged without it), two keys.
- S38: first margin flights (CPU model vs SITL at Tb 0.1 and 0.3 s). S39: G2 verdict draft. S40: route check 40; G3 task spec.
Hard stops for S36-S40: no new anomaly entry unless it blocks a flown stage-2 verdict; any sim anomaly gets a bound in the same
session and moves on; if G1 FINAL is not written by end of S36, stop and escalate to the owner a second time with a B-option
cost (3-5 more sessions, no gate progress), not a repeat of Q4.
