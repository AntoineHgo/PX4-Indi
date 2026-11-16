# S49: D-RATE-LEAD falsification sweep with unmodelled delay (model only, UNKEYED)

Script: `bench/lead_delay_sweep_s49.py results/stage2_s49/lead_delay_sweep.md` (host, ~1 s). It reuses `lead_model_s48.L_lead`
(PM keyed by T101) and adds a plant command delay `lat` (samples) that the INDI model does not know.

Calibration of the delay on the S48 flight tc33_p8 (no lead, K20, P8, 800 Hz): measured PM 25.9 / f_c 2.92 / GM 10.7 / DM 24.6.
Model lat 0: 28.6/2.97/14.2/26.8; lat 2 (2.5 ms): 26.1/3.05/9.7/23.8; lat 4 (5 ms): 23.5/3.14/7.2/20.8.
-> the unmodelled delay is about 2-2.5 ms (one flight, f_c 0.13 Hz high in the model: rough).

Lead (tau_c 0.033), at 2.5 ms delay: 800 Hz K20 57.8 deg/11.4 dB, K30 55.1/8.8, K40 46.0/6.9;
400 Hz K20 57.0/10.5, K30 52.8/8.1, K40 42.7/6.2. At 5 ms: K20 54.4/8.3 (800), 53.3/7.8 (400).
Stop rule (route check 49: PM < 50 or GM < 8 dB at 400 Hz): NOT triggered at K20-30 with the calibrated delay;
triggered at K40, and at K20 only if the delay were 5 ms. Lead stays the candidate, with K_R default 20 (not 40),
and the 400 Hz result depends on the delay: measure it (roll M3a at 400 Hz, no lead) before the lead flight.
Not a G2 result: model only, roll only, single calibration flight, unkeyed.
