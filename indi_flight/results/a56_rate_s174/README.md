# A-56 rate-loop probe (S174): one inner-loop change per flight, harsh hover seed 3

Probe (not gate evidence). Firmware as a56_probe_s173, freeze params `g5_freeze_s157/params.params` with one change,
harsh hover (`--vib-acc 27 --vib-gyr 0 --imu-noise-scale 4.0`), matched GNSS 110 ms, serial.
Fly: `sh indi_flight/results/a56_rate_s174/fly.sh` (s3), `fly2.sh` (bld03 s1, s2); score (Docker): `analyse.sh`.

| config | change | item 2 q (s3) | flagged p/q | item 1 LOC | item 3 |
|---|---|---|---|---|---|
| baseline, pos0, lpf4 (S172-S173) | - | sustained 2.0 Hz, window 81-82 | - | PASS | PASS |
| bld03 | MC_INDI_ACT_BLD 0.3 (was 1.0) | **not sustained** | 3/1 | PASS (tilt max 12.8 deg) | PASS (h rms 0.072 m) |
| lead0 | MC_INDI_LEAD 0 (was 1) | sustained 2.0 Hz, window 82 | 3/3 | PASS (14.9 deg) | PASS (0.048 m) |
| dgyro15 | IMU_DGYRO_CUTOFF 15 | not flown: runner refuses filter-cutoff params (`--rate-hz` fixes them) | - | - | - |

g3_checks rc 1 in both flown runs is the chatter clause (Q14), present in every run.

Reading: the seed-3 2 Hz q line appeared in 4/4 configurations that kept the rate blend at 1.0 s (baseline, pos0,
lpf4, lead0) and disappears with 0.3 s. The decision it names is D-RATE-BLD (value 1.0 s chosen on a one-seed
post-event transient; S76 margins showed no tb effect at the 4 Hz crossover). Before re-opening it: bld03 on s1/s2
(fly2.sh), see below.
