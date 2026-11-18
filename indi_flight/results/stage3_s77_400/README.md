# S77: rate-loop margins at 400 Hz vs rate blend (D-RATE-BLD precondition 1 at 400 Hz)

Roll M3a (D-G2-BREAK), hover_long, quad5in, 400 Hz, seed 1, speed 4, sequential, firmware `head.txt`.
Params: S57 file (`tb0.params`) and S57 + MC_INDI_ACT_BLD 1.0. Resume: `bash indi_flight/results/stage3_s77_400/fly.sh`.
Analysis: `bench/m3a_margins_pretest.py csv 1 60 10 400`, 18/18 bins accepted in each flight.

| tb [s] | PM [deg] | f_c [Hz] | GM [dB] | DM [ms] |
|---|---|---|---|---|
| 0 | 70.5 | 3.85 | 13.3 | 50.8 |
| 1.0 | 70.4 | 3.85 | 13.3 | 50.8 |

G2 thresholds (GM >= 6 dB, PM >= 45 deg, DM >= 2 periods (5 ms) + telemetry latency) met with wide margin; the
blend has no effect at 400 Hz either (its corner is below the crossover). With S76 (800 Hz: PM 68-69, GM 16 dB),
D-RATE-BLD precondition 1 is met at both rates on roll. Caveats: roll only, one seed; the `*_gate.md` FAIL "rate RMS
axis 0" is the S76 set-up artefact (gate window overlaps the roll injection). A-34 applies (law at HEAD, setpoint lead).
`velbreak_search.md`: no outer-loop injector exists yet (needed for the D-GAP velocity-break items).
