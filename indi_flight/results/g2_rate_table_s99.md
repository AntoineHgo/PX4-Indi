# G2 rate-loop margin table, compiled S99 from existing results (no new flights)
Break point M3a (INDI). Threshold: GM >= 6 dB, PM >= 45 deg, DM >= 2 periods (800 Hz 2.5 ms, 400 Hz 5 ms, 267 Hz 7.5 ms; measured path + telemetry latency, value not stated in sources). Gate requires 2 seeds, 800 and 400.
FW "S57" = 296766019a / f9f70d6ef9 (before setpoint lead da64bc26b3); "HEAD" = S76/S77 (499e1df991). A-34 OPEN: HEAD roll PM is ~8-10 deg lower than S57 on the same param file.

| ctrl | axis | state source | rate Hz | GM dB | PM deg | DM ms | req DM ms | seeds | status | source (session) |
|---|---|---|---|---|---|---|---|---|---|---|
| INDI | roll | measured v2 | 800 | 16.6/16.3 (S57); 16.2 (HEAD) | 77.5/77.0 (S57); 69.1 (HEAD) | 70/72; 47 | 2.5+lat | 2 (S57), 1 (HEAD) | PASS (prelim, stale vs HEAD) | stage3_s57/roll_m3a_meas800/README.md:10-13 (S57); stage3_s77_a34/README.md:6-9 (S77); stage3_s76_bld/bld0.1_margins.txt (S76, PM 68.2 GM 16.0) |
| INDI | roll | measured v2 | 400 | NOT COVERED (see note a) | | | 5+lat | | NOT COVERED | - |
| INDI | roll | measured v2 | 267 | - | - | - | 7.5+lat | 0 | NOT COVERED | - |
| INDI | roll | model-only | 800 | 11.3 | 86 | - | 2.5 | 1 sweep point, no DM | PASS (weak: S53 act_tc_sweep x1.5, pre-S56 lead set) | quoted stage3_s57/roll_m3a_267b/README.md:22 (S53); raw not re-read |
| INDI | roll | model-only | 400 | 10.6/10.4 | 84.4/84.4 | 58/59 | 5 | 2 | PASS (S57 fw) | stage3_s57_pre/roll_m3a_400/README.md:8-11 (S56/S57) |
| INDI | roll | model-only | 267 (800/3) | 10.2/10.0 | 83.2/83.6 | 57/57 | 7.5 | 2 | PASS (S57 fw) | stage3_s57/roll_m3a_267b/README.md:8-11 (S57) |
| INDI | roll | unspecified path | 400 | 13.3 | 70.5 (tb 0), 70.4 (tb 1.0) | 50.8 | 5 | 1 | PASS (HEAD, 1 seed, path not stated) | stage3_s77_400/README.md:7-10 (S77) |
| INDI | pitch | model-only | 800 | 11.9/12.0 | 86.9/86.8 | - | 2.5 | 2 | PASS (S52/S56 fw, JOURNAL only) | JOURNAL.md:488 (S52-S56) |
| INDI | pitch | model-only | 400, 267 | - | - | - | 5 / 7.5 | 0 | NOT COVERED | - |
| INDI | pitch | measured v2 | 800, 400, 267 | - | - | - | - | 0 | NOT COVERED (x3) | - |
| INDI | yaw | model-only | 800 | 18.4 (18.5/18.3 at 22 Hz) | 88 | 197 | 2.5 | 2 | PASS (S57 fw, matched plant) | stage3_s56/yaw_m3a/README.md:7-15 (PM), stage3_s57_pre/yaw_m3a_hf/README.md:6-12 (GM) |
| INDI | yaw | model-only | 400, 267 | - | - | - | 5 / 7.5 | 0 | NOT COVERED | - |
| INDI | yaw | measured v2 | 800, 400, 267 | - | - | - | - | 0 | NOT COVERED (x3) | - |
| PID | roll, pitch, yaw | M1 gyro | 800, 400, 267 | - | - | - | - | 0 | NOT COVERED (x9) | JOURNAL.md:460: no measured PID margins exist |

## Counts (18 INDI cells = 3 axes x 2 state sources x 3 rates; plus 9 PID cells)
- PASS (preliminary): 6 INDI cells: roll meas 800, roll model 800/400/267, pitch model 800, yaw model 800. One more roll-400 HEAD point (path unknown).
- FAIL: 0.  NOT COVERED: 12 INDI cells + 9 PID cells = 21.
- Gate-required 800+400 INDI cells: 12; preliminary PASS 5 (roll model 800/400, roll meas 800, pitch model 800, yaw model 800); NOT COVERED 7 (pitch/yaw model 400, roll/pitch/yaw meas 400, pitch/yaw meas 800).

## Flags
- Only 1 seed: roll meas 800 at HEAD (S76/S77), roll 400 at HEAD (S77), roll model 800 (S53 sweep, undocumented seeds).
- Pre-S49 numbers: none used. S40 (roll 61/12, model-only 25/4.3) and S49 PM 42.9 are void (A-22/A-23 limit cycle, G1 saturation). Excluded.
- Stale vs HEAD: every S52-S57 number predates setpoint lead da64bc26b3; A-34 (ANOMALIES.md:25) shows roll PM dropped 77.5 -> 69 at 800 Hz. All still exceed thresholds by >= 24 deg PM, but final gate must re-fly on the frozen pair (GATES.md cell table).
- Conflicts: (1) S53 800 Hz model-only PM 86 vs S57 400 Hz 84.4: consistent. (2) roll 400 Hz: S57 model-only PM 84.4/GM 10.5 vs S77 PM 70.5/GM 13.3; likely HEAD + measured path, but S77 README does not state path or whether file = S57 meas800: UNVERIFIED. (3) GATES.md:104-145 plateau rule (GM = min of GM and 1/|L| where arg within 10 deg of -180) : no source states it was applied; the S56-S57 GM values are plain crossings, UNVERIFIED.
- Not verified: no linear-model cross-check (PM within 10 deg, GM within 3 dB) for measured path (meas800 README says not done); second key for S57 rate numbers unconfirmed (single FRF key stated for 400/267); S53 raw data; pitch numbers only in JOURNAL (no README read); measured-path telemetry latency not defined; PID results none; yaw M3a is only a 1-sample-of-plant per seed (seeds change noise only).
- Attitude-break cells (S91/S92, PM >= 55 deg) are a different loop, excluded.

## S101 update
The required v2 800/400 rate cells are now covered at HEAD for both actuator-state paths: measured (B99 + P99, keyed
K100, 12/12 PASS, worst GM 13.1 dB) and model-only (P100 + B100, keyed K101, 12/12 PASS, worst GM 10.12 dB, PM 70.8
deg, DM 39.7 ms). Still open for the G2 verdict: linear-model cross-check of the v2 path, PID M1 reference cells
(reference only, F-5), 250 Hz reported.
