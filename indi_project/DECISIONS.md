# Decision log

One entry per decision taken without the owner: what was chosen, what else was
considered, and why. Newest entries at the bottom. This log is the raw
material for the justifications in the report.

## D-001 Commit sign-off and attribution (2026-11-13)

- **Choice:** commit without `-s`; end each commit body with
  `Assisted-by: Claude:<model id of the session>` (session 1 ran on
  `claude-fable-5-2`, later sessions on `claude-opus-5-5`); no `Co-Authored-By`.
- **Alternatives:** `git commit -s` as the `commit` skill does by default.
- **Why:** the skill states that `-s` is the owner's DCO certification of
  changes they have reviewed and must never be applied to work they have not
  seen. This project runs unattended, so nothing here has been reviewed.
  `AGENTS.md` asks for the `Assisted-by:` trailer and forbids
  `Co-Authored-By` naming an AI. The owner can add the sign-off when
  reviewing (e.g. `git rebase --signoff`) before any upstream submission.

## D-002 Docker image contents (2026-11-13)

- **Choice:** `indi_project/docker/Dockerfile` is `ubuntu:24.04` +
  `Tools/setup/ubuntu.sh --no-nuttx` (Gazebo Harmonic included), built with
  `Tools/setup` as context so the repository's own requirement files
  (`requirements.txt`, `test-requirements.txt` with MAVSDK and pytest) are
  installed by the same script the project uses. Extras: `scipy`, Xvfb/Mesa.
- **Alternatives:** (a) extend the stock `px4io/px4-dev` image: rejected, the
  local tag is old (v1.16) and adding Gazebo on top duplicates what
  `ubuntu.sh` already does; (b) include the NuttX toolchain: rejected for
  now, it adds gigabytes and the project validates in SITL. A NuttX compile
  check can use the stock `px4io/px4-dev` image later.
- **Why:** the mission asks to reuse the repository tooling with simulation
  tools included; `--no-nuttx` keeps the image small.

## D-003 Docker run wrapper (2026-11-13)

- **Choice:** `indi_project/docker/run.sh` derives the repository path from
  its own location (as `Tools/docker_run.sh` does), mounts only the repository
  at its own path and `~/.ccache`, runs as the host uid/gid, uses `--rm`,
  `--init`, a container name prefixed `px4-indi-`, an in-container
  wall-clock `timeout`, and no TTY. No ports are published.
- **Alternatives:** hard-coding the absolute repository path in the script:
  rejected, it would make the benchmark irreproducible on another machine.
- **Why:** matches the constraints in the mission; a predictable name prefix
  lets a cleanup step stop only this project's containers.

## D-004 Phase 1 scope (2026-11-13)

- **Choice:** a bounded reading list (`research/reading_list.md`) of 8 core
  papers, one background paper (Acquatella 2017, INDI-PID equivalence) and
  three reference implementations (Paparazzi, indiflight, prior PX4 work).
  One note per source in `research/notes/`, written by one small subagent.
- **Alternatives:** an exhaustive survey: rejected, session 1 lost its whole
  budget to five broad agents. Skipping the PID-equivalence paper: rejected,
  without it the INDI-vs-PID comparison cannot be interpreted.
- **Why:** budget is the binding constraint; sources are added only when the
  design or a result needs them.

## D-005 Harness disables GCS/RC-loss failsafes (2026-11-13)

- **Choice:** the SITL harness sets `NAV_DLL_ACT=0`, `COM_RC_IN_MODE=4`,
  `COM_RCL_EXCEPT=4` after boot, for every controller and every run.
- **Alternatives:** connecting a MAVSDK GCS and a virtual RC: heavier, and it
  changes nothing in the inner loops under test.
- **Why:** with no GCS heartbeat the arming check "No connection to the GCS"
  blocks takeoff. The change concerns failsafes only and is identical for
  INDI and PID, so it cannot bias the comparison.

## D-session3-1: benchmark acceptance criteria and fairness rule (2026-11-13)

- **Choice:** `bench/scenarios.md` v1, frozen before INDI exists: tuning set T1-T9,
  held-out set H1-H6, paired Wilcoxon over 10 seeds, "outperforms" means >= 10 %
  significant improvement on 4 of 6 held-out scenarios against a retuned PID,
  no failure, no significant >10 % loss, hover effort <= 1.5x.
- **Alternatives:** compare against PX4 defaults only (rejected: weak baseline);
  compare on mean metrics without statistics (rejected: seed noise could decide
  the outcome); tune each controller by hand (rejected: unequal effort is the
  classic way to bias such comparisons).
- **Why:** with fixed effectiveness INDI is an incremental PI(D)
  (acquatella2017), so a nominal-plant comparison mostly measures tuning. The
  scenarios target the mechanisms where INDI can differ (acceleration feedback,
  plant change, actuator state, saturation), and equal tuning budgets plus a
  held-out set keep the comparison honest.

## D-speed: simulation speed factor (session 4, 2026-11-13)

**Data:** `results/speedcheck_pid_default.md` (PID default, seeds 1-3, speed 1 vs 4).
Attitude-step and rate-step metrics (rate rms, attitude rms, rise time,
overshoot, motor effort) agree within the seed-to-seed spread. Hover
position rms does not: 0.027 m (0.021-0.033) at speed 1 vs 0.064 m
(0.038-0.104) at speed 4.
**Decision:** run attitude and rate scenarios at speed 4; run any scenario
whose metric is position (hover, trajectory tracking, wind/gust position
deviation) at speed 1 until the hover discrepancy is explained.
**Alternatives:** speed 1 everywhere (4x the CPU time, safe); speed 4
everywhere (rejected: measurably changes position-hold results).
**Open:** cause not yet found (candidates: MAVLink setpoint stream timing
at speed 4, EKF/sensor timing). To investigate before position scenarios.

## D-arch-1..6: stage-1 INDI architecture (session 5, 2026-11-13)

Full design and rationale in `plan/architecture.md`; summary here.
- **D-arch-1 Torque space ahead of the allocator.** INDI outputs the normal
  `vehicle_torque_setpoint`. Rejected: actuator-space increments (needs a new
  allocator input or bypassing it, loses prioritisation and airmode; prior
  PR #25216 reviewers asked for no allocator changes).
- **D-arch-2 Selection inside `mc_rate_control`.** Enum `MC_RATE_CTL_TYPE`
  (0 PID default, 1 INDI), latched while disarmed; INDI law in a new library
  beside the untouched PID library. Rejected: separate module selected at
  startup (duplicates acro setpoints, thrust/battery handling, status; two
  torque publishers hazard); external-mode pattern of mc_nn_control/mc_raptor
  (bypasses allocator and standard modes).
- **D-arch-3 Actuator state from a first-order torque-space model** fed by
  the allocated torque (setpoint minus `unallocated_torque`). Rejected for
  stage 1: ESC feedback (gz echoes the command), per-motor model (needs a
  copy of the allocator's unpublished normalisation). Trigger to upgrade:
  benchmark shows motor-asymmetry or saturation limits performance.
- **D-arch-4 Synchronisation** by applying LPF2p(IMU_GYRO_CUTOFF) then
  AlphaFilter(IMU_DGYRO_CUTOFF) to the modelled torque, plus an optional
  integer delay. Shared IMU filter params left at defaults unless tuning
  needs otherwise, in which case the retuned PID gets the same freedom.
- **D-arch-5 Fixed per-axis effectiveness G1 (and G2 for yaw)** identified
  from SITL steps. Adaptive effectiveness deferred to after stage 1.
- **D-arch-6 Safety:** no accumulator (windup-free by construction), state
  reset when disarmed, t_f held at 0 when landed, non-finite inputs reset the
  law and output zero increment, static memory only.

## D-g1-v1: G1 from in-loop identification (session 7, 2026-11-14)

- G1 roll = pitch = 241 (mean of the in-loop fits 237 / 245, R^2 0.94-0.95),
  G1 yaw = 7.4 (fits 7.2-7.6 across increment spans). Source:
  `results/sync_check_v0.md`. Parameter overlay `bench/params/indi_v1.params`.
- Alternative rejected: the session-5 open-loop fit on PID logs (321 / 211),
  which disagreed between two axes of a symmetric vehicle and fitted worse.
- One common roll/pitch value because the vehicle is symmetric and the two
  fits differ by 3 %, less than their seed-to-seed uncertainty is likely to be
  (not yet measured: re-fit on seeds 2-3 during the T-set tuning runs).
- G1 is not a tuning variable: it is identified, then K, ACT_TC and the
  attitude P gains are tuned. G2 (yaw rotor inertia) stays at its default; it
  is not identifiable from the yaw step data.

## D-yawfilt: INDI-only yaw low-pass applied to both feedback paths (session 7, 2026-11-14)

Problem: the yaw a_f noise reaches the yaw torque with gain 1/G1_Y; with the
small identified G1_Y (7.4) this is 4x the v0 noise, which already made INDI's
hover motor-rate effort 8x PID's (`results/sync_check_v0.md` sec. 3).

- **Chosen:** an extra second-order low-pass on the yaw axis inside the INDI
  law, `MC_INDI_YAW_CUT` (Hz, 0 = off), applied identically to a_f,yaw and to
  t_f,yaw, so the synchronisation of D-arch-4 holds. It costs yaw phase lag
  only; yaw bandwidth is low anyway (drag-torque limited). The cutoff enters
  the INDI tuning space. For fairness `MC_YAW_TQ_CUTOFF`, PID's yaw output
  filter, enters the PID tuning space.
- Rejected: inflating G1_Y above the identified value (this is what v0 did by
  accident): it detunes the cancellation and hides the model in a gain.
- Rejected: lowering `IMU_DGYRO_CUTOFF`: shared with PID's D term and with all
  axes; roll/pitch noise is already at PID's level.
- Rejected: reusing `MC_YAW_TQ_CUTOFF` on the INDI output: filtering after the
  increment breaks synchronisation.
- Implementation: firmware change in the INDI law library + unit test, then
  rebuild, before INDI tuning starts. PID tuning can start before it.

## D-indi-r1 (2026-11-14, session 8): INDI tuning round 1 space

- Space = INDI gains K_R/K_P/K_Y, MC_INDI_ACT_TC, MC_INDI_YAW_CUT, attitude
  P gains; base params `bench/params/indi_v1.params` (in-loop G1), same
  budget as PID r1 (24 candidates, seeds 1 2, same scenarios and cost).
- MC_INDI_YAW_CUT center 10 Hz (`bench/params/indi_r1_center.json`), span 2
  (5-20 Hz). Its firmware default stays 0 (disabled) so the parameter does
  not change behaviour by itself; log-space sampling cannot be centred on 0.
- Alternative rejected: leaving the yaw cutoff out of the space and fixing it
  at 10 Hz. Rejected because the PID space includes its yaw torque cutoff
  (MC_YAW_TQ_CUTOFF), so equal treatment means both families tune theirs.

## D-r2 (2026-11-14, session 9): tuning round 2 for both families

- Finding that motivates it (`results/effort_axes_s9.md`): after the 10 Hz
  yaw cutoff, INDI hover yaw torque setpoint still has 9x PID's standard
  deviation and its sample-to-sample change is the largest of the three
  axes; roll/pitch torque activity is only ~2x PID's. PID's default
  `MC_YAW_TQ_CUTOFF` is 2 Hz, so the two families did not filter yaw
  comparably in round 1 (INDI box 5-20 Hz).
- PID r2: center = PX4 defaults (r1 winner c00), span 1.5.
- INDI r2: center = r1 winner c07, except MC_INDI_YAW_CUT centered at 3.5 Hz
  so the box (2.3-5.3 Hz) reaches PID's 2 Hz yaw filtering; span 1.5.
- Both: 16 candidates, seeds 1 2 3 (3 instead of 2 to average the
  non-repeatable hover position RMS, see `pid_r1.md` follow-up), same 5
  tuning scenarios and frozen cost: 240 flights per family, as in r1.
- Rejected: span 1.3 (prompt-level suggestion of session 8): with the r1
  winner at the edge of the yaw box, 1.3 would not reach 2-3 Hz.
- Rejected: more candidates rather than more seeds: r1 showed ~2 % re-fly
  noise on J and up to 2.2x on single hover runs, so seed noise, not
  sampling density, limits the ranking.

## D-hover-noise (2026-11-14, session 9): non-repeatable hover runs

- Fact: the same seed re-flown gives hover position RMS up to ~2x apart
  (`pid_r1.md` follow-up); attitude/rate step metrics re-fly within ~2 %.
- Decision: treat hover position RMS as a noisy metric and average it
  over seeds (3 in tuning round 2, >= 8 in the final benchmark, paired
  Wilcoxon as in `bench/scenarios.md`), instead of first hunting the source
  of non-determinism. The likely source is thread scheduling between the
  PX4 and Gazebo processes in lockstep, which the seed does not control;
  removing it would be a simulator change of uncertain cost, while extra
  seeds cost only CPU.
- Consequence for the report: hover results are reported as distributions
  across seeds, and the simulation-limits section states that a seed does
  not reproduce a hover run exactly.
- Revisit if, with >= 8 seeds, the hover spread still hides the
  INDI-PID difference.

## D-dist: disturbances via a runtime ApplyLinkWrench wrench driven in sim time (session 10, 2026-11-14)

- Context: T6/T7 (and H2/H3) need wind, gust and payload disturbances that
  the stock gz_x500 setup lacks. The image has gz-sim 8.15 with the
  ApplyLinkWrench, WindEffects and DetachableJoint systems and Python
  gz-transport bindings.
- Decision: apply a persistent external wrench on the x500 base_link from a
  Python injector that follows the gz clock, with the profile defined in
  sim time and logged to CSV. Wind is a quasi-steady drag force
  F = 0.5 rho CdA v|v| acting 5 cm above the CoM; payload is a downward
  force step. Spec: `plan/disturbance_spec.md`.
- Alternatives rejected: (1) WindEffects system: its force model is a
  crude per-link linear scaling, it cannot apply a torque through a centre
  of pressure, and the gust timing through its topic is no more precise;
  (2) DetachableJoint payload: only detaches, so it models a payload drop,
  not an addition; (3) a PX4-side disturbance module: would touch flight
  code for a test concern. (4) Editing the stock world files: would change
  the environment under a running tuning batch.
- Limitations for the report: drag ignores vehicle velocity and rotor
  inflow effects; the payload adds weight but not inertial mass.

## D-yawnu: YAW_CUT also filters the yaw rate fed back in nu (session 11, 2026-11-14)

Evidence: `results/tuning/r2f_yc2.md`. With a_f,yaw and t_f,yaw filtered at
PID's 2 Hz, INDI hover motor-rate effort is still ~2.1x PID's; the chatter is
the gyro noise in nu_yaw = K_Y (r_sp - r), gain K_Y/G1_Y ~ 0.8.

- **Chosen:** when `MC_INDI_YAW_CUT` > 0, the yaw rate used in nu goes
  through a third low-pass instance with the same cut-off (setpoint not
  filtered). One knob then sets the yaw-axis noise bandwidth for every
  feedback path of the yaw increment, as `MC_YAW_TQ_CUTOFF` does for PID's
  whole yaw output. YAW_CUT = 0 stays bit-identical to the current code.
  r1/r2 results were obtained with the old semantics; the round that uses
  the new one must say so.
- Rejected: filtering the whole yaw increment (output) — this adds lag in
  series with the actuator, which INDI's increment form assumes is captured
  by t_f only, and breaks the a_f/t_f synchronisation of D-arch-4.
- Rejected: only shrinking K_Y — the tuner already had K_Y in its space
  (span 1.5 around 7.1) and settled at 5.8; lower K_Y trades away the yaw
  tracking that is INDI's measured advantage.
- Rejected: a separate parameter — enlarges the tuning space for one knob
  whose physical meaning (yaw noise bandwidth) is the same.

## D-r3 (2026-11-14, session 12): INDI round 3 centred at lower yaw gains

- Evidence (`bench/yaw_step_effort.py` on step_yaw seed 1, r2f_yawnu c00 vs PID r2 c00): on each 45 deg yaw
  step the INDI setpoint term K_Y*r_sp/G1_Y peaks at 2.75 normalised torque (r_sp 3.49 rad/s, clipped by the
  yaw rate limit), so the yaw torque saturates at 1.0; PID peaks at 0.33. Motor-rate RMS along the yaw
  allocation direction over [-0.2, +2] s: INDI 11.1 vs PID 1.55 (7x). The unfiltered setpoint path is the
  cause, confirmed. The INDI yaw rate loop crosses over near K_Y = 5.8 rad/s, PID's near P*G1_Y = 0.2*7.4
  = 1.5 rad/s: INDI was tuned about 4x faster in yaw.
- Choice: round 3 centred at K_Y 3.0, YAW_P 4.0 (other gains c11, YAW_CUT 2), span 1.5: K_Y in [2, 4.5],
  YAW_P in [2.7, 6]. The r2 tuner settled at K_Y 5.8 when hover effort dominated the cost; with D-yawnu that
  penalty is gone, so the yaw trade-off has to be explored again in a region r2 never sampled.
- Rejected: a yaw setpoint pre-filter in INDI only (unfair to PID; if adopted it must be offered to both).
- Rejected: wider span for all parameters (roll/pitch are already near their r2 optimum; one shared span).
- A first r3 launch centred at c11 (K_Y 5.8) was stopped after a few minutes and its output deleted.

## D-yawsp (2026-11-14, session 13): YAW_CUT filters the yaw rate error, setpoint included

Context: after r3 (`results/tuning/r3.md`), the only INDI penalty left under the frozen cost is step_yaw motor-rate
effort (~5x PID). Cause measured: the yaw setpoint step passes unfiltered through K_Y r_sp / G1_Y into the torque
increment; PID smooths the same step with its default 2 Hz yaw torque output filter (MC_YAW_TQ_CUTOFF), which
acts on its whole yaw command.
Choice: nu_yaw = K_Y * lpf(rate_sp - rate) with the YAW_CUT design (firmware 99634a6b71). It gives INDI the same
structure the PID baseline already has by default, so it is not an advantage offered only to INDI.
Alternatives rejected: (a) a separate yaw setpoint pre-filter parameter: one more parameter for the same effect;
(b) changing the effort metric or its weight: the cost is frozen (scenarios.md v1) and changing it after seeing
INDI lose would be after-the-fact selection; (c) lowering K_Y further: r3 already shows yaw tracking degrading
while the step in torque remains (proportional to K_Y).
Cost: added lag on the yaw setpoint path, expected to lower yaw step tracking somewhat (as for PID).

## D-r4 (2026-11-14, session 13): yaw-only round under D-yawsp

After D-yawsp, c13's yaw tracking dropped to 1.056 x PID while step_yaw effort fell to 1.42 x (penalty threshold
1.25). Roll/pitch gains are settled (r3) and decoupled from yaw, so r4 varies only MC_INDI_K_Y, MC_INDI_YAW_CUT and
MC_YAW_P (span 2 around c13, 12 candidates, `tune.py --vary`, added for this) on step_yaw and hover, seeds 1-3.
Selection rule fixed before seeing results: best step_yaw cost (ratio + effort penalty, the frozen per-run cost)
averaged over seeds; hover is only a sanity check (D-hovernoise, `results/tuning/r3f_yawsp.md`). The chosen yaw
set then replaces c13's yaw values, and the combined candidate is re-scored on all 5 tuning scenarios.
Alternative rejected: a full 8-parameter round (240 flights) to tune 3 parameters.

## D-hovernoise (2026-11-14, session 13): hover term of J is noise-dominated

Hover 3-D RMS is driven by sporadic vertical excursions, present for PID and INDI alike; horizontal RMS is tight and
equal (`results/tuning/r3f_yawsp.md`). The frozen tuning cost is kept unchanged. Consequences: J differences below
~0.1 are not treated as meaningful; the final benchmark uses more seeds and reports the horizontal/vertical split
alongside the frozen metric. Cause of the vertical excursions is open.

## D-freeze (2026-11-14, session 13): INDI tuned candidate frozen at r4f

INDI tuned = `results/tuning/indi/r4f/c00/params` (K_R 23.89, K_P 12.29, K_Y 2.118, ACT_TC 0.01142, YAW_CUT 1.572,
ROLL_P 6.275, PITCH_P 6.185, YAW_P 3.308; G1 241/241/7.4). Tuning-set J 0.978 vs PID defaults 0.96 (tie within
noise). Four INDI rounds (r1-r4, ~600 flights) plus three structural fixes (D-yawfilt, D-yawnu, D-yawsp); the last
two rounds moved J by less than the hover noise, and the remaining INDI deficit (yaw) is explained (`r4.md`). This
meets the stopping rule "several iterations without improvement, with an explanation". The PID baseline stays at
PX4 defaults (r1+r2, 64 candidates, none better). Both frozen candidates now go to the held-out and disturbance
scenarios, which were not used for tuning.

## D-h5 (2026-11-14, session 15): held-out H1, H4, H5 flown exactly as frozen in scenarios.md

H5 "inertia x0.8" is applied to all three axes (T9 named Ixx, Iyy explicitly; H5 does not restrict, and a yaw
inertia change exercises the INDI yaw path too). H5 "run T2 + T4" becomes two scenarios with the same model variant,
reported separately. H1 (12.6 m/s^2 centripetal) and H4 (motor x0.6 under 6.6 m/s^2 path acceleration) turned out
to exceed what the airframe and the default position-controller limits allow; they are flown unchanged, because
softening a held-out scenario after seeing one result would be selection after the fact. Ground contact and
saturation time are reported as outcomes. Alternatives rejected: raising MPC_TILTMAX_AIR for H1 (changes the
baseline's outer loop, not the rate loop under test), reducing H4 to x0.7 (would merely repeat T8).

## D-accept (2026-11-14, session 15): acceptance criteria applied literally

The section-6 criteria are applied as frozen. H4 (both controllers crash) counts against criterion 1 even though PID
fails identically, and H5 (T2 + T4) is split so that the worse part (T4, rate pulses 1.58x) decides criterion 3.
Alternative rejected: averaging the two H5 parts or excluding H4 as infeasible, because both would be rule changes
after seeing the data; neither would change the outcome anyway (criterion 3 fails on H5 alone). Outcome: "INDI does not
outperform PID". The report states it plainly, with the disturbance-rejection gains and the actuator-mismatch weakness.
