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
