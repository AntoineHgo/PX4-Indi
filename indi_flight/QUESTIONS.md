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
