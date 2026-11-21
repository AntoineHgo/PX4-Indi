# freeze-8 gate re-fly queue (S181, D-FREEZE-8)
Firmware: src/ at d2f3845292. Params results/g5_freeze_s157/params.params (no MC_INDI_XY_P/XY_VP, firmware 1.2/3.6; checked by grep).
Serial, idempotent: `queue.sh` (status `queue_status.tsv`: name, start, end, rc; log `queue.log` ends `QUEUE_END`). Every flight has a wall-clock timeout.
Resume (repo root, no sim running): `nohup bash indi_flight/results/freeze8_s181/queue.sh >> indi_flight/results/freeze8_s181/queue.log 2>&1 &`
(an item is skipped when its flight.ulg / margins output exists).

## Rows (87 flights, order as listed; estimate ~70-90 min, flights are 30-80 s wall)
| group | n | out | command source |
|---|---|---|---|
| G2 outer cells | 24 | g2o/pt{0,1}_ax{1,2,3}_r{800,400}_s{1,2} | g2o_fly.sh = g2_outer_freeze7_s177/fly.sh (out dir, prefix s181o), cell list/order and AMP/TP/SCN from its queue2.sh; margins + holes scored in-script |
| G2 spot cells | 2 | g2s/roll800_fwdef_s2, g2s/ax2_r400_s1 | g2s_fly.sh = g2_spot_freeze7_s178/fly.sh (out dir, prefix s181s) |
| G4 | 18 | g4/{hover,cruise}_{quiet,typ,harsh}_s{1-3} | bench/gate_g4.sh fly single-run, as freeze7_s177 (container names g4*, not s181) |
| G5.5 | 24 | g55/<sc>_s<seed> | freeze7_s177 queue (offb_vel_step, o1..o7 x 3) |
| G5.3/G5.4 | 9 | g5/{auto_tour,auto_land10,hold_wind}_s{1-3} | freeze7 queue; hold_wind = g5_freeze_s157/hold3.sh (`--stick-mode posctl --scenario-overrides g5_freeze_s157/hold_wind_overrides.json`, 5 m/s steady, 8 peak, +x) |
| G5 events in hover | 1 | events/g5_events_s1 | not flown at freeze-7; g5_freeze_s157/batch2.sh runev (bench/g5_events.py, no extra args) |
| G2-STEP | 9 | steps/seed{1-3}/step_{roll,pitch,yaw}_indi | freeze8_pretest_s181/fly.sh (g2_step_s64/indi.params, 800 Hz) |
Not included (per brief): G5.10, G3. G5.3 "mission" = auto_tour (as freeze-7). Scoring is not part of the queue (G5/G4/G5.5/step scorers as in the freeze-7 / pretest READMEs).
