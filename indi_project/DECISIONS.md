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
