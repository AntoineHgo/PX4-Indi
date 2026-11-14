# Owner guidance after session 24 (2026-11-14)

The owner reviewed the project at the end of session 24 and took the decisions below. They override the
"finish the report, then DONE" plan in `STATE.md`. Decisions marked **O-n** are the owner's: record them in
`DECISIONS.md` as owner decisions (not orchestrator decisions) the first time you act on them, and do not
re-open them. Everything marked *advice* is the owner's technical view: follow it unless the data contradicts
it, and if it does, record why in `DECISIONS.md`.

## Owner decisions

- **O-1 Scope: stage 2 (v2 controller).** The project does not stop after the v1 report. `DONE` is written
  only when the stage-2 work below is complete, validated and reported (see the end of this file).
- **O-2 Close v1 first.** Finish the v1 report as a self-contained result before any stage-2 work: the open
  items in `STATE.md` (acquatella2017 l.11 check, ch. 2 [GAP] items stated as limitations, PDF image per
  D-pdf, conclusions review of ch. 8-10 against `results/`). Then record the closing commit hash in `STATE.md`
  as "v1 report closed". The v1 verdict ("INDI does not outperform PID") is never rewritten; later chapters
  add to it.
- **O-3 ACT_TC: identify, then re-check (labelled post-acceptance).** Identify the plant's actuator time
  constants (up and down separately) and delay from step data, as was done for G1. Re-fly the frozen v1 INDI
  with the identified value(s) on the tuning set and on H5 (10 seeds), labelled as post-acceptance
  characterisation. It never changes the v1 verdict.
- **O-4 G2: check the simulator, then identify.** Find out from source whether gz's MulticopterMotorModel
  transmits the rotor-acceleration reaction torque to the body (rotor link inertia + how rotor speed is
  imposed on the joint). If it does, identify G2_y from yaw steps and re-check as in O-3. If it does not,
  say so in the report: G2 cannot be evaluated in this simulator.
- **O-5 Actuator state from rotor speed.** The target hardware has ESCs with rotor-speed telemetry:
  **AM32 firmware with bidirectional DShot (eRPM)**. Stage 2 uses measured rotor speed as INDI's actuator
  state. The onboard first-order model stays as a fallback when telemetry is missing or stale.
- **O-6 Inversion on u = omega^2.** The owner's direction: take the actuator variable as u_i = omega_i^2,
  so the control effectiveness G (torque, and thrust if needed, per unit omega^2) is constant: it no longer
  depends on the thrust level, the battery voltage or the motor command curve (THR_MDL_FAC). Whether the
  increment is then computed in torque space (t_meas = G omega^2, increment through PX4's allocator) or in
  actuator space (delta omega^2 = G^+ (nu - a_f), own allocation) is **the orchestrator's decision**. Write
  it up in `DECISIONS.md` with the alternatives, before coding. Points to weigh:
  torque space keeps the allocator, prioritisation and airmode and changes little code, but the increment
  goes through the allocator's command mapping, which must be consistent with omega^2; actuator space is
  the literature form (Smeur, Tal & Karaman) but must reimplement saturation handling and prioritisation
  (Paparazzi WLS), which the prior PX4 PR reviewers objected to.
- **O-7 Validation of v2: both sets.** Freeze a **new held-out set** before v2 flies for the first time;
  it decides the v2 verdict, under the **unchanged** acceptance criteria of `bench/scenarios.md` section 6.
  H1-H6 are re-flown too and reported for continuity, explicitly labelled as "seen" scenarios (their v1
  results were known while v2 was designed).
- **O-8 Extra stage-2 scope.** In addition to O-3..O-6: (a) simulation realism, (b) hardware-readiness
  fixes from the control-law review, (c) outer-loop INDI combined with differential flatness as in
  Tal & Karaman (2020/2021, note `research/notes/` tal2021). Not in scope: thrust/voltage scaling of G1 or
  adaptive (RLS) effectiveness: O-6 makes G constant instead.
- **O-9 Outer-loop baseline = stock PX4 pipeline.** The outer-loop comparison is against the stock PX4
  position/trajectory pipeline (mc_pos_control with its own feedforward, attitude and rate PID). The
  flatness feedforward counts as part of the INDI design and is **not** given to the PID baseline. The
  report must say this plainly, and should separate, where cheap, how much of any gain comes from the
  feedforward and how much from the INDI feedback (e.g. one INDI ablation without the flatness terms).
- **O-10 Order of work: inner loop first.** Follow the order below. The outer loop starts only once
  the inner-loop v2 is validated.

## Order of work

1. **Close v1** (O-2). Cheap, about one session.
2. **Simulation realism** (O-8a). Separate simulator commits, applied identically to both controllers.
   Keep the v1 configuration reproducible (flag or model variant), because v1 results must stay
   re-flyable; v2 runs on the new configuration.
   - Real rotor speed out of gz: today `esc_status.esc_rpm` echoes the command. Publish the rotor joint
     velocity (e.g. through gz's JointStatePublisher or the motor model's own topic, read by GZBridge)
     instead, so the telemetry reflects the simulated motor dynamics.
   - AM32 bidirectional-DShot eRPM model between the true rotor speed and PX4: frame rate tied to the
     DShot output rate, about one frame of latency, eRPM resolution (period encoding: coarser at high
     rpm), motor pole count, occasional dropped/CRC-failed frames. **Take every figure from the AM32
     source (github am32-firmware/AM32) and the DShot/Betaflight documentation, not from memory**, and
     record the values chosen in `DECISIONS.md` and `bench/sim_fidelity.md`. Check what PX4's DShot driver
     already provides for bidirectional DShot (`src/drivers/dshot`, esc_status) so the SITL path matches
     what the real driver publishes.
   - IMU: raise the gz IMU rate toward real-hardware rates (measure the lockstep cost first) and add
     vibration noise tied to rotor speed (blade-pass frequency), since a clean 250 Hz gyro flatters INDI's
     differentiated gyro (ch. 9).
   - After the sim change, re-fly the PID baseline (defaults, plus the PID tuning check with the same budget
     as v1) **before** any INDI v2 flight: the baseline numbers of v1 do not carry over to the new sim.
3. **Hardware-readiness fixes** (O-8b), one commit + regression test each, from
   `review/control_law_review_s16.md`: items 2 (dt jitter must not desynchronise t_f and a_f: redesign or
   reset both members of the pair consistently, or don't redesign on jitter inside a tolerance band),
   4 (stale saturation feedback; with measured omega it largely goes away, so check after O-5), 5 (keep
   the actuator state running while maybe_landed), 7 (fault path: hold the last valid state for a few
   cycles before a full reset), 9, 10, 11, 12, and the test gap of item 13 (dt jitter, landed/airborne
   transitions with moving torque, runtime parameter changes, fault recovery).
4. **Identification** (O-3, O-4) with the v1 re-checks, labelled post-acceptance.
5. **omega^2 inner loop** (O-5, O-6): design in `DECISIONS.md` first, then the library + tests, then
   module wiring, then flights. The measured omega^2 must go through the same filter chain as the gyro
   derivative, plus a delay that matches eRPM latency against gyro latency (identify it, do not tune it).
   eRPM loss detection and fallback to the model must be tested.
6. **Freeze the new held-out set** (O-7) before v2 flies: include scenarios aimed at the v1 weaknesses
   (plant motor tau x2 and asymmetric up/down, ESC latency, eRPM dropouts, vibration, battery sag) as well
   as the v1 strengths (gust, CoM shift, motor loss), plus the existing ones as "seen".
7. **Tune and validate inner v2**, same budget rules as v1 for both families.
8. **Outer-loop flatness INDI** (O-8c, O-9): read the tal2021 note and the paper sections on the
   flatness transform; write the design (inputs: trajectory to snap; check what `trajectory_setpoint`
   carries; thrust handling in omega^2 space) in `plan/` and `DECISIONS.md` before code; new trajectory
   scenarios frozen before it flies.

## Owner's technical review of v1 (advice; add to ch. 9 as "owner review" points)

- **ACT_TC was tuned, not identified.** The rule of D-g1-v1 ("model parameters are identified, then gains
  are tuned") was applied to G1 but not to MC_INDI_ACT_TC. The tuner settled at 0.0114 s, faster than the
  gz motor (0.0125 s up / 0.025 s down), i.e. already on the "plant slower than model" side that the
  review (s5) identifies as dangerous. The tuner most likely exploited the mismatch's band-pass gain boost
  as extra effective gain, which the frozen cost rewarded. H5 (plant tau x2) then pushed the
  mismatch to about 2-4x and gave the limit cycle. So the H5 loss partly reflects the tuning methodology,
  not only INDI. Lesson for v2: G, ACT_TC, delays and G2 are never in a tuning space.
- **G2 was never identified** although `plan/architecture.md` sec. 6 said it should be; this may be part of
  why yaw only reaches parity with PID.
- **Actuator model limits:** up/down asymmetry not modelled, and effectiveness in normalised torque
  depends on thrust level and command curve. Both disappear with measured omega and u = omega^2 (O-5, O-6).
- **Sim gyro is optimistic** (250 Hz, white noise, no vibration): already in ch. 9; stage 2 tests it (step 2).

## Budget

Stage 2 is large compared with the remaining budget. Keep the v1 rules: small subagent tasks that write as
they go, CPU over tokens, and a STATE update before every long operation. If the budget clearly cannot cover
step 8, finish and report steps 1-7 as a complete inner-loop v2 and leave step 8 as designed but not flown.
Record that as a decision rather than stopping silently.

## Definition of DONE (replaces the v1 condition)

Create `indi_project/DONE` only when: v1 report closed (O-2); v2 inner loop implemented, validated on the
new held-out set, and reported; the outer-loop flatness INDI implemented, validated against the stock
pipeline and reported (or, if the budget forced it, explicitly recorded as designed-not-flown per the Budget
section); and `STATE.md` has a final summary.
