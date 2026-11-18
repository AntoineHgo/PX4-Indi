# S91 attitude-loop break pre-test (MC_INDI_INJ_PT 1, rate-setpoint break)

Firmware 2bed1ae95a (SITL build 08:22). `fly.sh AX RATE SEED RAMP`, hover_xlong, quad5in, v2, 400 Hz, roll (AX 1),
Tp 10, 0.2-20 Hz, NP 5, DLY 20, base params stage5_s84_accbreak/pt1.params without PINJ. Two flights, serial:
RAMP 0.03 and 0.06 rad/s per component. Extractor `bench/ratesp_csv.py` (T192, keyed T193 AGREE WITH MINOR,
design/t193_ratesp_key.md), L = -Y/X with y = rates_sp_pre_inject, x = rates_sp_applied.

| RAMP | PM deg | GM dB | f_c Hz | check | holes |
|---|---|---|---|---|---|
| 0.03 | 57.3 | 22.04 | 1.332 | PASS | FAIL sim 0.061 % (limit 0.05), excess 8.75 ms; a Docker pytest ran in parallel |
| 0.06 | 56.6 | 22.02 | 1.318 | PASS | PASS |

Validity both flights: window 50.0 s with d != 0 (20000 cycles), max |x-y-d| <= 3e-8, max gap 3.75 ms, no fault/stale.
attitude_break_check.py: law received x (rate_sp_dot one-step error 0.003 of signal vs 0.875 if fed y); c responds
at excited bins.

Linearity between amplitudes: 0.4-12.6 Hz within 1.0 dB and 3 deg, coherence >= 0.965. Not met at the two lowest
bins (0.2, 0.3 Hz; |L| 14-20 dB, far from crossover): up to 2.0 dB / 12.9 deg, coherence 0.73-0.79 at RAMP 0.03
(low SNR against hover disturbances; 0.97 at RAMP 0.06). Pre-test verdict: PASS for RAMP 0.06 (cells use 0.06);
the 0.2-0.3 Hz bins do not affect PM/GM.
Delay margin (PM / (360 f_c)): 0.119 s. Unverified: gate restart on a PT change in flight (M3 of T191).

## Cells (batch.sh, serial, RAMP 0.06, seed 1)

| axis | rate Hz | PM deg | GM dB | f_c Hz | delay margin s | min coh (decade of f_c, bins >= 0.2 Hz) | check | holes |
|---|---|---|---|---|---|---|---|---|
| roll | 400 | 56.6 | 22.0 | 1.318 | 0.119 | 0.966 | PASS | PASS |
| pitch | 400 | 56.8 | 22.1 | 1.332 | 0.119 | 0.902 | PASS | PASS |
| yaw | 400 | 73.4 | 34.3 | 0.455 | 0.448 | 1.000 | PASS (rate_sp_dot SKIP on yaw) | PASS |
| roll | 800 | 57.3 | 21.9 | 1.319 | 0.121 | 0.880 | PASS | PASS |
| pitch | 800 | 58.1 | 21.9 | 1.311 | 0.123 | 0.931 | PASS | PASS |
| yaw | 800 | 73.8 | 33.9 | 0.454 | 0.452 | 1.000 | PASS (rate_sp_dot SKIP on yaw) | PASS |
| roll | 267 (reported, S92) | 55.5 | 21.8 | 1.364 | 0.113 | not computed | PASS | FAIL (count-disagree flag only, see below) |

All six cells are above the G2 thresholds (GM >= 6 dB, PM >= 45 deg, delay margin >= 2 periods + telemetry latency,
i.e. a few ms). All windows are 50.0 s and max |x-y-d| is 3e-8. Limits: the attitude loop is measured with the
outer loops closed (open question 2 of design/attitude_break_s86.md); there is no linear-model cross-check yet
(note sec 5); no PID reference at this break (note sec 4); 250 Hz reported point flown at 267 Hz (D-RATE267) for roll only; one seed. Roll at 800 Hz has
coherence 0.88 < 0.9 at the lowest bins of the decade, which are far from crossover.

## S92: 267 Hz reported cell (batch267.sh)

Roll, 800/3 = 266.7 Hz (D-RATE267; the runner rejects 250), RAMP 0.06, seed 1, same firmware and pipeline as
batch.sh. PM 55.5 deg, GM 21.8 dB, f_c 1.364 Hz, delay margin 0.113 s (30 periods), window 50.0 s, max gap
0.0005 periods, max |x-y-d| 3e-8, check PASS. hole_report OVERALL FAIL comes only from the count-disagree flag on
vehicle_torque_setpoint and actuator_motors: 2 intervals of 6.25 ms (5 physics steps instead of 3) with 0 messages
missing by count, i.e. timestamp jitter, no lost controller output; all missing-% and excess limits pass. Not
re-flown (RC89: no cosmetic re-flies); the cell is reported, not a pass cell. Coherence not computed.
Margins move little from 400 to 267 Hz (PM 56.6 -> 55.5 deg), as expected with crossover at 1.3 Hz.
