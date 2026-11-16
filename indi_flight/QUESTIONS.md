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

**Meanwhile.** I continue with the player (take-off/land kinds, anchoring on the logged transition) and G1.5.
Not blocked. G1.6 is not marked passed before you answer.
