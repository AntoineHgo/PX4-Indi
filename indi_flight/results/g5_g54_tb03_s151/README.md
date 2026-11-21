# S151 G5.4 take-off/land probe at MC_INDI_POS_TB 0.3 (D-GAP-G510 overturn test, probe, seed 1, serial)

Fly + check: `bash indi_flight/results/g5_g54_tb03_s151/fly.sh` (params `results/g5_g510_s150/params_tb03.params`,
firmware f3b93704b6 tree, matched GNSS 110 ms). Checker `bench/auto_smoke_check.py` (keyed S135, g54_key2.py).

| scenario | edge step (<= 10 % hover) | ramp max | overshoot / bounce | touchdown vz (<= 0.8) | tilt | land vz | RTL err |
|---|---|---|---|---|---|---|---|
| auto_land10 | 4.0 % | 7.5 % | -0.09 / 0.20 m | 0.685 m/s | 0.21 deg | 0.692 | n/a |
| auto_tour | 4.4 % | 7.5 % | -0.09 / 0.20 m | 0.691 m/s | 0.11 deg | 0.698 | 0.048 m |

All G5.4 limits PASS, same as S135 at TB 1.0 (edge <= 4.4 %, ramp 7.5 %). The faster blend does not move the
ramp -> flight or landing edges. Overturn test of D-GAP-G510 (ramp/landing edge) not triggered on this seed.
