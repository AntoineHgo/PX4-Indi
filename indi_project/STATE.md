# INDI project state

## Status summary (read this first)

- **Phase:** 1 (state of the art) not really started: session 1 was cut off by a
  usage limit before any research note was written. Docker image built, not
  yet tested.
- **Headline results:** none yet. No controller code, no simulation run.
- **Blocker:** none. Usage budget is the binding constraint (see known problems).
- **Last updated:** 2026-11-13 (corrected by the owner after session 1).

## Phase checklist

| # | Phase | Status |
|---|-------|--------|
| 1 | State of the art (`research/`, report ch. 2-3) | not started (raw material downloaded) |
| 2 | PX4 analysis and design (`plan/`, report ch. 4-5) | not started (some code read, no notes) |
| 3 | Simulation + benchmark harness on PID baseline (`docker/`, `bench/`) | image `px4-indi-sim` built, untested |
| 4 | Implementation (firmware + unit tests) | not started |
| 5 | Tuning and iteration | not started |
| 6 | Validation and report | not started |

## In progress (session 2, 2026-11-13)

- Background: `make px4_sitl_default` in Docker (log `logs/smoke_build.log`).
- Subagents in flight (output files; partial notes may exist if cut off):
  - smeur2016 (haiku) -> `research/notes/smeur2016.md`
  - acquatella2017 (haiku) -> `research/notes/acquatella2017.md`
  - impl_paparazzi (sonnet) -> `research/notes/impl_paparazzi.md`

## Next concrete actions

1. Commit `docker/`, `STATE.md`, `DECISIONS.md` (all still untracked).
2. Smoke-test the image: build `px4_sitl` through `docker/run.sh`, fly
   `gz_x500` headless once, record lockstep and speed-factor behaviour.
3. Write `research/reading_list.md` (about 8 core sources, 2-3 implementations),
   then run research as small subagent tasks (one source or one repository
   each), reusing what is already in `research/raw/`.
4. Read the PX4 rate/attitude/allocator/gyro-filter code; write
   `plan/px4_analysis.md` and `plan/architecture.md`.

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

## Journal

- 2026-11-13: session 1 started from scratch; created `STATE.md`, `DECISIONS.md`,
  Docker image `px4-indi-sim`. Cut off by the 5-hour usage limit at 08:13.
- 2026-11-13: owner review after session 1: supervisor now on Opus 5.5 with a
  per-session spend cap, max 3 concurrent subagents, host kept awake; prompt
  updated (small tasks, write as you go, bounded phase 1, early smoke test).
