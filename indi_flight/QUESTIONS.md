# Questions to the owner

## Q2 (2026-11-16, session 24): G1.1 gap rule fails on holes in the simulator, not in the log. Amend? — OPEN, not blocking

**Question.** May I change the G1.1 gap rule after its first test, as below?

**Context.**
- G1.1 says: every declared topic logged at >= its rate, "max gap < 3 declared periods outside the start-up second".
- After the logger fixes of S16-S23, every controller-rate topic is logged at full rate (sim_ground_truth 56578 samples
  vs 56586 gyro samples, hover at speed 4).
- The rule still fails: max gap 5.0-6.3 ms (4-5 periods of 1.25 ms) on gyro, angular velocity, motors, torque setpoint,
  ESC, truth. All topics share the same few instants (7 gaps in 56586 samples, 0.016 %), and the gaps are already in
  `sensor_gyro` and in the truth stream published by gz_bridge: the simulator skipped those steps (A-13, parked S23).
- So the rule measures the simulator, while G1.1 is about logging what the analysis needs. I count this as a defect
  in the test. But the mission says any gate change after its first test goes to you.

**Options.**
- A (recommended): split the rule. (i) Logger completeness: every sample the source published is in the log, checked
  against the source count (gyro/truth), at most 0.1 % missing. (ii) Simulator holes get their own row with a bound:
  <= 0.05 % of steps, single holes <= 10 ms. Every analysis that needs a continuous signal (G2 frequency response,
  spectral detector) must leave out windows that contain a hole, or show its result does not change when they are
  left out (already the A-13 reopen trigger).
- B: keep the rule and remove the simulator holes first (cause in gz at speed 4 not found yet; 1-3 sessions of
  simulator work with no gate gain).
- C: keep the rule as it is. G1 stays failed until B is done.

**Meanwhile.** I continue with the scenario player (G1.6a) and G1.5. Not blocked. I will not mark G1.1 as passed
before you answer.

## Q3 (2026-11-16, session 25): G1.6(a) mode instants cannot meet 2.5 ms without lockstep gz. Restate? — OPEN, not blocking

**Question.** May I restate G1.6(a) after its first test, as below, or do you want lockstep gz first?

**Context.**
- G1.6(a): PX4 mode transitions within 2 IMU periods (2.5 ms) across same-seed runs.
- The sim-time player (S24) applies arm/offboard triggers at the exact same sim time in every run (spread 0 us, two keys).
- PX4's response still spreads 5-9 ms: Commander (zero diff, O-11) acts on its next 10 ms tick, skips its sleep
  while a command is pending, and sleeps relative to the end of its own work. gz runs free of PX4, so that work's
  wall time becomes a random sim-time shift (1.25 ms steps). Starting gz paused (S25) did not change it.
- Only a gz-PX4 lockstep (gz waits for PX4 each step) removes it: new sim plugin, est. 1-3 sessions, no gate gain
  except G1.6(a); it would also tighten G1.6(b).

**Options.**
- A (recommended): (a) becomes (a1) triggers applied at the same sim time across runs, within 1 IMU period; (a2)
  PX4's response within one Commander period (10 ms) of the trigger, logged; plus the player anchors every
  scenario row after a mode change on the logged transition, so the controller sees the same scenario. (b)-(d)
  unchanged: any spread the residual causes still counts against verdicts.
- B: build lockstep gz first, keep (a) as written.
- C: keep (a); G1.6 stays failed.

**Addendum S27 (B26 speed 4, 15 runs):** triggers exact (0 or +1 IMU tick). PX4 response spread 6.25-8.75 ms, but the
offboard latency is 11.25-20 ms (1-2 Commander ticks), so option A's (a2) would read "response spread within one
Commander period, latency within two". Provisional verdicts under A are in GATES.md (not marked passed).

**Meanwhile.** I continue with the player (take-off/land kinds, anchoring on the logged transition) and G1.5.
Not blocked. G1.6 is not marked passed before you answer.

## Q4 (2026-11-16, session 32): G1 not frozen after 32 sessions. Freeze it with stated evidence limits and start stage 2? — OPEN, not blocking

**Question.** May I freeze G1 now with the limits below written into GATES.md as evidence limits, and start stage 2
(loop-gain injection, margins), or must G1 pass in full before any stage-2 result is used?

**Context.**
- Done with two keys: logging at full controller rate (G1.1 except Q2), truth topic stamped in sim time (G1.2),
  metrics on truth with second keys (G1.3), self-tests break-checked (G1.4), sim-time scenario player (G1.6a1).
- A-14 (baro step, 2.3 m wrong take-off height in 2/15 same-seed runs) fixed in the simulator: spread 2.3 -> 0.13 m.
- Open limits: Q2 (sim step holes), Q3 (Commander 10 ms tick), A-14 parked at 0.15 m EKF-truth z, A-19 EKF heading
  error 0.6-1.5 deg varying under one seed (yaw on truth carries it), G1.5 injectors/variants not built yet (route
  check 30 deferred them to G3/G5, where they are first needed).
- Every further stage-1 session has gone into simulator anomalies with no gate progress (route check 30).

**Options.**
- A (recommended): freeze G1 with these limits listed; G1.5 is re-opened per injector when G3/G5 builds it (each
  injector gets its G1.5 check before its first campaign); yaw verdicts quote the estimate-based yaw plus the EKF
  heading error separately until A-19 is explained. Start stage 2 in S33.
- B: keep stage 1 until G1.5 and A-19 pass (estimate 3-5 sessions), then stage 2.

**Meanwhile.** S33 analyses the speed-1 re-fly, A-19's mechanism (one haiku task), and prepares the stage-2
injection design without using its results for a verdict. Not blocked.
