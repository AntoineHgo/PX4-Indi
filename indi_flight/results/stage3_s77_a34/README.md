# S77: A-34 closing flights (rate-loop PM shift vs S57)

Roll M3a, hover_long, quad5in, 800 Hz, seed 1, speed 4, flown sequentially (A-32) at `head.txt` (dcba400943).
Resume: `bash indi_flight/results/stage3_s77_a34/fly.sh` from the repo root. 18/18 bins accepted in each flight.

| run | params | PM [deg] | f_c [Hz] | GM [dB] | DM [ms] |
|---|---|---|---|---|---|
| tb0 | exact S57 file (blend off) | 69.1 | 4.07 | 16.2 | 47.1 |
| bld1.0 | S57 + MC_INDI_ACT_BLD 1.0 | 68.9 | 4.12 | 15.8 | 46.5 |
| S57 (f9f70d6ef9) | same file as tb0 | 77.5 | 3.08 | 16.6 | 69.8 |

Findings.
1. The rate blend is not the cause: tb 0 at HEAD reproduces S76 (PM 69 deg), not S57.
2. Parallel load (A-32) is not the cause: S76 (3 parallel) and S77 (sequential) agree within 0.6 deg / 0.5 dB.
3. The runner label (`indi_m3a` in S57, `indi` now) is metadata only; MC_INDI_POS_EN is not set in either flight.
4. Shape of the change: |L| higher by 2.3-3.1 dB from 1 to 5 Hz, phase 7-12 deg lower from 2.5 to 8 Hz, identical
   above 10 Hz (within 1 dB / 4 deg). That is a change in the low/mid-frequency path (attitude to rate setpoint to
   torque), not in the inner INDI rate path.
5. Firmware between the two binaries that the flight runs (pos module off): 65356c4250 (landed flags, ramp),
   6fd4542b52 (setpoint timeout), da64bc26b3 (rate-setpoint lead on the setpoint path, D-S3-ATT-STEP),
   b8866cd4b1 (derivative restart). Only da64bc26b3 changes the airborne law: it adds MC_INDI_LEAD x filtered
   d/dt(rate setpoint), which raises the gain of the attitude path at mid frequencies, as observed.
   Not confirmed by a flight: MC_INDI_LEAD 0 removes both leads, so no parameter isolates it.
Closing test (pending): fly the same file at da64bc26b3^ (worktree build) and expect S57 within 2 deg, or add the
setpoint lead to `bench/margins_models.py` and match the 1-8 Hz bins within 1 dB / 5 deg.
G2 reading: margins at HEAD (the law to be frozen) pass with 24 deg PM and 10 dB GM above thresholds.
