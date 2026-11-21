Queue start: 2026-11-21 16:34:32 CET (nohup setsid, log queue.nohup.log, status queue_status.tsv)
Command: cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi && nohup setsid bash indi_flight/results/freeze9_s183/queue.sh > indi_flight/results/freeze9_s183/queue.nohup.log 2>&1 &
Resume: rerun `bash indi_flight/results/freeze9_s183/queue.sh` from the repo root; done items (flight.ulg or margins JSON present) are skipped.
First item g2o_pt1_ax3_r800_s1: rc=0, margins json present (pm 63.1 deg, dm 0.26 s); param check MC_INDI_XY_VP=2.4, MC_INDI_XY_P=1.2 (initial params, no changed-param entries).
G4 cruise_harsh_s2 excluded until Q19 (D-FREEZE-9).

## Hole re-fly (S183)

Five cells whose hole report read OVERALL FAIL were re-flown (gate rule: hole problems mean re-fly, not fail).

Moved aside to `holefail_first/`:
- `holefail_first/g2o/`: dirs `pt0_ax1_r400_s2`, `pt1_ax1_r400_s2`, `pt0_ax3_r800_s2`, `pt1_ax3_r800_s1`, plus each cell's `_holes.txt`, `_margins.json`, `_margins.err`, `_pinj.csv`, `.params`, `.stdout.log`.
- `holefail_first/g2s/`: dir `roll800_fwdef_s2` and `roll800_fwdef_s2.params`.

Command (queue skips items whose done-file exists, so only these 5 flew):
`cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi && nohup setsid bash indi_flight/results/freeze9_s183/queue.sh > $R/queue_refly.nohup.log 2>&1 &`
All 5 items finished with rc 0 (17:44 to 17:49). QUEUE_END appended 17:49:36.

| Cell | First attempt OVERALL | Re-fly OVERALL | First pm/gm/dm | Re-fly pm/gm/dm |
|---|---|---|---|---|
| g2o pt0_ax1_r400_s2 | FAIL | PASS | 51.57 / 13.43 / 0.384 | 51.58 / 13.43 / 0.395 |
| g2o pt1_ax1_r400_s2 | FAIL | FAIL | 57.61 / 13.88 / 0.513 | 52.05 / 14.14 / 0.469 |
| g2o pt0_ax3_r800_s2 | FAIL | FAIL | 65.47 / nan / 0.246 | 72.42 / nan / 0.302 |
| g2o pt1_ax3_r800_s1 | FAIL | FAIL | 63.13 / nan / 0.256 | 61.00 / nan / 0.244 |
| g2s roll800_fwdef_s2 | FAIL | PASS | 47.08 / 15.93 / 0.076 | 47.31 / 16.09 / 0.076 |

Re-fly FAIL detail: pt1_ax1_r400_s2 is a count-disagree on vehicle_local_position_setpoint (3 holes). pt0_ax3_r800_s2 and pt1_ax3_r800_s1 both fail on sim_ground_truth at 800 Hz (176/218 and 114/139 holes). These three need a further re-fly under the same rule.

Margins units: pm in deg, gm in dB, dm in s. gm is nan for the two ax3 cells (no phase crossing).

## G2 hole re-fly, round 2 (S183)

Moved aside to `holefail_second/g2o/` (cell dir, `<cell>_*` files, `.params`, `.stdout.log`; same layout as `holefail_first/g2o/`): the second attempts of
`pt1_ax1_r400_s2`, `pt0_ax3_r800_s2`, `pt1_ax3_r800_s1`. `docker ps` empty, then `bash queue.sh` (nohup setsid, log `queue_refly2.nohup.log`) flew the 3 cells and g4 cruise_harsh_s2 (rc 0 each); QUEUE_END 17:55:00.

| cell | attempt | hole OVERALL | failing class rows | PM deg | GM dB | DM s |
|---|---|---|---|---|---|---|
| pt1_ax1_r400_s2 | first (holefail_first) | FAIL | controller: vehicle_local_position_setpoint count-disagree (0 holes, max 0 ms) | 57.6 | 13.9 | 0.512 |
| pt1_ax1_r400_s2 | second (holefail_second) | FAIL | controller 0.0169 % holes, max gap 23.75 ms (lpos_setpoint count-disagree) | 52.0 | 14.1 | 0.469 |
| pt1_ax1_r400_s2 | third (current g2o/) | PASS | none (sim 0.0139 %, max 10.0 ms, controller 0 %) | 58.3 | 14.1 | 0.508 |
| pt0_ax3_r800_s2 | first | FAIL | controller 0.0244 % (count-disagree, max 20.0 ms) | 65.5 | n/a | 0.246 |
| pt0_ax3_r800_s2 | second | FAIL | sim 0.2470 % (sim_ground_truth/sensor_gyro), max gap 8.75 ms; controller 0.0931 %, max 17.5 ms | 72.4 | n/a | 0.302 |
| pt0_ax3_r800_s2 | third (current) | PASS | none (sim 0.0104 %, max 6.25 ms; controller 0.0278 %, max 5.0 ms) | 65.7 | n/a | 0.260 |
| pt1_ax3_r800_s1 | first | FAIL | controller 0.0150 % (count-disagree, max 3.75 ms) | 63.1 | n/a | 0.256 |
| pt1_ax3_r800_s1 | second | FAIL | sim 0.1593 % (limit 0.05), max gap 8.75 ms | 61.0 | n/a | 0.244 |
| pt1_ax3_r800_s1 | third (current) | FAIL | sim 0.0161 % ok but max gap 13.75 ms (excess 12.5 > 10); controller 0.0172 %, max gap 15.0 ms (excess 13.75 > 10) | 59.9 | n/a | 0.231 |

(gm n/a = no phase crossing, as in the margins JSON.) pt1_ax3_r800_s1 has now failed the hole report three times; per the task rule (flight fails twice -> record, stop) it was not flown again. It is left in `g2o/` as the current attempt (OVERALL FAIL), awaiting the owner. The third attempt ran with nothing else on the host.
