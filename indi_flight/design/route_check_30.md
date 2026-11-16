# Route check 30 (sonnet, 2026-11-16, session 30)
Read: STATE, DECISIONS (heads + D-SCHED/D-A17/D-A14/D-EFFORT-BW), ANOMALIES, JOURNAL tail, GATES G1, route_check_27. No source, no logs.

## 1. Still on the shortest path?
No. 30 sessions in stage 1 (plan: far fewer); GATES.md:25 still says "no item is marked passed"; stages 2-7 have 0 sessions.
Route check 27 (rc27:34-54) items:
- 1 provisional G1 verdicts under Q2-A/Q3-A, B26 analysed: DONE for speed 4 (GATES:24-35), speed 1 not analysed (STATE:56).
- 2 G1.3/G1.4 for gate-bearing metrics only: DONE late, S28-S29 (T59, T61, T62; STATE:21-44). Still open: rate key used
  interpolation not ZOH (STATE:41-43), attitude key 15 % off + A-19 (STATE:43-44), step_metrics on the estimate (STATE:41).
- 3 G1.5 minimum injectors: NOT DONE (0 sessions; STATE:49 still lists "injectors" as pending).
- 4 freeze G1 at S30 and start stage 2: NOT DONE. 5 stage-3 task at S31: not reachable.
- "Do not open a new anomaly / read logs for a cause": broken. A-14 reopened S27 (ANOMALIES:21) and has now eaten S27, S28,
  S29, S30 (4 sessions vs the 2-session cap, STATE:139); A-19 opened S29 (ANOMALIES:25).
Cause of the slip: the session after rc27 went to A-14, not to the freeze list. A-14 is a real G1.6(c) finding (2/15 runs
fly the hover 2.3 m high), but the work done on it was a single fix attempted twice.

## 2. Which decision is the difficulty a consequence of?
Immediate: D-A14 (DECISIONS:148-163). It chose the SDF `reference_altitude` fix on a source claim never read (gz-sensors),
staged it, built `a14_close.sh` around it, and the pretest failed (STATE:26-30); S29 T60 showed the SDF cannot work
(DECISIONS: S29 overturn paragraph). Two sessions went on an unverified premise. The alternatives listed in D-A14
(EKF2_BARO_CTRL 0, player arm gate) cost one param line and were rejected for a G5 reason that is two stages away.
Root: D-SCHED (S23) + B26. D-SCHED bought sim-time exactness; B26 then re-flew 15 same-seed runs, which is what exposed A-14
and the two metric defects (EKF vs truth, effort bandwidth). The defects exist because metrics were ported in S7-S9 on the
EKF estimate while G1.2 (GATES:8) already said "tracking metrics read truth": the gate text and the code disagreed for 20 sessions.
Amplifier: ANOMALIES:3 "nothing is frozen with an open anomaly that touches it" turns every parked anomaly into a freeze blocker.
But GATES:12 G1.6(c) only asks "cause identified and its bound stated"; since S28 the A-14 cause is identified (STATE:15),
so GATES:34 ("cause not identified") is stale. A-14 needs a bound, not a finished fix, to freeze G1.

## 3. A fresh start on stage 1 would
- Run one sensor-consistency check in the very first pre-test flight (T13/T15, S9-S10): raw baro vs GNSS height, EKF z vs
  truth at arm. It would have found A-14 at S10; it was found at S19-S28.
- Make every metric read truth and ship with self-test + second key in one task (rc27:30-31 said so already).
- Write G1 as bounds (pass or written bound) and put the freeze at a fixed session; never let a gate name a cause.
- Build no gz-wide change (4 ms to 1.25 ms world, paused start, 800 Hz logs) before the sim was shown sane on one hover.
- Start stage 2 (CPU-only margins) in parallel at S4; it never depended on the simulator.

## 4. Minimal list to freeze G1 and start stage 2 (S30-S32)
S30 (now, one session, one agent each):
 a. T63 bridge baro fix + a14_close pretest. HARD STOP: if the pretest does not show raw pressure ~95.6 kPa in this session,
    set EKF2_BARO_CTRL 0 in the bench params (D-A14 fallback), note "baro failsafes untested until G5", and move on.
 b. Haiku, logs only, one task: rate key with ZOH (STATE:42-43), attitude 15 % gap and A-19 closing test on >= 5 B26 logs.
    If A-19 is not explained in that one task, attitude verdicts quote roll/pitch and yaw separately (ANOMALIES:25) and A-19 is
    parked with that bound. step_metrics: switch to truth if a one-line change, else tag "estimate, not gate-bearing".
S31:
 c. Re-fly the G1.6 set once on the fixed baro (hover/step_roll/traj x5, speed 4; speed 1 hover x5), detached, $0, <= 40 min
    wall, analysed with the existing `second_key_player.py` and `g16_spread.py`. Pass = 0 of 15 runs with EKF z error > 0.1 m.
 d. Write G1 FINAL in GATES.md: per item pass or bound; evidence-limit list = A-7, A-10, A-13, A-14, A-17, A-19; Q2-A, Q3-A
    recorded as owner-reviewable, not blocking. Replace GATES:34 stale text. Commit. Do not wait on the owner (rc27:23-24).
S31-S32: kick off stage 2 in parallel (CPU only: linear rate-loop model, blend margin, answers A-1); then the FRF/loop-gain
    injection run needs one player row kind, built then, with its own G1.5 test (frame, sign, magnitude 2 %, applied time) and
    the A-13 rule (ANOMALIES:20: identified windows contain no sensor_gyro gap, or FRF shown unchanged without them).
Deferrable to the stage that consumes it (list in GATES G1.5 as "built when its gate runs", note as owner Q4):
 - delayed GNSS, sag ramp, battery model, vibration, noise profiles, seeded drops, plant variants, rotor-inertia web check
   (J_rotor ASSUMED): G3. Disturbance/motor-fault/erpm-loss/thrust-sag hooks refused by --sched today: G3/G5.
 - errata re-score of archived set-O/T5, window rule for nav_state 23, land row, step_pitch/yaw, circle, pva propagation: tag
   "unverified" until a verdict reads them.
 - A-1 (stage 2), A-2/A-4/A-6 (stages 3-5), A-10/A-13 reopen triggers as written. G1.5 for G1: only the player's applied time
   (already exact, 0 us, GATES:31).
Do not: open another anomaly, add player kinds, or extend S30-S31. If the freeze is not written by end of S31, stop and escalate.
