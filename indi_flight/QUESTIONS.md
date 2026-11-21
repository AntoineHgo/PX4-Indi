# Questions to the owner

No open question (S50). Q1-Q4 closed, archived in JOURNAL.md.

N1 closed S61 (moved to JOURNAL.md; open items C2, C3 carried in STATE.md).

N2 closed S69 (summary in JOURNAL.md).

Q5 closed S70 (no owner objection to addendum 6; summary in JOURNAL.md).

Q6 closed S120 (owner answer B, conditions (i)-(v) in DECISIONS.md D-IDENT; full text in JOURNAL.md).

Owner directive 2026-11-20 (F-7/F-8/F-9) closed S134: acted on (DECISIONS D-F7-GROUND, GATES 5b, STATE
next actions); text in JOURNAL.md.

Q7 closed S140 (owner answer A: G5.7 validity at the 4 edges leaving posctl; written into GATES 5b; text in JOURNAL.md).

## Q8 (S143, 2026-11-20): G5 event injectors, G1.5 timing and two rows not injectable firmware-free. NOT blocking.
Context: S142 built bench/g5_events.py (one flight: EKF yaw/xy reset, RC/link/offboard loss, kill/re-arm), pre-test
in results/g5_events_s142/README.md. (a) Every MAVLink-side event is applied 3-24 ms after its commanded time: the
runner only acts on lockstep ticks of 10-20 ms. G1.5 asks "applied within 1 physics step (1.25 ms) of commanded and
logged as applied". The applied time IS logged by the firmware itself (kill flag, failsafe flags, EKF reset counters).
(b) G5.6 false maybe_landed and G5.11 EKF z reset cannot be produced without firmware: the land detector needs
ground contact, and the external-position reset in ekf2 is horizontal only.
Options (a): A [recommended] for discrete events (stream stop, kill, EKF reset command) the G1.5 timing check becomes
"applied time taken from the firmware's own log flag/counter, every G5 transient metric referenced to it, the
commanded-applied spread reported"; the 1-step rule stays for physics injectors (torque, wind, motor, eRPM). This
fixes a defect of the test (the rule exists so metrics start at the real event), it does not loosen a G5 limit.
B: build a sim-time event scheduler (gz plugin or firmware hook), about 2 sessions.
Options (b): A [recommended] SITL-only test parameter in the two INDI modules (not in stock modules, O-11 holds) that
forces maybe_landed into their own land input for 0.5 s; z reset: try an EKF2_HGT_REF switch in flight (param, no
firmware), else row "not tested" with this reason. B: mark G5.6 false maybe_landed and G5.11 z as not tested.
Meanwhile: fix the ekf_yaw and rc_loss injector defects and continue G5.5 (A18); event rows fly after G5.7/A18.
Q8 addendum (S144): yaw-reset and RC-loss injector defects fixed and keyed (results/g5_events_s144). With applied time
taken from the firmware log, command events are 1.75-4.25 ms after send (ekf_yaw 3.0 ms). For stream-stop events
(rc/link/offboard loss) the firmware has no "applied" instant other than the failsafe flag, which includes the
timeout; the G1.5 1-step check cannot apply there and those G1.5 FAIL lines are by construction, not evidence. The
G5.8 limit (failsafe <= 1 s after timeout) is checked as written. Option (a) A covers this; still not blocking.
Q8 addendum 2 (S146): G5.9 "motors 0 within one command period" referenced to manual_control_switches.kill_switch
measures 5.00 ms (FAIL vs 1.25 ms, fix_s2), all of it stock commander latency switch -> actuator_armed.kill; outputs
are 0 in the same sample as the kill flag (0.00 ms). Options: A [recommended] reference = actuator_armed.kill rise
(the instant the control stack is told; commander latency reported, O-11 forbids changing it); B keep the switch
reference: G5.9a FAIL recorded as a stock limit. Meanwhile: both numbers reported, row counted FAIL. Not blocking.
Q8 addendum 3 (S146): G5.8 definitions, two items, not blocking (results/g5_events_s146_move/README.md).
(i) "excursion <= 1 m" at 3 m/s: measured from the position at loss it includes the flight during the timeout
(4 s offboard timeout = 12 m) and the braking (3.4-3.5 m from 3 m/s, stock hold). Options: A [recommended] excursion
at 3 m/s = max horizontal deviation of ground truth from the position setpoint/trajectory the failsafe action
commands (what the controller controls), <= 1 m; hover keeps the current definition. B: drop the 3 m/s excursion.
(ii) link_loss "timeout": the firmware flags GCS loss COM_DL_LOSS_T after the last telemetry_status heartbeat flag,
which itself stays set about 2.25 s after the last GCS message (fix_s2: last message 75.35 s, entry 80.60 s; stock
mavlink/commander, O-11). Options: A [recommended] timeout reference = firmware's own flag (as now, S144 note), the
receiver window reported; B: reference = last message sent, row FAIL in both stacks (stock limit).
Meanwhile: G5.8 hover counted on the S144 definition with the 2.25 s window reported; 3 m/s rows not counted.

## Q9 (S147, 2026-11-21): G5.10 row after its first probe. NOT blocking.
Context (results/g5_g510_s147/README.md): scenario sat_sustained = 5 s at thrust scale 0.274 (2x hover) with the
row's 3 m position step, then a "full-scale aggressive manoeuvre". Seed 1: INDI alt loss 2.15 m (<= 2.0 FAIL), tilt
48.9 deg (<= 20 FAIL), back 4.3 s PASS; PID same flight 3.22 m, 44.7 deg, 5.9 s. (a) The 3 m step makes the stock
position loop command up to MPC_TILTMAX_AIR 45 deg, so "tilt <= 20 deg" fails for any controller: defect of the test.
(b) No position-mode manoeuvre saturates at full scale: 20-37 m steps peaked at 0.49 command (velocity/tilt limits).
Options (a): A [recommended] tilt limit = MPC_TILTMAX_AIR + 5 deg (no tilt beyond what the stack commands, overshoot
bounded); alt loss 2.0 m and recovery 5 s unchanged. B: keep 20 deg, drop the position step (saturation in hover only).
Options (b): A [recommended] full-scale part flown in stabilized: full throttle + full roll stick 1 s (inner loop at
full-scale saturation), limits as the row; B: drop the full-scale part.
Meanwhile: 3 seeds of the SAT part as is (counts against the current text), A-48 closing test. Not blocked.
Q9 note (S147, later): seeds 2/3 show the real G5.10 failure is INDI's tilt spike at the saturation EXIT (65 deg,
PID 33 deg), not the 20 deg text; (a) still applies to the SAT part. Cause search first (A-48), no answer needed for it.
Q9 note 2 (S149, results/g5_g510_s148/altloss_split.md, haiku log read, UNKEYED): the SAT part does NOT saturate:
motor command peaks 0.71, 0 % of time >= 0.99 in s1-s3 (THR_SC 0.274 leaves 2x hover thrust available). All 2.7 m alt
loss happens in the first 1.7 s after the thrust drop (collective ramps 0.14 -> 0.71 in ~1.5 s), none after REC.
So the row as flown measures the transient of an instantaneous 73 % thrust-effectiveness loss, not sustained
saturation. Proposal (c) A [recommended]: SAT part = scale chosen so hover needs >= 1.0 command (e.g. THR_SC <= hover
fraction) for 5 s with the limits as written, flown after a one-flight check that motors sit at >= 0.99; the 73 %
drop kept as a G3-type side probe, not a G5.10 pass condition. B: keep as is (row FAIL counted). Not blocking.
Q9 note 3 (S150): the 2.7 m loss is a controller limit, not a test defect: the D-GAP collective blend (TB 1.0 s,
bound 0.3 < the 0.36 gap) absorbs the drop too slowly (DECISIONS D-GAP-G510). Being fixed on the INDI side whatever
the answer to (c); (c) still decides whether the row also needs a truly saturating part.
Q9 note 4 (S151): with TB 0.3 + bound 0.5 the SAT part passes alt loss (1.74-1.76 m) and recovery (1.9-2.0 s) on 3
seeds (results/g5_g510_s151); only (a) tilt 45.3 deg = MPC_TILTMAX_AIR and (b)/(c) the non-saturating AGG/SAT
definition keep the row from PASS. Still not blocking.

Note S154 (RC154): the stage-6 freeze will proceed with option A assumed for Q8 (a)/(b)/add.2/add.3 and Q9 (a)/(c); an answer
B from the owner changes only the affected G5 rows, re-scored or re-flown after the freeze.

## Q10 (S157, 2026-11-21): G5.2 posctl z settle FAIL at the freeze is estimator height error. NOT blocking.
Update S157: seeds 2-3 posctl settle 0.36/0.35 s PASS; the FAIL is seed 1 only (5/6 runs PASS).
Context (results/g5_freeze_s157/README.md): freeze re-fly, typical noise, seed 1: G5.2 posctl z step settle 4.15 s
(limit 4.0 s, band 2 % of d = 0.039 m); overshoot and the x step pass. Truth vs estimate after release: the controller
holds the estimate on the setpoint within 0.02 m over the whole window, while EKF2 height error (est - truth) is
-0.078 m at release and decays to 0 over ~5 s; the truth "settle" is that decay. Stock ekf2 (O-11), not the INDI law.
At the sim-default noise (S138) the same row settled 1.2-3.0 s. Lesson 3: tracking on truth, estimator error separate.
Options: A [recommended] keep the truth metric and the limit; add a reference PID flight of the same seed (F-5): if PID
also fails, record the row as FAIL with cause "estimator height error > settle band", stack-independent, reported with
the est-truth trace; B (gate change after first test): settle band = max(2 % of d, 0.10 m) for z, justified by the
EKF height accuracy under the typical profile; C: settle measured on the estimate, truth error reported separately.
Meanwhile: the other rows continue; seeds 2-3 and one PID reference flight of this row are flown and scored as written.
Update S158: PID reference of the same seed PASSES (z settle 3.39 s, os 0.004 m). Option A therefore records the INDI
s1 FAIL as FAIL (1/6 runs), not as stack-independent. INDI holds the estimate on the setpoint; PID's slower z
response lets the EKF height error decay inside its own travel. Still not blocking; B or C only on your call.

## Q11 (S158, 2026-11-21): G5.5 o1-o4/o7 still FAIL at the freeze. Re-open outer-loop base A? NOT blocking.
Context (results/g5_freeze_s157/README.md, seed 1; seeds 2-3 flying): horizontal RMS vs the analytic trajectory
0.58-0.79 m (limit 0.5 m) on o1-o4/o7; vertical, o5/o6 and offb_vel_step PASS. Same as the probes (S139-S143). Cause
(route check 143, D-A18-SOURCE): the acceleration command a_c produced by the stock PositionControl vel/pos feedback in
base A (accel_only) lags the trajectory ~100 ms; the INDI stage and the plant add only 20-40 ms. A drag feed-forward
probe made it worse (rejected). PID on o1 (S139, older plant) 1.04 m: the row fails for both stacks. The fix is in the
architecture you confirmed (base A keeps stock PositionControl for the feedback), so I ask before touching it.
Options: A [recommended] record G5.5 o1-o4/o7 FAIL with data and cause, both stacks; G5 otherwise judged on its rows;
B: re-open base A for offboard trajectories only: INDI module's own pos/vel feedback with full flatness FF (estimated
2-3 sessions + re-freeze of G5); C: owner reviews the 0.5 m limit (gate change after first test, needs your call).
Meanwhile: seeds 2-3 and a PID o1 reference at the freeze plant are flown and scored as written.
Update S158: 3/3 seeds FAIL on each of o1-o4/o7 (0.57-0.81 m), o5/o6/offb_vel_step PASS 3/3; PID o1 s1 at the
freeze plant 0.785 m (also FAIL).

## Q12 (S160, 2026-11-21): G5.11 xy reset tilt limit fails for both stacks. NOT blocking.
Context (results/g5_freeze_s157/README.md, G5.11 row; exact test GATES 5b S160): a 1 m external-position reset
(MAV_CMD_EXTERNAL_POSITION_ESTIMATE) moves the estimate 1 m; EKF2 then fuses GNSS and returns it to truth in ~1 s, so
the position loop sees a 1 m transient error and commands 5.7-6.4 deg tilt (INDI, 3 seeds) and 7.82 deg (PID, seed 1)
against the row's 1 deg. Truth excursion 0.15-0.19 m (<= 0.5) and no oscillation in both stacks. The firmware-free
injector cannot produce a reset that the EKF keeps (stock ekf2, O-11).
Options: A [recommended] record G5.11 xy as FAIL, stack-independent (stock EKF/pos loop), truth excursion reported as
the controller-relevant number; B (gate change after first test): xy part judged on truth excursion and oscillation
only, the 1 deg limit kept for yaw (and z if injectable); C: drop the xy part (injector cannot make a persistent reset).
Meanwhile: yaw part (INDI-specific 1.8 deg spike, PID 0.48 deg) gets its cause search; xy counted FAIL as written.
Q12 addendum (S161): INDI yaw spike cause found and fixed (D-T10-RESET, results/g511_fix_s161/README.md): estimator
reset re-seeded a filter with one raw sample. After the fix the yaw event reads 1.08 deg on s1, inside INDI's own
no-event range of the same metric (0.72-1.10 deg; PID 0.48-0.86): the 1 deg limit is at INDI's hover tilt-command
noise floor under the typical profile. Option D [recommended, gate defect fix]: tilt jump measured as the event value
minus the 95th percentile of the same metric at no-event instants of the same flight (the row then measures the reset,
the noise is judged in G4). Meanwhile scored as written. Not blocking.

## Q13 (S164, 2026-11-21): G2 phase-plateau GM formula on bins with |L| > 1. NOT blocking.
Context (results/g2_plateau_s164.md): the G2 pass uses min(GM, plateau GM), plateau GM = min of 1/|L| over bins with
arg L within 10 deg of -180. First applied at the freeze (67 cells): 66 PASS; attitude pitch 800 Hz seed 2 gets
"-18.5 dB" from its 0.2 Hz bin, BELOW crossover, |L| = +18.5 dB, arg -170.9 deg (other seeds -158 to -165 deg there).
There 1/|L| is not a gain margin: the loop is stable with 18.5 dB of gain REDUCTION margin. Classic GM 20.2 dB, PM 54.1.
Options: A [recommended, test-defect fix] plateau GM over bins with |L| < 1; bins with |L| > 1 within 10 deg of -180 are
reported as gain-reduction margin 20log10|L| with the same >= 6 dB pass threshold (no threshold lowered); 67/67 PASS.
B: keep the literal formula: the cell FAILs G2.
Meanwhile: G2 work continues (model x-check, 267 Hz); both readings reported in GATES G2 freeze status.

## Q14 (S170, 2026-11-21): G4 command-chatter clause fails on a sub-DShot-step line in both stacks. NOT blocking.
Context (results/a54_s170/README.md): G4 "Additional" flags a 20-100 Hz line in actuator_motors at peak > 20 x median.
All G4 metric rows PASS 18/18 with >= 10x margin; the clause FAILS 3/3 typical/harsh on a 70 Hz line. Cause (one
session, A-54): the modelled rotor vibration (1P 159 Hz, blade-pass 476.5 Hz) folds through the stock 800 Hz IMU, 267 Hz
accel decimation and EKF2 stages into the command; PID carries the same line (78x) - INDI shows more (768x), probably because it
feeds acceleration back. Line RMS 2.5e-4 of full scale = half of one DShot step (1/2000); C20 23x under its limit. A
real FIFO-mean IMU attenuates the blade-pass alias only ~6 dB, so a hook change would not close the clause honestly.
Options: A [recommended, test-defect fix, lesson 6]: a line counts as chatter when peak > 20 x median AND its RMS
(+-2 Hz) >= one DShot step (5e-4 of full scale); ratio reported. B: keep the clause as written: G4 FAIL recorded,
stack-independent cause. C: change the vibration model (FIFO mean): line ~4x lower in power, still FAIL; not advised.
Meanwhile: G4 verdict written both ways; key2 of g3_checks.py; G3 preparation continues.
Q14 addendum (S170, later): the blind key2 of the checker (results/g4_gate_s169/g3_key2.md) flags the 20 x median rule
on every quiet and typical run too (22-39 Hz, command std 2.5e-4): the ratio alone flags a sloped background, not
only lines. This supports option A (absolute floor); being checked against key1 (A-55) before the G4 verdict.
Q14 addendum 2 (S170): the original checker (key1) run on all 9 runs agrees with key2: the clause flags 9/9 runs, quiet
included (22-39 Hz, windows from take-off), so as written it fails every profile (results/g4_gate_s169/a55_key1_all.md).
