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

## S174 follow-up: bld03 s1/s2 and land-entry trace (falsifies the blend reading and the S173 "INDI rate loop" reading)

bld03 s1: no sustained line; **s2: q sustained 2.0 Hz, window 82** (baseline s2 was clean). The line moves between
seeds; it is not the blend. Window 82 = the 3 windows that span AUTO_LAND entry in every flagged run.
Trace (`land_entry_trace.py <ulg> <t0> <t1>`, 0.5 s bins of vehicle_angular_velocity q vs vehicle_rates_setpoint, trajectory_setpoint):
at AUTO_LAND entry the stock land setpoint jumps (vx 0.2-0.54 m/s, x moving 0.1-0.56 m) and q follows its own
setpoint (q std = qsp std within 10 %) for 1-2.5 s, then returns to the hover floor (0.3 deg/s).

| run | land-entry q std peak (deg/s) | duration | traj vx peak (m/s) | item 2 flag |
|---|---|---|---|---|
| INDI bld03 s2 | 25.0 | ~2 s | -0.29 | sustained q 2 Hz |
| INDI bld03 s3 | 9.1 | ~1 s | 0.54 | no |
| PID s2 (a56_pid_s173) | 16.0 | ~2 s | 0.51 | no |
| PID s3 (a56_pid_s173) | 30.5 | ~2.5 s | 0.22 | no |

Reading: A-56 is a setpoint-driven transient at AUTO_LAND entry, present in BOTH stacks with similar size (PID s3 is
the largest), not an oscillation of the INDI rate loop (the rate loop tracks its setpoint). Whether the spectral
detector flags it as "sustained" depends on window alignment and the transient's spectrum. Source of the setpoint
jump (stock navigator/FlightTaskAuto land initialisation, likely from the noisy velocity estimate at harsh
vibration) is UNVERIFIED and stock (O-11). G4 item 2 consequence: owner question Q15.
