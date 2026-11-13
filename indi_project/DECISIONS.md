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
