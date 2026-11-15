# s8l: O-13 pre-check of set O re-flown with SENS_GNSS0_DELAY 0 (session 56, 2026-11-15)

pid_tuned, seed 1, v2 sim, `--gnss-delay 0` (D-s8-gnss-delay). Script `bench/s8l_o13_gnss0.sh`. Feasibility only.
Old = `results/s8i_o13_precheck.md` (stock 110 ms delay). Track = trajectory rms 3d in the EKF frame.

| entry | track old -> new [m] | max dev old -> new [m] | effort old -> new | saturation old -> new | verdict |
|---|---|---|---|---|---|
| O1 lemniscate | 0.441 -> 0.455 | 1.36 -> 1.16 | 0.712 -> 0.765 | 0 -> 0 | flyable |
| O2 circle_z (5 m/s) | 0.579 -> 0.584 | 1.15 -> 1.14 | 0.664 -> 0.671 | 0 -> 0 | flyable |
| O3 lemniscate + gust | 0.404 -> 0.411 | 1.41 -> 1.24 | 0.625 -> 0.657 | 0 -> 0 | flyable |
| O4 lemniscate + payload | 0.742 -> 0.775 | 2.17 -> 2.77 | 0.627 -> 0.517 | 8.7 % -> 33.3 % (high) | flyable, thrust-limited |
| O5 zsine + com_shift | 0.190 -> 0.165 | 0.65 -> 0.57 | 0.776 -> 0.779 | 0 -> 0 | flyable |
| O6 zsine + mass | 0.155 -> 0.096 | 0.43 -> 0.31 | 0.978 -> 0.986 | 0 -> 0 | flyable |
| O7 lemniscate, tau x2 | 0.439 -> 0.452 | 1.36 -> 1.11 | 0.716 -> 0.765 | 0 -> 0 | flyable |

No watchdog abort, no warning. All seven entries stay flyable; the set is unchanged.

O4: mean motor command 0.88 in both runs, so the payload leaves little thrust headroom and the saturated fraction
moves a lot with small changes (8.7 % -> 33 %). The disturbance response is the same (peak vertical deviation 0.70 m,
recovered in 5.8 s old / 8.9 s new). O4 stays in the set as frozen, because thrust-limited flight is part of what a
payload entry tests. In the verdict its saturation fraction is reported, and seed-to-seed spread is expected to be
large. No entry is changed after this pre-check.
