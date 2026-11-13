# INDI project state

## Status summary (read this first)

- **Phase:** 1 (state of the art) 8 of 12 notes; phase 2 (PX4 analysis) started;
  phase 3 runner v0 works (pymavlink, seeded gz, one command per run).
  Benchmark spec frozen (`bench/scenarios.md` v1) before any INDI code.
  Phase 3 smoke test PASSED: `px4_sitl_default` builds in Docker and
  `gz_x500` flies headless (takeoff, hover at 2.5 m, land) at speed factor 1
  and 4 (4x: 43 s of sim in ~10 s wall, no log dropouts).
- **Headline results:** none yet. No controller code. Sim speed 4 is
  equivalent to speed 1 for attitude/rate metrics but NOT for hover position
  rms (0.027 vs 0.064 m): position scenarios run at speed 1 (DECISIONS D-speed).
- **Blocker:** none. Usage budget is the binding constraint.
- **Caveat on notes:** paper notes are from PDF text extraction; several
  equations are flagged as reconstructed. Check them against the PDFs before
  quoting in the report.
- **Last updated:** 2026-11-13, session 4.

## Phase checklist

| # | Phase | Status |
|---|-------|--------|
| 1 | State of the art (`research/`, report ch. 2-3) | in progress: reading list written, notes smeur2016, acquatella2017, blaha2024, wang2019, tal2021, impl_paparazzi, impl_px4_prior done; remaining: sieberling2010, steffensen2023, sun2022, smeur2018, impl_indiflight |
| 2 | PX4 analysis and design (`plan/`, report ch. 4-5) | not started |
| 3 | Simulation + benchmark harness on PID baseline (`docker/`, `bench/`) | image works, SITL build OK; gz_x500 headless smoke flight OK at speed 1 and 4 (`bench/smoke_gz.sh`); equivalence of results across speed factors not yet verified with metrics |
| 4 | Implementation (firmware + unit tests) | not started |
| 5 | Tuning and iteration | not started |
| 6 | Validation and report | not started |

## In progress

- Session 4 subagents: rate-path analysis DONE (`plan/px4_analysis_rate.md`,
  committed); integration analysis (`plan/px4_analysis_integration.md`) and
  note smeur2018 (`research/notes/smeur2018.md`) were running at the last
  save: if the files exist but are uncommitted, review and commit them.

## Next concrete actions

1. Phase 2: write `plan/architecture.md` from the two `plan/px4_analysis_*.md`
   files (orchestrator's own judgement, not delegated). Key facts: rate loop
   runs on vehicle_angular_velocity at IMU_GYRO_RATEMAX (400 Hz); angular
   accel = backward difference of LPF2p(40 Hz) gyro then AlphaFilter
   (IMU_DGYRO_CUTOFF 20 Hz, first order despite yaml saying Butterworth);
   torque setpoint normalised. To synchronise, filter the actuator/torque
   signal with the same NotchFilter/LowPassFilter2p/AlphaFilter chain.
2. Harness: find why hover position rms differs at speed 4; add the
   remaining scenarios of `bench/scenarios.md` to `bench/scenarios.py`
   (trajectory, wind/gust, payload, degraded motor, plant mismatch: these
   need simulator extensions in separate commits).
3. PID retuned baseline (documented tuning effort) before INDI flies.
4. Remaining phase-1 notes: sieberling2010 (fetch), steffensen2023 (PDF on
   disk), sun2022 (fetch), impl_indiflight (code on disk).
5. Budget lesson: two Sonnet code-reading agents (~30 tool calls each) cost
   about $1 together. Use at most one Sonnet agent per $3 session.

## Key findings so far (from notes, to verify before the report)

- With a fixed effectiveness, rate-loop INDI is algebraically an incremental
  PI(D) with gain 1/(G*Ts) (acquatella2017, eq. 29-30). Any INDI advantage
  over a well-tuned PID must come from effectiveness scaling, actuator-state
  feedback (true motor state vs commanded), saturation handling, or the
  acceleration feedback path: the benchmark must be designed to probe these.
- Paparazzi: same 2nd-order Butterworth on gyro and on modelled actuator
  state; first-order actuator model; WLS allocation with roll/pitch priority
  in the full version; no NaN checks, fixed dt (impl_paparazzi).
- wang2019: INDI's model-error perturbation is (B-B^)Δu, shrinking with
  sampling, vs (B-B^)u for NDI: "less sensitive", not model-independent.
  No transferable numeric bound for a multicopter rate loop.
- tal2021: outer loop is PD + INDI increments; motor speed from optical
  encoders, 2nd-order Butterworth 30 Hz on motor speed and IMU; no PID
  baseline in hardware. Without motor feedback a motor model is needed (our
  inference).
- Prior PX4 PR #25216 was closed by the stale bot; reviewers wanted a
  separate module and no changes to commander/ControlAllocator
  (impl_px4_prior).

## Known problems

- **Session 1 lost its work to a usage limit.** Five Sonnet subagents ran in
  parallel for about 14 minutes, took the 5-hour usage window from 11 % to
  101 %, and were all killed by HTTP 429 before writing anything to
  `research/`. They were too broad (100-140 tool calls each) and kept
  everything in context until the end. The prompt now asks for small tasks
  that write as they go.
- **Budget, measured:** one 5-hour window holds about $9 of model usage; that
  session used 6 % of the weekly window. Plan for a few hours of active agent
  time per week.
- **Raw material already on disk** (gitignored, moved from `/tmp`):
  `research/raw/` holds shallow clones of paparazzi, indiflight (+ support),
  crazyflie-firmware, ActiveSetCtlAlloc, lei-ss/indi, and partial PDF and text
  downloads in `foundations/`, `robustness/`, `papers_dl/`, `px4_eco/`. The
  folder names come from the killed agents; check contents before relying on
  them.

## Conventions (so a fresh session does not have to rediscover them)

- Commits: conventional format, no `-s` sign-off (the owner has not reviewed
  the work), trailer `Assisted-by: Claude:<model id of this session>` (the
  orchestrator now runs on `claude-opus-5-5`), no `Co-Authored-By`. Push with
  `git push origin feat/indi-control`.
- Everything that builds or simulates goes through `indi_project/docker/run.sh`.
- Containers started by this project are named `px4-indi-*`. The container
  `peaceful_bhabha` (image `px4io/px4-dev:v1.16.0-rc1-...`) belongs to the
  owner: never stop or remove it.
- The shell guard rejects any command containing the bare words `apt`, `dpkg`,
  `snap`, `halt`, `reboot`... even as grep patterns; phrase commands around that.
  It also rejects `gh auth`.
- `Tools/simulation/jmavsim/` and `nohup.out` are untracked files that predate
  the project: leave them alone and never `git add -A`.

## Ledger (rough)

| Session | Subagents spawned | Simulation runs | Notes |
|---------|-------------------|-----------------|-------|
| 1 (2026-11-13) | 5 (all killed by usage limit) | 0 | ~$10 spent, only the Docker image survived; host was also suspended 7 h |
| 2 (2026-11-13) | 5 (4 haiku, 1 sonnet), all completed | 1 SITL build, 4 smoke flights (2 OK) | ~$2.5 of $3 cap |
| 3 (2026-11-13) | 1 sonnet (runner v0), haiku notes | ~6 runner test flights | runner left uncommitted, committed in session 4 |
| 4 (2026-11-13) | 2 sonnet, 1 haiku | 18 runs (speed check), 0 failures | ~$3 cap |

## Journal

- 2026-11-13: session 1 started from scratch; created `STATE.md`, `DECISIONS.md`,
  Docker image `px4-indi-sim`. Cut off by the 5-hour usage limit at 08:13.
- 2026-11-13: owner review after session 1: supervisor now on Opus 5.5 with a
  per-session spend cap, max 3 concurrent subagents, host kept awake; prompt
  updated (small tasks, write as you go, bounded phase 1, early smoke test).
- 2026-11-13: session 2: committed Docker image files; SITL build OK in Docker; reading list; notes smeur2016, acquatella2017, impl_paparazzi, impl_px4_prior; smoke flight script `bench/smoke_gz.sh`; smoke flight OK at speed 1 and 4.
- 2026-11-13: session 3: froze `bench/scenarios.md` v1 (T1-T9 tuning, H1-H6 held-out, paired Wilcoxon acceptance); notes wang2019, tal2021.
- 2026-11-13: session 2 closed: note blaha2024 added (RLS effectiveness identification, no PID baseline in that paper).
- 2026-11-13: session 4: committed runner v0; speed-factor check (18 runs): speed 4 OK for attitude/rate, not for hover position; PX4 rate-path analysis.
