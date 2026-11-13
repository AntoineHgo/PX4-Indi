# INDI project state

## Status summary (read this first)

- **Phase:** 1 (state of the art) in progress: 5 of 12 reading-list notes done.
  Phase 3 smoke test PASSED: `px4_sitl_default` builds in Docker and
  `gz_x500` flies headless (takeoff, hover at 2.5 m, land) at speed factor 1
  and 4 (4x: 43 s of sim in ~10 s wall, no log dropouts).
- **Headline results:** none yet. No controller code.
- **Blocker:** none. Usage budget is the binding constraint.
- **Caveat on notes:** paper notes are from PDF text extraction; several
  equations are flagged as reconstructed. Check them against the PDFs before
  quoting in the report.
- **Last updated:** 2026-11-13, session 2.

## Phase checklist

| # | Phase | Status |
|---|-------|--------|
| 1 | State of the art (`research/`, report ch. 2-3) | in progress: reading list written, notes smeur2016, acquatella2017, blaha2024, impl_paparazzi, impl_px4_prior done |
| 2 | PX4 analysis and design (`plan/`, report ch. 4-5) | not started |
| 3 | Simulation + benchmark harness on PID baseline (`docker/`, `bench/`) | image works, SITL build OK; gz_x500 headless smoke flight OK at speed 1 and 4 (`bench/smoke_gz.sh`); equivalence of results across speed factors not yet verified with metrics |
| 4 | Implementation (firmware + unit tests) | not started |
| 5 | Tuning and iteration | not started |
| 6 | Validation and report | not started |

## In progress

- Nothing. No subagent or simulation running.

## Next concrete actions

1. Harness: write the scenario/metric spec (`bench/scenarios.md`) and a
   MAVSDK-based runner (one command: scenario, controller, seed -> ULog +
   metrics). Verify speed factor 1 vs 4 give the same metrics before using 4.
   Smoke usage: `indi_project/docker/run.sh -n smoke-gz -t 600 indi_project/bench/smoke_gz.sh <speed>`;
   ULogs land in `build/px4_sitl_default/rootfs/fs/log/`.
2. Remaining phase-1 notes, one small subagent each (haiku for papers):
   sieberling2010 and tal2021 and sun2022 need fetching (web-fetch, save PDFs
   under `research/raw/papers_dl/`); wang2019, steffensen2023 have PDFs on
   disk (`research/raw/robustness/`, need text extraction, e.g. `pdftotext`
   if present in the container); impl_indiflight
   (sonnet, code on disk).
3. Phase 2: read PX4 rate/attitude/allocator/gyro-filter code; write
   `plan/px4_analysis.md` and `plan/architecture.md`.
4. Draft report ch. 2 (state of the art) from the notes once the list is covered.

## Key findings so far (from notes, to verify before the report)

- With a fixed effectiveness, rate-loop INDI is algebraically an incremental
  PI(D) with gain 1/(G*Ts) (acquatella2017, eq. 29-30). Any INDI advantage
  over a well-tuned PID must come from effectiveness scaling, actuator-state
  feedback (true motor state vs commanded), saturation handling, or the
  acceleration feedback path: the benchmark must be designed to probe these.
- Paparazzi: same 2nd-order Butterworth on gyro and on modelled actuator
  state; first-order actuator model; WLS allocation with roll/pitch priority
  in the full version; no NaN checks, fixed dt (impl_paparazzi).
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

## Journal

- 2026-11-13: session 1 started from scratch; created `STATE.md`, `DECISIONS.md`,
  Docker image `px4-indi-sim`. Cut off by the 5-hour usage limit at 08:13.
- 2026-11-13: owner review after session 1: supervisor now on Opus 5.5 with a
  per-session spend cap, max 3 concurrent subagents, host kept awake; prompt
  updated (small tasks, write as you go, bounded phase 1, early smoke test).
- 2026-11-13: session 2: committed Docker image files; SITL build OK in Docker; reading list; notes smeur2016, acquatella2017, impl_paparazzi, impl_px4_prior; smoke flight script `bench/smoke_gz.sh`; smoke flight OK at speed 1 and 4.
- 2026-11-13: session 2 closed: note blaha2024 added (RLS effectiveness identification, no PID baseline in that paper).
