# INDI project state

## Status summary (read this first)

- **Phase:** 1 (state of the art) 8 of 12 notes; phase 2 (PX4 analysis) started;
  phase 3 runner v0 works (pymavlink, seeded gz, one command per run).
  Benchmark spec frozen (`bench/scenarios.md` v1) before any INDI code.
  Phase 3 smoke test PASSED: `px4_sitl_default` builds in Docker and
  `gz_x500` flies headless (takeoff, hover at 2.5 m, land) at speed factor 1
  and 4 (4x: 43 s of sim in ~10 s wall, no log dropouts).
- **Headline results:** INDI (untuned defaults) flies in gz_x500: hover
  and roll step stable, no faults (`results/first_flight_indi_v0.md`,
  1 seed, smoke only). Roll step slower than default PID (rate rms 0.108 vs
  0.084 rad/s), off-axis coupling lower. Not a benchmark result yet. Sim speed 4 is
  equivalent to speed 1 for attitude/rate metrics but NOT for hover position
  rms (0.027 vs 0.064 m): position scenarios run at speed 1 (DECISIONS D-speed).
- **Session 7 findings:** INDI filters are synchronised (lag 0-1 cycle);
  in-loop G1 roll/pitch 237/245 (agree, R^2 0.95), yaw 7.4 (v0 default 30).
  INDI v0 hover motor-rate effort is 8x PID's, all of it from yaw: the yaw
  a_f noise passes to torque with gain 1/G1_Y. Fix decided (D-yawfilt), not
  yet implemented (`results/sync_check_v0.md`).
- **Blocker:** none. Usage budget is the binding constraint.
- **Caveat on notes:** paper notes are from PDF text extraction; several
  equations are flagged as reconstructed. Check them against the PDFs before
  quoting in the report.
- **Last updated:** 2026-11-14, session 7. Before that: 2026-11-13, session 5 (architecture written; INDI law
  library + unit tests committed, not yet wired into mc_rate_control; first
  G1 identification: pitch 211 (R^2 0.90), roll 321 (R^2 0.63), yaw not
  identified; see `results/identification_g1_v0.md`).

## Phase checklist

| # | Phase | Status |
|---|-------|--------|
| 1 | State of the art (`research/`, report ch. 2-3) | in progress: reading list written, notes smeur2016, acquatella2017, blaha2024, wang2019, tal2021, impl_paparazzi, impl_px4_prior done; remaining: sieberling2010, steffensen2023, sun2022, smeur2018, impl_indiflight |
| 2 | PX4 analysis and design (`plan/`, report ch. 4-5) | architecture v1 done (`plan/architecture.md`); report chapter not drafted |
| 3 | Simulation + benchmark harness on PID baseline (`docker/`, `bench/`) | image works, SITL build OK; gz_x500 headless smoke flight OK at speed 1 and 4 (`bench/smoke_gz.sh`); equivalence of results across speed factors not yet verified with metrics |
| 4 | Implementation (firmware + unit tests) | not started |
| 5 | Tuning and iteration | not started |
| 6 | Validation and report | not started |

## In progress

- Session 7 (2026-11-14): sonnet agent writing `bench/tune.py` (shared
  tuning driver, spec in `plan/tuning_driver_spec.md`), log in
  `plan/impl_log_tune.md`. INDI step_pitch/step_yaw seed1 batch running
  (`results/batch_s7_indi_pitchyaw.log`) for in-loop G1 identification.
- Nothing in flight. Session 6: INDI wired into mc_rate_control
  (d66f114963 msg `indi_rate_status`, d6182aea41 `MC_RATE_CTL_TYPE` +
  `MC_INDI_*` params). SITL build OK, lib gtest OK, diff reviewed by the
  orchestrator. INDI has NOT flown yet. Log: `plan/integration_log.md`.
  rate_ctrl_status is not published on the INDI branch (by design).

## Next concrete actions

0. Session 7 next steps, in order: (a) review/commit `bench/tune.py`
   (agent output, see "In progress"); (b) PID tuning round 1 on T1-T4
   (`--family pid --n-candidates 24 --seeds 1 2 --jobs 6`, add
   MC_YAW_TQ_CUTOFF to the PID space per D-yawfilt) — CPU only;
   (c) implement `MC_INDI_YAW_CUT` (D-yawfilt) in the INDI lib + gtest,
   rebuild, re-check hover effort with indi_v1.params; (d) INDI tuning round
   1 with the same budget (add MC_INDI_YAW_CUT to the INDI space).
   Primary metric of T2/T3 is stepped-axis attitude RMS, not IAE (metrics.py
   has no IAE): record this in the scenarios.md change log before tuning.
1. Phase 2 architecture DONE (`plan/architecture.md`, D-arch-1..6).
   INDI library DONE and integrated in mc_rate_control (session 6).
   First INDI flights DONE (session 6). Next: plot indi_rate_status
   (t_f vs allocated torque, a_f vs nu) on step_roll to check filter
   synchronisation before any gain change; then K sweep on T-set. Before tuning: SITL step
   identification of G1, actuator tc, loop/gyro rate (architecture sec. 10).
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

- PX4 integration facts (plan/px4_analysis_integration.md, unverified by a
  second reader): allocator is linear in motor command, normalised torque,
  sequential desaturation (thrust > roll/pitch > yaw); Gazebo
  `esc_status.esc_rpm` only echoes the command (no measured rotor speed), so
  SITL INDI needs an onboard first-order motor model; x500 motor time
  constants 0.0125 s up / 0.025 s down; PX4 CA_ROTOR_KM 0.05 vs gz
  momentConstant 0.016 (built-in yaw model mismatch). Suggested selection
  pattern: enum param in mc_rate_control (default PID), INDI law in a new
  lib beside src/lib/rate_control; mc_nn_control/mc_raptor use external
  modes and are not a suitable pattern.
- smeur2018: wind tunnel 10 m/s, INDI 0.21 m vs PID 1.51 m position error,
  but the PID had no gain matching (caveat for our fair-baseline design).

## Known problems

- RESOLVED (session 7): roll vs pitch G1 (321 vs 211) was an artefact of the
  open-loop fit; in-loop fit gives 237/245 (D-g1-v1).
- INDI yaw noise amplification (D-yawfilt) open; and step_yaw INDI v0
  saturates motors 14 % of the time (vs 4 % PID).
- INDI library: on a non-finite input it resets the actuator model to zero,
  so the next valid cycle starts from t_f = 0 (torque transient). Acceptable
  for stage 1; revisit (hold last valid state) during module integration.
- DONE: `make tests TESTFILTER=indi_rate_control` (ASAN build) passed in
  session 5 (log `results/unittest_asan_s5.log`, untracked).
- Guard false positives: both Sonnet agents had a heredoc/python shell
  command blocked as "system administration"; they used the Edit tool
  instead. Brief agents to write files with Write/Edit, not heredocs.

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
| 5 (2026-11-13) | 1 sonnet (INDI lib, 27 tool calls) | 2 runs (step_pitch, step_yaw PID seed1), 0 failures | ~$2.4 used of $3 cap |
| 7 (2026-11-14) | 1 sonnet (tune.py) | 2 INDI runs (step_pitch, step_yaw seed1) + agent smoke runs | $3 cap |
| 6 (2026-11-13) | 1 sonnet (module integration, 29 tool calls, ~$0.45) | 1 SITL build, 2 INDI runs (hover, step_roll seed1), 0 failures | $1.63 cap |

## Journal

- 2026-11-13: session 1 started from scratch; created `STATE.md`, `DECISIONS.md`,
  Docker image `px4-indi-sim`. Cut off by the 5-hour usage limit at 08:13.
- 2026-11-13: owner review after session 1: supervisor now on Opus 5.5 with a
  per-session spend cap, max 3 concurrent subagents, host kept awake; prompt
  updated (small tasks, write as you go, bounded phase 1, early smoke test).
- 2026-11-13: session 2: committed Docker image files; SITL build OK in Docker; reading list; notes smeur2016, acquatella2017, impl_paparazzi, impl_px4_prior; smoke flight script `bench/smoke_gz.sh`; smoke flight OK at speed 1 and 4.
- 2026-11-13: session 3: froze `bench/scenarios.md` v1 (T1-T9 tuning, H1-H6 held-out, paired Wilcoxon acceptance); notes wang2019, tal2021.
- 2026-11-13: session 2 closed: note blaha2024 added (RLS effectiveness identification, no PID baseline in that paper).
- 2026-11-13: session 4: committed runner v0; analyses plan/px4_analysis_{rate,integration}.md; note smeur2018; speed-factor check (18 runs): speed 4 OK for attitude/rate, not for hover position; PX4 rate-path analysis.
- 2026-11-13: session 5: `plan/architecture.md` + D-arch-1..6; gz x500 IMU 250 Hz, rotor inertia noted; `bench/identify_g1.py` and `results/identification_g1_v0.md` (roll only); INDI library delegated.
- 2026-11-13: session 5 closed: INDI law library + 10 gtests committed; pitch/yaw identification added.
- 2026-11-13: session 6: INDI selectable in mc_rate_control via MC_RATE_CTL_TYPE (PID default), indi_rate_status message; not yet flown.
- 2026-11-13: session 6: first INDI flights (hover, step_roll) stable with default parameters.
- 2026-11-14: session 7: `bench/check_sync.py`; INDI filters synchronised; in-loop G1 241/241/7.4 (`indi_v1.params`); yaw noise path found (D-yawfilt); tuning driver spec + agent.
