# G5 gap flights (S198): events seeds 2 and 3, G5.8 at 3 m/s

Firmware: existing build `build/px4_sitl_default/bin/px4` (mtime 2026-11-21 22:38:25, sha256 d220e19315c2...), not rebuilt; the S193 README records this same binary. HEAD differs from 7fe6206fcc in src only by new unit tests and one line (IndiStageMode.hpp fminf/fmaxf, commit e9e85e395d, 01:46 on 11-22, after the binary; same arithmetic). Params g5_freeze_s157/params.params, PLANT as queue.sh.
One simulation at a time, `fly.sh` (progress.txt). Commands: `python3 indi_flight/bench/g5_events.py --controller indi $PLANT --seed N --params $P --out events/g5_events_sN` (same as queue.sh `ev`), moving: same plus `--moving`, out `moving/g5_events_mov_sN`.
Scoring (host python): g5_rows_check.py, g511_check.py, g5_rows_key2.py per flight dir; key2_g511 via copy `key2_g511_s198_copy.py` (D set to events/, seeds 2,3, output key2_g511_s198.txt; original untouched). Outputs in events/ and moving/.

## Gap 1, events seeds 2, 3 (s1 from S193 unchanged: all PASS)
| row | s2 value | s3 value | limit | key 1 | key 2 |
|---|---|---|---|---|---|
| G5.8 rc_loss entry-timeout / excursion | 510 ms / 0.062 m | 510 ms / 0.082 m | 1 s / 1 m | PASS PASS | PASS |
| G5.8 link_loss | 8 ms / 0.086 m | 6 ms / 0.121 m | 1 s / 1 m | PASS PASS | PASS (entry on flag; key 2 has no excursion) |
| G5.8 offboard_loss | 25 ms / 0.080 m | 32 ms / 0.073 m | 1 s / 1 m | PASS PASS | PASS (entry only) |
| G5.9a kill (outputs 0 after kill flag) | 1.25 ms | 0.00 ms | <= 1.25 ms | PASS PASS | gate definition PASS (same numbers); script prints FAIL on the legacy switch reference (+6.25 / +10.0 ms), as known (audit item 4) |
| G5.9b rearm states | all zero | all zero | zero | PASS PASS | key 2 prints zeros, no verdict |
| G5.9c first second | 0.01 % | 0.01 % | 5 % | PASS PASS | 1.01 / 1.02 % of full scale, no verdict |
| G5.9d takeoff after re-arm | 4.0 % of hover, dip 0 m | 4.7 %, dip 0 m | 10 %, 0.3 m | PASS PASS | PASS |
| G5.11 ekf_yaw tilt excess / excursion / osc | jump 0.55, excess -0.33 deg / 0.061 m / no | jump 1.00, excess +0.12 deg / 0.040 m / no | 1 deg / 0.5 m | PASS PASS | s2 PASS; s3 raw jump 1.003 > 1 on the legacy rule (script prints FAIL); its no-event refs max 0.951 give excess ~0.06 deg, so PASS under Q12 D; excursion 0.040 PASS; osc not computed by key 2 |
| G5.11 ekf_xy excursion / osc | 0.234 m (3-D 0.235) / no | 0.248 m / no | 0.5 m | PASS PASS | excursion 0.235 / 0.249 PASS; its 1 deg tilt rule (6.8 / 7.4 deg) is obsolete and not judged |

## Gap 2, G5.8 at 3 m/s (`--moving`, seeds 1-3): NOT SCORED
No script scores "deviation of ground truth from the commanded setpoint/trajectory <= 1 m" (Q8 add.3 (i)). g5_rows_check.py (and key 2) measure distance from the position at event onset, and print "hover case only, 3 m/s not flown". Not written, per instruction. Raw numbers of the existing scorer (onset-referenced, so not the gate definition; FAIL printed by it by construction), excursion m:
| seed | rc_loss | link_loss | offboard_loss | entry-timeout (rc/link/ob) |
|---|---|---|---|---|
| 1 | 5.308 | 12.307 | 15.694 | 510 / 10 / 28 ms |
| 2 | 5.149 | 12.84 | 15.813 | 510 / 5 / 22 ms |
| 3 | 4.186 | 12.23 | 15.245 | 510 / 1 / 26 ms |
Link_loss moving: scorer reports "entered nav 14 (offboard), configured hold: False" on all three seeds (vehicle was in offboard, not hold, at the event); timing entry is via the gcs_connection_lost flag. Matches the S147 probe (5.39 / 12.47 / 15.56). Files: moving/g5_rows_mov_sN.txt, key2_g5rows_mov_sN.txt.

## Big files
All 5 files over 1 MB (flight.ulg x5) are matched by indi_flight/.gitignore (`*.ulg`) (git check-ignore confirmed). sends.csv, *.log, gz_model_info.txt also ignored.
