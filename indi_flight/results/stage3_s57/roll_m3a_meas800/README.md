# S57: roll M3a at 800 Hz on the measured-rotor path (flight configuration anchor)

`run_all.sh`, `meas800.params` = S56 `roll400.params` (ACT_TC 0.05, lead 1, derived G1, G2_Y 27, TP 10, AMP 0.001, bins 1-60 Hz)
+ `CA_R_W_MAX 2700` (quad5in maxRotVelocity, as S40 `inj_measured_long.params`), `--sim v2` (rotor speed through the eRPM
telemetry model), `--rate-hz 800`, hover_long, speed 4, firmware 296766019a. Margins `m3a_margins_pretest.py csv 1 60 10 800`.
Logged rates: actuator_motors 800 Hz (dt p1/p99 1.25 ms); esc_status median 800 Hz, mean 776-781 Hz (some 0/2.5 ms pairs).
Path check (log, `indi_rate_status.measured_torque_in_use`): 1.000 of samples in the 52-82 s analysis window on both seeds
(0.978 after first use over the whole flight: take-off/landing transitions).

| seed | pre-inj gate (--delay 4 --length 15) | bins | f_c [Hz] | PM [deg] | GM [dB] | DM [ms] | Ms [dB] |
|---|---|---|---|---|---|---|---|
| 1 | PASS (RMS 0.0039/0.0041/0.0006) | 18/18 | 3.08 | 77.5 | 16.6 | 70 | 2.1 |
| 2 | PASS (RMS 0.0045/0.0059/0.0011) | 18/18 | 2.99 | 77.0 | 16.3 | 72 | 2.1 |

Against the model-only path at 800 Hz (S53, same ACT_TC 0.05): PM 86 / GM 11.3. On the measured path the crossover is lower
(3.0 vs ~4 Hz at 400/267 Hz model-only), PM 9 deg lower, GM 5 dB higher, Ms 2 dB lower. G2 thresholds (GM 6 dB, PM 45 deg,
DM >= 2.5 ms + telemetry latency) met with margin. NOT yet cross-checked against a linear model of the measured path (G2 asks
for it): stage-6 item, together with the measured-path rows at 400 Hz and 800/3 Hz (route check 57). Single key: FRF script
S40-keyed; path check and rates read by the orchestrator on the log.
