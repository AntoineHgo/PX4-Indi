# S130 SITL smoke flights: INDI stage_mode (D-STAGE-STALE), hover and POSCTL, quad5in, seed 1

## Flags (read first)
- Build OK: `make px4_sitl_default` rc 0 (`build.log`), `bin/px4` linked.
- stage_mode: all published samples are 1 (indi). No 0, 2 or 3 in either flight. No "INDI stage degraded" in either px4.log.
- Expectation "0 on ground / takeoff ramp" not seen: 0 is never published (per the msg comment). The first `indi_pos_status` sample is at 14.6 s (hover) and 14.3 s (POSCTL), so no ground-time samples exist at all.
- Hover window: the NAV_LAND (command 21) is at 69.5 s ULog time, in S128 too. The hold window is therefore 55.0 to 69.5 s, not 55 to 85 s. The 55-85 window includes the descent (z goes to 0 by 78 s). The previous S128 numbers quoted a 55-85 window with z std 0.015 m; that cannot include the landing, so they were likely computed on a different window. Like-for-like comparison below uses 55.0-69.5 s.
- Runner timing anomaly, pre-existing (same in S128 and S129): NAV_LAND is sent about 16 s before the runner's own window end (`run.json` t_window_end 85.1 s / 79.3 s vs NAV_LAND at 69.5 s / 63.1 s). Not caused by this change; not investigated further.
- POSCTL hold is noisier than S129 (z std 0.114 vs 0.050 m, max xy 0.042/0.040 vs 0.016/0.021 m, tilt 0.45 vs 0.26 deg). Still well inside 0.05 m and 0.5 deg, but it is a visible change on one seed. Cannot tell noise from regression with n=1.
- POSCTL metrics.json warnings: "no nav_state 14 span" (expected, not OFFBOARD) and "window start from run.json". Status "ok" is not a hold result.
- The ~2 m altitude excursion in POSCTL (36-56 s) reproduces S129 almost exactly (see table).

## Commands
Build (`build.log`, rc 0):

    timeout 1500 indi_project/docker/run.sh -n s130build -t 1400 'make px4_sitl_default'

Hover (params file from S128, output changed):

    timeout 900 indi_project/docker/run.sh -n s130hover -t 420 -- python3 indi_flight/bench/run_scenario.py --scenario hover --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --params indi_flight/results/smoke_s128_idok0/smoke_params.params --out indi_flight/results/smoke_s130_stage/hover

POSCTL (params file from S129, output changed):

    timeout 900 indi_project/docker/run.sh -n s130posctl -t 420 -- python3 indi_flight/bench/run_scenario.py --scenario stick_zsine_o6 --stick-mode posctl --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --params indi_flight/results/smoke_s129_posctl/smoke_params.params --out indi_flight/results/smoke_s130_stage/posctl

Both exit 0, runner error None, `run.json` error None.

## stage_mode counts (indi_pos_status, ULog)
| run | stage_mode 0 | 1 | 2 | 3 | samples | first sample | airborne | ground |
|---|---|---|---|---|---|---|---|---|
| hover | 0 | 5601 | 0 | 0 | 5601 | 14.59 s | 5601 | 0 |
| posctl | 0 | 5198 | 0 | 0 | 5198 | 14.30 s | 5198 | 0 |

"Airborne" = `vehicle_land_detected.landed` false. No stage_mode transitions in either run.
S128 had 5601 `indi_pos_status` samples and S129 had 5192, so the sample counts are consistent with before.

## Metrics: S130 vs previous
Hover, window 55.0-69.5 s (S130) vs S128 as reported (window 55-85 s, see flag):

| metric | S128 (prev) | S130 |
|---|---|---|
| z mean (NED) | -4.985 m | -5.013 m |
| z std | 0.0149 m | 0.0140 m |
| max abs x dev | 0.049 m | 0.038 m |
| max abs y dev | 0.058 m | 0.047 m |
| max body rate (norm) | 0.028 rad/s | 0.0235 rad/s |
| max tilt | not reported | not computed in hold window |

Hover 1 s z means, 30-68 s: -5.00 to -5.04 m throughout (flat).

POSCTL, hold window 55.0-63.1 s (same window as S129):

| metric | S129 (prev) | S130 |
|---|---|---|
| z mean (NED) | -6.32 m | -6.27 m |
| z std | 0.050 m | 0.114 m |
| max abs x dev | 0.016 m | 0.042 m |
| max abs y dev | 0.021 m | 0.040 m |
| max tilt | 0.26 deg | 0.45 deg |
| max body rate (norm) | 0.024 rad/s | 0.020 rad/s |

POSCTL altitude excursion, 1 s z means (NED, m), S129 / S130:
36 s -4.98 / -4.96; 40 s -5.86 / -5.84; 44 s -6.41 / -6.34; 48 s -6.76 / -6.75; 52 s -7.02 / -7.00; 56 s -6.31 / -6.30.
z std 45-58 s: 0.62 (S129) / 0.57 (S130).

## Command timeline (ULog, s)
- Hover: arm 10.38, takeoff 10.50, OFFBOARD (176) 32.39, NAV_LAND 69.49, landed ~78.2, disarm ~80.
  nav_state: 17 TAKEOFF at 10.5, 4 LOITER at 18.0, 14 OFFBOARD at 32.5, 18 LAND at 69.5.
- POSCTL: arm 9.93, takeoff 10.11, POSCTL (176) 31.93, NAV_LAND 63.12, landed 73.45.
- S128 land command at 69.52 s and S129 at 63.12 s, so the land timings match the previous runs exactly.

## Files (untracked, under this folder)
build.log, hover/ and posctl/ (flight.ulg, metrics.json, run.json, px4.log, sends.csv, ...), hover_run_stdout.log, posctl_run_stdout.log, analysis.json, analyze_s130.py, analyze_hover_s130.py, cmp_land_s130.py, smoke_params.params (copy of the S129 file).
