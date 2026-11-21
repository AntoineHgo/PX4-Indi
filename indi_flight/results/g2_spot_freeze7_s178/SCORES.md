# G2 spot-check at freeze-7 (S178 cells), scores

Commands (repo root, run by queue3.sh/fly.sh; scoring outputs read as the README "Scoring" section names them, not re-run):
- rate: `python3 indi_flight/bench/m3a_csv.py D/roll800_fwdef_s2/s1/flight.ulg 0 D/roll800_fwdef_s2/s1.csv; python3 indi_flight/bench/m3a_margins_pretest.py D/roll800_fwdef_s2/s1.csv 1 60 10 800 > D/roll800_fwdef_s2/margins.txt` (+ pretest gate: PASS, rates/motor pin/torque fraction in limits)
- att: `python3 indi_flight/bench/attitude_break_check.py D/ax2_r400_s1/flight.ulg 1 --Tp 10 --fmin 0.2 --fmax 20` (RESULT PASS) then `python3 indi_flight/bench/ratesp_csv.py D/ax2_r400_s1/flight.ulg 1 D/ax2_r400_s1_att.csv --Tp 10 --fmin 0.2 --fmax 20 --margins > D/ax2_r400_s1_margins.json`
- holes: `hole_report.py` output in holes.txt / ax2_r400_s1_holes.txt (OVERALL line).
Limits: PM >= 45 deg, GM >= 6 dB, DM >= 2 periods + latency (2.5 ms at 800 Hz, 5 ms at 400 Hz, plus latency). Escalate shift vs freeze-6 > ~1 dB / 1 deg.

| cell | GM dB (freeze-6) | PM deg (freeze-6) | DM ms (freeze-6) | limit | verdict | hole check |
|---|---|---|---|---|---|---|
| roll800_fwdef_s2 | 16.1 (16.4) | 47.8 (54.3) | 80.6 (83.4) | GM>=6, PM>=45, DM>=2 periods | PASS on limits; PM 2.8 deg above limit (marginal), -6.5 deg vs freeze-6: ESCALATE | OVERALL PASS (sim 0.0035 %, controller 0.0116 %) |
| ax2_r400_s1 (pitch att) | 19.1 (19.2) | 43.0 (53.4) | 88.7 (106) | GM>=6, PM>=45, DM>=2 periods | FAIL: PM 43.0 < 45 (-10.4 deg vs freeze-6) | OVERALL PASS (sim 0.0075 %, controller 0.0057 %) |

**Total: 1/2 PASS (att cell fails PM; roll cell passes but shifted -6.5 deg vs freeze-6, marginal).**
Not done: att second key (g2_att_freeze_s162/key2_att_margins.py) and rate second key were not run here; values are primary only.
