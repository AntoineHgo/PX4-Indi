# T145: G2-STEP re-fly from a clean-tree build (g2_clean_s68)

Question: were the earlier G2-STEP 400 Hz results affected by a dirty-tree build? S64 400 Hz used a binary from dirty tree f183dad.

## Provenance
- HEAD: 524800b426687ad56df446a85e9c7a3f4077c237 (`git rev-parse HEAD`)
- `git status --short -uno` at start: ` M indi_flight/STATE.md` (one tracked change, a markdown status doc, not under the PX4 source tree). `git diff --stat HEAD` shows only that file. Left as is (user's uncommitted work, not stashed or committed).
- The g16_indi_s67 README records no build step. The S64 batch built with `make px4_sitl_default` via `indi_project/docker/run.sh` and gated flights on its rc. This batch follows the S64 procedure: `fly.sh` builds from the current tree first (`build.log`, rc in `done.txt`), flights start only on build rc=0.
- `head.txt` in this directory records HEAD and the status at batch start.

## Batches
- Batch A: 400 Hz, `results/g2_step_s64_400/indi.params`, seeds 1-3 x step_roll/step_pitch/step_yaw, 3 seed chains in parallel, `--speed 4`, wall timeout 900 s. Out: `steps_seed<N>/step_<axis>_indi`.
- Batch B: 800 Hz, `results/g2_step_s64/indi.params`, step_roll seed 1, 5 runs in parallel, `b800/r<k>/step_roll_indi`.

## Run status
- `done.txt`: build rc=0 (`make px4_sitl_default`, `build.log`), batch A 9/9 rc=0, batch B 5/5 rc=0, ALLDONE. No container left running, no Traceback in any `.stdout` file.
- Containers at start: none running (nothing to stop).
- Scoring: `bench/g2_step_metrics.py` (run from `indi_flight/`) -> `g2_step_primary_400.json` (9 flights), `g2_step_primary_800.json` (5 roll runs). Second key `bench/t127_step_metrics_key.py` per flight -> `key_400.md`.
- Pass limits (from `g2_step_metrics.py`): est OS <= 5.0 %, est settle <= 450 ms (roll, pitch) / 1350 ms (yaw). The S64 README gives no numeric limits, only "800 Hz limits", so these are the script's limits.

## Batch A: 400 Hz, seeds 1-3 (clean HEAD build) vs S64 400 Hz (dirty-tree binary f183dad)

| flight | S64 rise / settle / est OS / truth OS | clean rise / settle / est OS / truth OS | pass (clean) |
|---|---|---|---|
| seed1 roll | 188.7 / 312.5 / 1.78 / 1.86 | 195.7 / 352.5 / 0.78 / 0.71 | pass |
| seed1 pitch | 196.0 / 327.5 / 1.10 / 1.13 | 204.0 / 345.0 / 0.71 / 0.50 | pass |
| seed1 yaw | 544.7 / 918.8 / 0.16 / 0.00 | 543.9 / 910.0 / 0.36 / 0.00 | pass |
| seed2 roll | 205.7 / 360.0 / 0.40 / 0.43 | 199.9 / 358.8 / 1.09 / 0.79 | pass |
| seed2 pitch | 201.2 / 360.0 / 0.69 / 0.48 | 209.0 / 360.0 / 0.84 / 0.83 | pass |
| seed2 yaw | 545.1 / 906.3 / 0.38 / 0.00 | 543.8 / 890.0 / 0.38 / 0.00 | pass |
| seed3 roll | 199.3 / 336.3 / 0.74 / 0.57 | 200.3 / 360.0 / 0.71 / 0.52 | pass |
| seed3 pitch | 206.9 / 353.8 / 0.68 / 0.67 | 208.3 / 352.5 / 0.84 / 0.61 | pass |
| seed3 yaw | 544.7 / 926.3 / 0.24 / 0.00 | 545.4 / 898.8 / 0.25 / 0.00 | pass |

Units: rise ms, settle ms (est), OS %. All 9 pass in both sets.

Largest differences (clean minus S64):
- seed1 roll: est OS -1.00 pts (1.78 to 0.78), truth OS -1.15 pts, est settle +40 ms, rise +7.0 ms.
- seed2 roll: est OS +0.69 pts (0.40 to 1.09), truth OS +0.36, rise -5.9 ms.
- seed1 pitch: rise +8.0 ms, est settle +17.5 ms, est OS -0.39 pts.
- Yaw: rise within 1 ms, settle within 20 ms, OS within 0.25 pts.

Reference, same-seed spread at 400 Hz speed 4 (5 repeats, from `results/g16_indi_s67/README.md`): rise 4.04 ms, settle 15.00 ms, OS 0.70 pts. Batch A is three different seeds, so this is only a yardstick, not a like-for-like comparison. Clean seed1 roll OS 0.78 lies inside the g16 same-seed OS range (0.53 to 1.23), and S64 1.78 lay outside it. Clean seed1 roll rise 195.7 is about 6 ms below the g16 minimum (202.05).

Key check (`key_400.md`, est_g2 vs gt_g2): not all AGREE. OS differs by 0.01 to 0.38 pts, and settle has truth outliers. Truth settle is 2116 ms on seed1 pitch and 1966 ms on seed3 roll (est 345 and 360 ms). Yaw truth settle is about 1070 ms vs est 890 to 910 ms, and seed2 yaw truth settle is NaN. The S64 README reports AGREE on all 9, so this batch's key differs there. Pass/fail uses est values only.

## Batch B: 800 Hz, step_roll seed 1, 5 repeats (clean HEAD build)

| run | rise ms | est settle ms | est OS % | truth OS % | pass |
|---|---|---|---|---|---|
| r1 | 207.19 | 367.50 | 0.76 | 0.76 | pass |
| r2 | 202.78 | 353.75 | 1.66 | 1.54 | pass |
| r3 | 198.96 | 328.75 | 1.33 | 1.19 | pass |
| r4 | 211.54 | 346.25 | 0.85 | 0.73 | pass |
| r5 | 213.47 | 361.25 | 0.68 | 0.54 | pass |

Spread (max minus min) across the 5 runs:
- rise: 198.96 to 213.47 ms, 14.5 ms
- est settle: 328.75 to 367.50 ms, 38.75 ms
- est OS: 0.68 to 1.66 %, 0.98 pts
- truth OS: 0.54 to 1.54 %, 1.00 pt

S64 800 Hz seed 1 roll (rise 206, est settle 366, est OS 0.66, truth OS 0.39), against this spread:
- rise 206: inside the spread.
- est settle 366: inside the spread, near the top (max 367.5).
- est OS 0.66: just below the minimum (0.68), outside by 0.02 pts.
- truth OS 0.39: below the minimum (0.54), outside.

So S64 800 Hz roll sits inside the spread on rise and settle but falls just outside on both OS measures.

## Open points (not verified)
- This batch does not show whether the dirty-tree binary changed the 400 Hz results. There is no clean-vs-dirty same-seed pair at 400 Hz, and the dirty binary was not re-flown.
- The 400 Hz key differences above (truth settle outliers) were not investigated further.
- Only the 800 Hz roll flights were re-flown for batch B, not pitch or yaw.
- `indi_flight/STATE.md` was a tracked uncommitted change at batch start. It is a markdown doc outside the PX4 source tree, and `git diff --stat HEAD` shows it as the only change. The firmware build used the same sources as HEAD. It was not stashed or committed.
- Nothing committed.

## Late change to the tree (added after this batch started)
- `git status --short -uno` at batch start (`head.txt`, 23:43:56) showed only `indi_flight/STATE.md`.
- During the batch, `src/lib/indi_accel_control/IndiAccelControlTest.cpp` became a tracked modification (26 added lines, mtime 23:45:54). This was not made by this batch. Its origin is unknown and it was not touched here.
- The firmware build (`build.log`, rc 0) was done before that change. All 14 flights ran the binary from that build, so the flights come from HEAD plus STATE.md only. This is the intended build, but the tree was not clean for the whole session.

## Orchestrator reading (S68)
- Provenance note: the only tracked change at build time was `indi_flight/STATE.md`; the guard test added later to
  `IndiAccelControlTest.cpp` (T146) is not compiled into the SITL binary. T146 also rebuilt `build/px4_sitl_o11` from
  unchanged source; not used by this batch.
- A clean HEAD build gives seed-1 roll at 400 Hz rise 192.5 ms, inside the range of S64 (187.5-188.7) and of the
  g16 runs (202-210) taken together: the dirty-tree lead (T144) is not needed to explain the S64 outlier.
- Same-seed spread, clean binary: 800 Hz rise 14.5 ms, settle 39 ms, OS 1.0 pt; 400 Hz (g16 + this) rise ~18 ms.
  Worst settle 368 ms against the 450 ms limit: margin 82 ms, more than twice the spread. G2-STEP 9/9 at 400 Hz
  and 9/9 at 800 Hz stand.
- Truth-settle outliers in `key_400.md` (nan, ~2 s) were already present in S64 (`../g2_step_s64_400/key_all.md`:
  nan, 2811 ms): the truth end value sits ~0.2 deg (1.5 % of 15 deg) from the setpoint, at the edge of the 2 % band.
  Pass/fail uses the estimate (est_g2); not a new anomaly.
- Remaining lead for the spread: wall-clock arming. Next: sim-time arm in the runner (second key), then 5 same-seed runs.
