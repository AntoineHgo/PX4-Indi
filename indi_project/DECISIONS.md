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
PX4 defaults (r1+r2, 40 candidates, none better; "64" in the first version of this entry was wrong, corrected session 17 from `results/tuning/pid/r{1,2}/summary.csv`). Both frozen candidates now go to the held-out and disturbance
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

## D-actsweep (session 17, 2026-11-14): post-acceptance ACT_TC robustness sweep

H5 showed that a plant motor time constant 2x the controller's MC_INDI_ACT_TC gives a 5-7 Hz roll limit cycle.
To map INDI's stability margin against this error, the frozen INDI candidate (r4f/c00) is flown on step_roll with
MC_INDI_ACT_TC scaled by f in {0.33, 0.5, 0.67, 1, 1.5, 2, 3} on the stock gz_x500 plant (plant/model ratio 1/f),
speed 4, seeds 1-3 (`results/act_tc_sweep_s17/`). Scaling the controller's assumption instead of the plant keeps the
inertia and mass unchanged and reuses the stock model; it is equivalent for the loop as long as only the ratio matters,
which is an assumption to state in the report. This is post-acceptance work: it never changes the verdict of
`results/acceptance_s15.md`, and it is reported as characterisation, not as a re-tune.

Outcome (session 17): the equivalence assumption above is falsified by the data. No limit cycle for f in 0.33-3,
whereas plant tau x2 with the stock model limit-cycles (H5 diagnostic). The report states the sweep as a test of
model error on a fast actuator only, and attributes the H5 instability to a slower physical actuator left unmodelled.

## D-landyaw (session 19, 2026-11-14): fix the landed yaw-filter bug after the freeze

The session-16 control-law review found that `resetStates()` zeroed the yaw filters on every landed /
maybe_landed cycle, so yaw control was scaled by ~0.005 on the ground and early in each takeoff when
MC_INDI_YAW_CUT > 0 (the frozen candidate uses it). Fixed in 1d776dc6dc (reset from the next input instead),
with a regression gtest that fails without the fix.

Alternatives: (a) leave the frozen firmware untouched and only document the bug; rejected, a known bug in a
deliverable that is meant to fly is not acceptable, and the fix is local. (b) re-fly the whole benchmark;
rejected for budget, since the bug only acts while landed/maybe_landed, i.e. before every metric window.
Chosen: fix, keep the frozen parameters, and check that the metric windows are unaffected by re-flying INDI on
step_diag (yaw commanded, speed 4) and com_shift (largest INDI gain, speed 1), seeds 1-3, against the committed
runs (`results/landyaw_check_s19/`). The verdict of `results/acceptance_s15.md` was obtained with the pre-fix
code and is reported as such.

## D-pdf (session 22, 2026-11-14): no PDF build yet

- Fact: neither the host nor `px4-indi-sim` has pandoc or LaTeX (checked with `which`).
- Choice: keep the report as Markdown chapters for now; add a PDF build only as a separate small image
  (e.g. `indi_project/docker/report.Dockerfile` with pandoc + texlive-xetex) once all chapters are final,
  so the simulation image stays unchanged and every benchmark result stays reproducible with it.
- Rejected: adding pandoc/LaTeX to `px4-indi-sim` (rebuild of the simulation image, ~1 GB, no benefit to results).

## D-noretune (session 23, 2026-11-14): the planned full-T re-tune is not run

- Fact: `bench/scenarios.md` v1.1 planned a re-tune of both controllers on the full T set (T1-T9) once T5-T9
  existed. It was never run: D-freeze froze both candidates on T1-T4 and the held-out set H1-H6 was then flown
  (sessions 14-15) and the acceptance decided (D-accept).
- Choice: do not run it now. Any re-tune after the held-out results are known would be tuned with knowledge of
  the held-out outcome (H5 actuator mismatch, H2/H3 disturbances), which the held-out rule exists to prevent; the
  acceptance verdict stays the one obtained with the T1-T4 tuning. The report states the omission as a limitation:
  neither controller was tuned on any disturbance scenario, so a PID with a retuned integrator might narrow the
  disturbance gap (ch. 9).
- Rejected: re-tuning both families on T1-T9 and re-flying H1-H6 (contaminated held-out set, and ~1000 flights of
  budget the project does not have).

## D-pdf-2 (session 26, 2026-11-14): PDF built and committed
Supersedes D-pdf. `docker/report.Dockerfile` (image px4-indi-report, pandoc + xelatex, report only) and
`docker/build_report.sh` build `report/report.pdf` from ch. 1-12. The PDF is committed so the owner can read it on
GitHub; it is rebuilt and recommitted whenever the report changes materially. Alternative (leave it untracked) rejected:
the owner follows progress from outside.

## D-t8-10 (session 26, 2026-11-14): T8 reported on 10 seeds
Seeds 4-10 of T8 had been flown in session 14 with the same firmware (empty `git diff 553c4dbdd0 c883907c92 -- src msg
ROMFS Tools`) and the frozen r4f/c00 parameters, but the report used seeds 1-3. The review s25 (item 1) flagged it.
Summarised all 10 (`results/t8_motor_loss_10seeds_s26.md`); the numbers match the 3-seed ones within seed spread, so
no conclusion changed, only the significance statement (p = 0.002 now available). Not a new experiment.

## Owner decisions O-1..O-10 (owner review 2026-11-14, after session 24)
These are the owner's decisions, not the orchestrator's; full text in `OWNER_GUIDANCE.md`; not re-opened.
- O-1 scope: stage 2 (v2 controller); DONE only per the owner's definition.
- O-2 close v1 first: acted on in session 26 (v1 report closed, see STATE.md).
- O-3 identify ACT_TC (up/down) and delay, re-check v1 post-acceptance (tuning set + H5, 10 seeds).
- O-4 check whether gz transmits rotor reaction torque; identify G2 if so, else state it cannot be evaluated.
- O-5 actuator state from measured rotor speed (AM32 bidirectional DShot eRPM), model as fallback.
- O-6 inversion on u = omega^2; torque vs actuator space is the orchestrator's decision, written before coding.
- O-7 new frozen held-out set decides v2 under unchanged criteria; H1-H6 re-flown as "seen".
- O-8 extra scope: sim realism, hardware-readiness fixes, outer-loop flatness INDI; no G scaling/RLS.
- O-9 outer-loop baseline = stock PX4 pipeline; flatness feedforward not given to PID; ablation where cheap.
- O-10 order: inner loop first.

## D-escfb (session 27, 2026-11-14): rotor speed telemetry in gz, behind a parameter and a bench flag

- Decision: GZBridge parameter `SIM_GZ_ESC_FB` (0 = echo command, v1 default; 1 = rotor joint speed in rpm from
  JointStatePublisher x rotorVelocitySlowdownSim 10). The JointStatePublisher is added by the bench to the per-run
  model copy (`model_variant.py` key `rpm`, `run_scenario.py --sim v2`), not to `Tools/simulation/gz/models/x500`.
- esc_status keeps being published from the command callback, i.e. once per motor output (the DShot frame rate on
  hardware); the joint callback only stores the latest speed. The eRPM model (rate, latency, quantisation, loss)
  will sit in that publish path.
- Alternatives rejected: a new `x500_rpm` model + airframe in Tools (more upstream files, does not compose with the
  T9/H5 model variants that already copy x500); publishing esc_status from the joint callback (rate tied to the
  physics step, not to the output rate as on hardware).
- Evidence: `results/s2_escfb_check.md`.

## D-erpm (session 27, 2026-11-14): eRPM telemetry model values

- Latency: one output period (the reply to frame k-1 is read at frame k: PX4 `DShot.cpp:98,169`, note
  `px4_bdshot.md`). AM32 rebuilds the reply once per DShot frame (`Src/main.c:1744-1756`, `am32_erpm.md` session 27);
  turnaround has no constant in AM32 (signal.c starts the reply from the DMA-complete interrupt): not modelled.
- Resolution: AM32 9-bit mantissa / 3-bit exponent period (us) and PX4's eRPM/100 rounding then integer division by
  pole pairs (`dshot.c:885-910`, `DShot.cpp:793`). Poles 14 (AM32 default `DroneCAN.c:343-347`, PX4 default
  `DShot.cpp:1026`).
- Drops: last good value held, error counter incremented (`dshot.c:676-700`). Rate: no primary source found;
  secondhand forum figures 0-0.3 % idle, 2-5 % under load, "1 % rule of thumb" (URLs in `am32_erpm.md`, search snippets
  only). Chosen: 1 % nominal for the v2 configuration, 5 % as a stress scenario in the new held-out set.
- Alternatives rejected: a Gaussian noise model on rpm (real error is deterministic quantisation plus holds); a
  latency of several frames (no source).

## D-imurate (session 28, 2026-11-14): v2 simulation runs the IMU and physics at 1000 Hz

- Choice: `--imu-rate 1000` (gz IMU update_rate and physics step 1 ms) for every stage-2 flight, both controllers.
  v1 stays re-flyable at the stock 250 Hz (`--sim v1`, default `--imu-rate 250`).
- Evidence (`results/s2_imu_rate.md`): rate control runs at 1 kHz (VehicleAngularVelocity publishes every sample under
  IMU_GYRO_RATEMAX 800); lockstep keeps up at speed 4 and with 6 parallel runs at speed 1; speed 2/4 step metrics stay
  inside the 6-seed spread at speed 1.
- Why: the owner review flags the clean 250 Hz gyro as flattering INDI's differentiated gyro, real flight controllers
  run the gyro at >= 1 kHz, and rotor vibration (1P ~ 120 Hz, blade-pass ~ 240 Hz at hover) aliases at 250 Hz sampling
  (Nyquist 125 Hz) but not at 1000 Hz, where it reaches PX4 as on hardware with the IMU's own anti-alias filter.
- Alternatives rejected: 500 Hz (no cost reason left to compromise); 2000+ Hz (beyond IMU_GYRO_RATEMAX default;
  untested lockstep cost). The logger subsamples at 3.5 ms, so analyses of logged INDI signals at 1 kHz see a subsample.
- Speed rule unchanged: attitude/rate scenarios may run at speed 4, position scenarios at speed 1 (D-speed).
