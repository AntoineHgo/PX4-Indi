# S56: roll M3a at 267 Hz (800/3) -- INVALID SET-UP, re-fly with TP 15

Logged rates OK (actuator_motors 266.7 Hz, dt 3.75 ms), pre-injection gates PASS (RMS 0.0032/0.0026, 0.0036/0.0035).
Set-up fault: MC_INDI_INJ_TP 10 s is 2666.67 controller samples at 800/3 Hz, so the multisine period is not a whole
number of samples and `margins_est.frf_periodic` cannot do a period-exact FFT. Seed 2 raised TimeBaseError; seed 1
passed the integer check by float rounding (PM 84.0, GM 10.0, DM 56 ms, Ms 4.1, f_c 4.2 Hz): PROVISIONAL, not used.
Fix: TP 15 (4000 samples) for 267 Hz (also valid at 400 and 800 Hz), and check why seed 1 passed the check.

S57: superseded by `results/stage3_s57/roll_m3a_267b/` (TP 7.5). Seed 1 here took the least-squares path (non-uniform time
base, 0.33 sample), not the FFT integer check; its numbers agree with the re-fly.
