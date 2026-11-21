# S162 G2 attitude cells at the stage-6 freeze

Plant/params: D-FREEZE-6 (quad5in, --sim v2 measured rotor speed, matched GNSS 110 ms, G4 typical noise --vib-acc 10
--vib-gyr 0 --imu-noise-scale 4.0), firmware d1b65d0f09 (freeze + D-T10-RESET), base params
= g2_freeze_s160/params_roll.params minus MC_INDI_INJ_*; break MC_INDI_INJ_PT 1 (attitude-loop output = rate
setpoint), S107 recipe (RAMP 0.06, TP 10 s, 0.2-20 Hz, NP 5, hover_xlong). Command: `bash chain.sh > chain.log`
(pre-test roll/yaw 800 s1 gated the other 10 cells; all 12 flew, fly rc 0). Scripts: attitude_break_check.py
(validity), ratesp_csv.py --margins (FRF + margins), hole_report.py.

| cell | PM deg | GM dB | f_c Hz | DM ms | check | holes |
|---|---|---|---|---|---|---|
| roll 800 s1/s2 | 54.7 / 54.5 | 20.2 / 20.3 | 1.39 | 109 / 109 | PASS | FAIL* / PASS |
| roll 400 s1/s2 | 54.0 / 54.2 | 19.9 / 19.6 | 1.40 | 107 / 107 | PASS | PASS |
| pitch 800 s1/s2 | 54.9 / 54.1 | 20.9 / 20.2 | 1.38 | 111 / 109 | PASS | PASS |
| pitch 400 s1/s2 | 53.4 / 53.9 | 19.2 / 19.7 | 1.40 | 106 / 107 | PASS | FAIL* / PASS |
| yaw 800 s1/s2 | 81.4 / 81.3 | 30.5 / 30.5 | 0.47 | 479 / 474 | PASS | PASS |
| yaw 400 s1/s2 | 81.4 / 81.4 | 30.8 / 30.9 | 0.48 | 476 / 475 | PASS | PASS |

Worst of 2 seeds per cell: all pass GM >= 6 dB, PM >= 45 deg, DM >= 2 periods + latency (<= 10 ms). Lowest: pitch
400 PM 53.4 deg, GM 19.2 dB. Seed spread <= 0.8 deg / 0.7 dB. *Hole FAILs are on vehicle_local_position_setpoint
(88.9 Hz position-loop output, outside the loop under test: 1 hole of 25 ms; count-disagree 2 samples); the analysed
attitude-break window has max gap 0 periods and u = c + d error 3e-8 in every run, so the GATES validity condition
"result unchanged with hole windows left out" holds trivially. Versus S107 (preliminary pair, sim-default noise):
roll/pitch PM 56.8+ -> 53.4-54.9 deg, GM 22.0+ -> 19.2-20.9 dB; yaw PM 73 -> 81 deg (D-T10/freeze param changes and
typical noise; not chased, all far from limits). Linear-model x-check: attitude roll/pitch model = S93 T195 (A-36,
GM model low), yaw unmodelled: not re-run here. Second key: key2_att_margins.{py,txt} (S162, pending).
