# S178 G2 spot-check at freeze-7 (Q16 answer A): 2 rate/attitude loop-margin cells

Freeze-7 firmware = current HEAD build (commit 08011e92d0), config params results/g5_freeze_s157/params.params (rate cell via
g2_freeze_s160/params_fwdef_roll.params, attitude cell via g2_att_freeze_s162/params_base.params, same base). Plant: matched GNSS
110 ms, `--vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0`, quad5in, `--sim v2`. G2 passes once the 24 freeze-7 outer cells
(g2_outer_freeze7_s177) and these 2 cells pass (QUESTIONS.md Q16).

## Cells (freeze-6 values from g2_freeze_s160 / g2_att_freeze_s162)
| cell | loop | rate | seed | freeze-6 GM dB | PM deg | DM ms | why |
|---|---|---|---|---|---|---|---|
| roll800_fwdef_s2 | rate roll, measured, firmware-default params (ID_OK 0, W_MAX 0, ACT_TC 0.05) | 800 | 2 | 16.4 | 54.3 | 83.4 | lowest measured rate PM (54.3/54.3/54.4 over seeds; model-only cells excluded per plateau rule, g2_plateau_s164_key2.md) |
| ax2_r400_s1 (pitch) | attitude (rate-setpoint break) | 400 | 1 | 19.2 | 53.4 | 106 | lowest attitude margin: PM 8.4 deg above 45 limit (GM 19.2 is 13 dB above 6), so PM is the binding one |

Recipes: rate = g2_freeze_s160/batch.sh (S138 injection, hover_long, check_rates, pretest_gate, m3a_csv, m3a_margins_pretest keyed
K100/K101); attitude = g2_att_freeze_s162/batch.sh (INJ_PT 1, RAMP 0.06, TP 10, 0.2-20 Hz, NP 5, hover_xlong). fly.sh changes only
out dir (g2_spot_freeze7_s178), container prefix (s178s*), wall-clock timeouts (flight 1000/1600 s, scoring 300/700 s); it also
runs hole_report on the rate cell.

## Run
queue3.sh polls (30 s, max 3 h) until queue2 finished: `^end` + QUEUE_END in g2_outer_freeze7_s177/queue2.log, 24 non-empty
`*_margins.json`, no container named s177* or s178s*. Then flies rate cell, attitude cell, serially. Log queue3.log (ends QUEUE3_END,
also on WAIT_TIMEOUT), status queue3_status.tsv.
Resume (repo root, only when no sim is running):
`setsid nohup bash indi_flight/results/g2_spot_freeze7_s178/queue3.sh >> indi_flight/results/g2_spot_freeze7_s178/queue3.log 2>&1 &`
A cell with a non-empty margins output is skipped; a flight.ulg without margins is only re-scored.

## Scoring (already inside fly.sh; manual repeat, repo root, docker idle)
- rate: `python3 indi_flight/bench/m3a_csv.py D/roll800_fwdef_s2/s1/flight.ulg 0 D/roll800_fwdef_s2/s1.csv; python3 indi_flight/bench/m3a_margins_pretest.py D/roll800_fwdef_s2/s1.csv 1 60 10 800 > D/roll800_fwdef_s2/margins.txt` (D = this dir)
- att: `python3 indi_flight/bench/attitude_break_check.py D/ax2_r400_s1/flight.ulg 1 --Tp 10 --fmin 0.2 --fmax 20` then
  `python3 indi_flight/bench/ratesp_csv.py D/ax2_r400_s1/flight.ulg 1 D/ax2_r400_s1_att.csv --Tp 10 --fmin 0.2 --fmax 20 --margins > D/ax2_r400_s1_margins.json`
- holes: `python3 indi_flight/bench/hole_report.py <flight.ulg>`; att second key: g2_att_freeze_s162/key2_att_margins.py.

## Pass rule (GATES.md G2)
GM >= 6 dB (smaller of the phase-crossover GM and min 1/|L| within 10 deg of -180), PM >= 45 deg, delay margin >= 2 control
periods + telemetry latency (model-only: +0); valid run: fault 0, landed 0, u = c + d <= 1e-6, no gap > 3 periods except sim holes
(hole FAILs on topics outside the loop under test are not invalidating, S163/S162). Single seed here (spot-check, Q16): result
reported against freeze-6 (expected within ~1 dB / 1 deg); a larger shift or any limit violation is escalated, not absorbed.

## Results
Pending (queue3.sh waiting).
