# S135 G5.4 probe (pre-freeze, RC113): take-off, land, RTL from 20 m, INDI from arming (F-7, b9fb83c4a0)

quad5in, `MC_RATE_CTL_TYPE 1` + `MC_INDI_POS_EN 1` (params.params = auto_smoke_s132), speed 4, sim v2, sim default noise.
Commands: `run_batch.sh` (auto_tour, auto_land10, seeds 1-3), `run_rtl20.sh` (auto_rtl20, mission ends ~28 m from home).
Checker: `bench/auto_smoke_check.py RUN --json RUN/check_s135.json` (g54_takeoff, g54_other; 8 synthetic self-tests,
break-checked). Second key: `bench/g54_key2.py` (independent, key2_s135.md): touchdown vz, tilt, re-lift, edge step
agree to rounding on auto_tour_s1, auto_tour_s3, auto_land10_s2.

Result: 9/9 runs, every GATES 5/5b G5.4 limit PASS, all runs exit ok (per-run table for 6 runs: g54_table.md).

| limit (GATES 5b / 5) | worst over 9 runs | threshold |
|---|---|---|
| ramp thrust step, 0.1 s means, after ramp+0.5 s | 7.5 % hover | 10 % |
| take-off edge step | 4.4 % hover | 10 % |
| truth dip 1 s after edge | 0.000 m | 0.3 m |
| take-off overshoot | -0.005 m (never above target) | 0.5 m |
| touchdown truth vz (anchor: truth z_up <= ground+0.05 m) | 0.710 m/s | 0.8 m/s |
| tilt at touchdown | 0.45 deg | 10 deg |
| land mean vz vs MPC_LAND_SPEED 0.70 | 0.713 m/s | +-20 % |
| contact -> disarm | 2.69 s | COM_DISARM_LAND + 1 = 3.0 s |
| RTL height error (auto_tour, auto_rtl20) | 0.275 m (rtl20 s2) | 1 m |

Notes: bounce reads 0.200 m by construction (entry band), the test is "no fall > 0.3 m below target", passes. Re-lift reads
0.05 m = touchdown anchor height, no re-lift. ground_contact flags ~0.43 s after truth touchdown, hence the truth anchor.
Not covered here: noise = typical profile (G4, re-fly at freeze); A-46 (ACRO edge) goes with the G5.1 acro probe.
