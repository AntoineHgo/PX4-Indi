# A-55 closing test (S170): key1 vs key2 on all 9 hover runs

Command (docker): `bash indi_flight/bench/a55_key1_all.sh` (key1 g3_checks.py, window = last 10 s of the hold from
run.json; output <run>/g3_checks_a55.json). Key2: <run>/g3_checks_key2.json (harsh only committed; quiet/typ in g3_key2.md).

| item | key1 | key2 | agree |
|---|---|---|---|
| 1 loss of control | PASS 9/9 | PASS 9/9 | yes |
| 3 steady state | PASS 9/9 | PASS 9/9 | yes (values differ by window/reference, <= 0.098 m, both inside 0.10) |
| 2 p/q/r oscillation | none 9/9 | none 8/9; harsh_s2 2 Hz q at ~117 s (landing, after hold end) | no, span only |
| chatter (20-100 Hz, > 20 x median) | flagged 9/9 | flagged 9/9 (harsh 70 Hz, quiet/typ 22-39 Hz) | yes |

Both detectors scan the whole flight (key1 81 windows). The clause flags the quiet profile (no vibration) as well, at
22-39 Hz with ratios up to ~8000 in windows that start at 2 s (take-off); where in the flight the quiet flags sit is NOT
checked. Conclusion: the keys agree; the clause as written does not separate profiles (Q14 addendum 2). Remaining
disagreement = item-2 span at landing (GATES 304 "whole flight"), kept in A-55.

## S171 re-score after D-G3-SPAN (key1 span fixed)
Key1 now scores item 2 over the whole airborne span (descent included). Same command. Result on p/q/r: q sustained on
hover_harsh_s2 only (both keys agree, 9/9 runs). Key1 item-2 "fail" on the other 8 runs is the command-chatter clause (Q14).
The q oscillation starts at the offboard -> AUTO_LAND switch (119.06 s, ulog) and lasts through the descent to touchdown
(127.2 s). Descent body-rate RMS, ulog (host pyulog read, S171): INDI harsh 3.1-6.3 deg/s, typ 0.4-1.6, quiet 0.2-0.3,
hover before 0.3-0.4; PID harsh s1 (results/a54_s169) 0.3. Land-entry edge peak: INDI 10-73 deg/s (harsh), 9-10 (quiet);
PID harsh 72/63. -> A-56.
