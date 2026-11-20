# S143 G5.7 mode_switch10 seed 2 with GNSS delay 110 ms (corrected set-up)
Command (repo root; same as S139 run_batch.sh, plus `--gps-dly 110 --gnss-delay 110`; `timeout 600`):
`indi_project/docker/run.sh -n g5g57gnss2 -t 500 -- python3 indi_flight/bench/run_scenario.py --scenario mode_switch10 --stick-mode posctl --controller indi --model quad5in --seed 2 --speed 4 --sim v2 --params indi_flight/results/g5_g57_s139/params.params --gps-dly 110 --gnss-delay 110 --out indi_flight/results/g5_g57_s143_gnss/mode_switch10_s2`
Score: `bench/g57_check.py --validity leaveP` (S139 official rule; no lag_compare needed), `g57_summary.txt`. No firmware rebuild, no code edits, no stray containers.
Tilt error deg over [e+0.3, e+1.0] (limit 5), thrust step % of hover (limit 20); S139 s2 (GNSS delay 0) vs S143 (110 ms):
| edge | speed | tilt S139 / S143 | thrust S139 / S143 |
|---|---|---|---|
| e1 P>A | 2.5 | 0.32 / 0.54 | 0.9 / 0.9 |
| e2 A>P | 1.0 | 1.79 / 1.38 | 0.4 / 0.4 |
| e3 P>S | 2.3 | 0.32 / 0.53 | 0.3 / 0.1 |
| e4 S>P | 0.9 | 4.99 / 2.37 | 3.0 / 3.0 |
| e5 P>H | 2.2 | 4.79 / 2.14 | 0.3 / 0.2 |
| e6 H>P | 0.1 | 3.86 / 2.27 | 0.3 / 0.1 |
| e7 P>A | 1.9 | 0.30 / 0.49 | 1.0 / 1.1 |
| e8 A>S | 0.8 | 0.06 / 0.03 | 0.5 / 0.7 |
| e9 S>H | 0.3 | 2.96 / 3.62 | 1.2 / 1.4 |
| e10 H>P | 0.1 | 5.24 FAIL / 2.30 | 0.3 / 0.2 |
Verdict (leaveP): S143 seed 2 PASS (max tilt 3.62 at e9, max thrust 3.0 %); S139 seed 2 FAIL. Validity: 10 edges, 4 leaving-P edges >= 1.5 m/s, no LOC, hover 0.137, rc=0.
One seed only: seeds 1 and 3 were not re-flown, so G5.7 is not re-scored as a gate (S139 s1 PASS, s3 FAIL under delay 0).
Seed 3 (same command, seed 3, rc=0, valid: 4 fast edges, no LOC): PASS, max tilt 3.55 deg at e9 S>H (S139 s3 FAIL: 5.17 e6, 5.25 e10; S143 e6 2.41, e10 2.11), worst thrust step 3.0 % at e4 (S139 3.1 %). Summary: g57_summary_s3.txt.
