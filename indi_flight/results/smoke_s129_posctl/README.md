# S129 SITL smoke flight: POSCTL stick scenario, INDI position module, quad5in, seed 1

## Command
    timeout 900 indi_project/docker/run.sh -n s129posctl -t 420 -- python3 indi_flight/bench/run_scenario.py --scenario stick_zsine_o6 --stick-mode posctl --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --params indi_flight/results/smoke_s129_posctl/smoke_params.params --out indi_flight/results/smoke_s129_posctl

Exit code 0, runner error None, metrics.json status "ok" (see caveat below).

## Params diff vs S128
Params file: `smoke_params.params` (copy of the S128 smoke file). Diff against the S128 file: none.
- `MC_INDI_POS_EN 1` was ALREADY present in both `indi_flight/bench/params/quad5in_indi_defaults.params:38` and the S128 smoke copy. Adding it was a no-op.
- `MC_RATE_CTL_TYPE 1` is present (appended, as in S128).
- The tracked defaults file differs from the copy only in comments.

## Scenario
S128 used `hover`, which is OFFBOARD (nav_state 14), not POSCTL. The requested POSCTL run therefore used
`stick_zsine_o6` (mode="stick", ZSINE/zmulti vertical-velocity stick profile, 18 s, neutral x/y/yaw sticks) with
`--stick-mode posctl`. `s5_gap085_posctl` was not used because it injects a motor fault (thrust 0.85 on the "up" segment).

## Checks (from flight.ulg)
- Parameters: MC_INDI_POS_EN = 1, MC_INDI_EN = 1.
- Module started: topic `indi_pos_status` present, 5192 samples. px4.log has `[mc_indi_pos_control] INDI stage ...` lines. Zero `mc_pos_control` lines in px4.log.
  The S128 ulog also has `indi_pos_status` (5601 samples), so S128 already ran the INDI position module.
- nav_state (vehicle_status): 4 (LOITER) at 0 s, 17 (TAKEOFF) at 10.3 s, 4 at 17.7 s, 2 (POSCTL) at 32.1 s, 18 (LAND) at 63.3 s, 2 at 75.2 s (after disarm).
- Command log (vehicle_command): arm 400 at 9.9 s, takeoff 22 at 10.1 s, DO_SET_MODE 176 (POSCTL) at 31.9 s,
  NAV_LAND 21 at 63.1 s with source_system 255 (the runner).
- Landing: "Landing detected" at 73.1 s, "Disarmed by landing" at 75.1 s. No failsafe (failsafe flag 0 throughout).
- Hold window, POSCTL, neutral sticks, 55-63.1 s (n=720):
  z mean -6.32 m NED, z std 0.050 m; max |x-mean| 0.016 m, max |y-mean| 0.021 m; xy drift 0.002 m;
  max tilt 0.26 deg; max |body rate| 0.024 rad/s.
- Altitude excursion, POSCTL neutral sticks, 1 s means: 36 s -4.98 m, 40 s -5.86 m, 44 s -6.41 m, 48 s -6.76 m, 52 s -7.02 m, 56 s -6.31 m (NED).
  So ~2 m of altitude drift over 36-52 s, then recovery to about -6.3 m.
  Window 45-58 s: z std 0.62 m, dominated by this excursion; xy max 0.03 m; tilt max 0.29 deg; rate max 0.024 rad/s.
- Metric script: `metrics.json` (runner-generated) reports window 55.2-79.2 s, which spans the landing and the stick
  sweep. Its "ok" status is not a hold result. The hold numbers above come from my own pyulog analysis. S128 had no separate
  metric script beyond the runner's metrics.json.

## Caveats and anomalies
- The runner sent NAV_LAND at 63.1 s, in the middle of the 18 s stick sweep (sweep rows in sticks.csv run to 74.95 s).
  The sweep was therefore only partly flown (about 5 s), and the rest of the flight was a descent to landing.
  Root cause not found (runner stick-segment timing vs land step). Not investigated further.
- Altitude excursion of about 2 m in POSCTL is unexplained (possibly the altitude capture at mode switch, or the
  INDI position loop). Not analysed.
- Gazebo/PX4 time base taken as ULog time = runner sim time (matched on arm and mode-switch commands).

## Verdict
- Module started: YES (indi_pos_status present, INDI stage log lines, MC_INDI_POS_EN 1).
- Flies in POSCTL: YES, takeoff, POSCTL 32-63 s, xy hold within 0.03 m, tilt < 0.3 deg, rates < 0.025 rad/s.
- Holds altitude: NO clean result. About 2 m altitude excursion in POSCTL with neutral sticks. Stable again by 56 s (z std 0.05 m over 55-63 s).
- Smoke as specified (stick sweep flown in POSCTL): NOT validated, because the runner landed mid-sweep.

## Unverified
- Cause of the 2 m altitude excursion and of the early NAV_LAND.
- mc_pos_control not running is inferred from zero px4.log lines and the presence of indi_pos_status; no dedicated topic for mc_pos_control was checked.
- Stick-sweep tracking in POSCTL (the flown part is 58.2-63.1 s only).
- Not a repeat of the S128 metric (the S128 hover was OFFBOARD, not POSCTL).
