# G5 evidence audit at FREEZE-10 (S197)

Check of evidence against the written tests (GATES.md 5 and 5b, owner amendments S175, S180, S183, S187, S197). No test or limit changed, no verdict written here. Evidence root `results/freeze10_s193/` (abbrev. `f10/`), freeze-9 root `results/freeze9_s183/` (`f9/`). Scores are in `f10/G5_SCORES.md` and `f10/G5_5_RESCORE_Q25.md`.

Carry-over rule used: D-FREEZE-10 invalidates G5 outer rows (all re-flown at freeze-10) and carries nothing over for G5. G5 event rows are a 1-seed hover confirm at each freeze since D-FREEZE-6/7 ("G5 event rows in hover 1 seed confirm"); the older 3-seed event flights are on older firmware and are not carried over by D-FREEZE-10.

| row | test as written (seeds, limit) | evidence path | key 1 | key 2 | complete? |
|---|---|---|---|---|---|
| G5.1 acro | stick_steps, 3 seeds; RMS rate error <= 10 deg/s on 100 deg/s steps; no LOC | f10/g5_modes/stick_steps_s{1-3}_acro (*.key1.txt, *.key2.txt) | PASS 3/3 (worst 1.94) | PASS 3/3 | yes |
| G5.1 stab | 3 seeds; tilt <= 3 deg and yaw rate <= 10 deg/s after release; no LOC | f10/g5_modes/stick_steps_s{1-3}_stab | PASS 3/3 (worst tilt 0.12) | PASS 3/3 | yes |
| G5.2 z (altctl) | 3 seeds; z overshoot <= 0.3 m, settle <= 4 s (band max(2 %, 0.10 m), Q10 B) | f10/g5_modes/stick_pos_steps_s{1-3}_altctl | PASS 3/3 | PASS 3/3 (strict 2 % band also < 4 s) | yes |
| G5.2 xy (posctl) | 3 seeds; x overshoot <= 0.5 m, settle <= 4 s; z as above | f10/g5_modes/stick_pos_steps_s{1-3}_posctl | PASS 3/3 | PASS 3/3 | yes |
| G5.3 hold | 3 seeds; 3-D RMS <= 0.3 m in 5 m/s wind, nav 4 | f10/g5/hold_wind_s{1-3}, g53_hold_check.txt, key2_g53_hold.txt | PASS 3/3 (worst 0.062) | PASS 3/3 | yes |
| G5.3 mission | 3 seeds; 4 waypoints within 1.0 m, speed <= 1.1 x cruise | f10/g5/auto_tour_s{1-3}.g53.check.txt | PASS 3/3 (worst wp 0.970 m, margin 0.03) | none exists (also none at freeze-9) | yes for key 1; minor: no key 2 script for this row |
| G5.4 take-off, land | 3 seeds; overshoot <= 0.5 m, no bounce, ramp/edge step <= 10 %, dip <= 0.3 m; td vz <= 0.8, tilt <= 10, no re-lift | f10/g5/auto_land10_s{1-3}, auto_tour_s{1-3} (*.check.txt) | PASS 6/6 | auto_land10 3/3 PASS (key2_g54.txt, key2_g54_land.txt); auto_tour take-off not key-2 scored | yes (take-off and land are in the land10 flights, keyed twice) |
| G5.4 RTL | 3 seeds; RTL height error <= 1 m | f10/g5/auto_tour_s{1-3}.check.txt | PASS 3/3 (0.045-0.062 m) | none | key 1 only; minor: RTL height has no second key |
| G5.5 o1-o7 | 3 seeds each; H RMS <= H_lim (Q25 B: max(0.5, 0.125 v_rms)), V RMS <= 0.3 m | f10/g55/*_s{1-3} (21 flights), G5_5_RESCORE_Q25.md | 21/21 PASS under Q25 B (as written 20/21: o2 s1 0.5027 > 0.5, the one case the amendment changes) | 21/21 PASS | yes |
| G5.5 offb_vel_step | 3 seeds; vx RMS <= 0.2, end |vx| <= 0.1, dz <= 0.3 | f10/g55/offb_vel_step_s{1-3} | PASS 3/3 | PASS 3/3 | yes |
| G5.6 | not tested (owner Q8(b), S175) | n/a | n/a | n/a | n/a, nothing to score |
| G5.7 | mode_switch10, 3 seeds; thrust step <= 20 %, attitude jump <= 5 deg, validity leaveP | f10/g5_modes/mode_switch10_s{1-3} | PASS 3/3 (worst 3.98 deg) | PASS 3/3 | yes |
| G5.8 hover (rc, link, offboard loss) | entry <= 1 s after timeout, excursion <= 1 m; 3 seeds (5b "3 seeds per row") | f10/events/g5_events_s1 (g5_rows.txt, key2_g5rows_s1.txt) | PASS 3/3 rows, SEED 1 ONLY | PASS, seed 1 only | missing: seeds 2 and 3 |
| G5.8 at 3 m/s (same three) | each also at 3 m/s; excursion per Q8 add.3 (i) (deviation from commanded setpoint, <= 1 m) | none at freeze-10 or freeze-9. Only a pre-amendment probe, f9-era `results/g5_events_s147_move/` (S147, "not counted", excursion FAIL by the old definition) | none | none | missing: the 3 m/s flights (batch2.sh notes "`--moving` NOT flown (G5.8 3 m/s cut)"; no decision record of the cut found) |
| G5.9a kill | motors 0 within one command period (1.25 ms) of actuator_armed.kill rise (Q8 add.2 A); seed 1 | f10/events/g5_rows.txt, key2_g5rows_s1.txt | PASS (0.00 ms after kill rise, spacing 1.25 ms) | read on the gate's definition: PASS. Key 2 prints "outputs 0 ... +0.00 ms after kill rise, +2.50 ms after switch"; the 2.50 ms is the switch to kill-flag latency (commander, reported not gated by the amendment). The FAIL in G5_SCORES.md compares that switch reference to 1.25 ms, a reference the amendment replaced | seed 1 only; missing: seeds 2, 3 |
| G5.9b rearm states | all INDI states zero at re-arm (S145 definition) | same | PASS (none non-zero) | values: blend, hold_cycles, torque_filtered, rate_sp_dot all maxabs 0 at arm and over first 0.2 s. No verdict line printed; every value is 0, i.e. within the limit. PASS by reading | seed 1 only |
| G5.9c first second | motor command change <= 5 % of full scale | same | PASS 0.01 % | 0.93 % of full scale (W = 2700), <= 5 %, no verdict line. PASS by reading (different measure, same direction) | seed 1 only |
| G5.9d take-off after re-arm | passes G5.4: handover step <= 10 % hover, dip <= 0.3 m | same | PASS (4.7 %, 0.000 m) | PASS | seed 1 only |
| G5.10 stabilized full-scale | INDI 3 seeds; no LOC, tilt <= MPC_MAN_TILT_MAX + 5, att err <= 5 deg 1 s after centre (Q17 A); valid all-4 >= 0.99 | f10/g510_stab/indi_stab_s{1-3} (score_key1/key2) | PASS 3/3 (tilt 35.50, err 0.24) | PASS 3/3 | yes (PID reference is a reference, not gated; freeze-9 PID kept) |
| G5.10 SAT part | Q21: valid only if all 4 motors >= 0.99 for >= 1 s in both stacks, else dropped | `results/g510_q21_s187/` (INDI max motor 0.869, PID aborted) | INVALID, SAT part dropped per Q21 | n/a | yes: Q21 drops it (S187 evidence is freeze-9 config; rule makes it not a freeze-dependent row) |
| G5.11 ekf_yaw | 3 seeds; tilt command jump excess <= 1 deg (event minus p95 no-event, Q12 D), excursion <= 0.5 m, no oscillation; "second key before the verdict counts" | f10/events/g5_events_s1 only (g511.txt) | PASS seed 1 (jump 0.61, excess -0.54, exc 0.088 m, osc no) | key2_g511 run on seed 1 (see below): jump 0.610 deg, exc 0.087 m, PASS. Oscillation not computed by key 2 | missing: seeds 2 and 3 |
| G5.11 ekf_xy | 3 seeds; Q12 B: truth excursion <= 0.5 m and no oscillation (tilt jump reported only) | same | PASS seed 1 (0.240 m, osc no) | key 2 excursion 0.240 m (<= 0.5 PASS under Q12 B); the script prints FAIL because it still applies the 1 deg tilt jump (7.383 deg), which Q12 B removed for xy. Oscillation not computed by key 2 | missing: seeds 2 and 3 |
| G5.11 z reset | not tested (owner Q8(b)) | n/a | n/a | n/a | n/a |

## G5.11 key 2 run
Script `results/g511_fix_s161/key2_g511.py` hardwires seeds 1-3 and its own directory. Run on a copy (the original untouched; copy in /tmp, directory and output name changed, seeds limited to 1) on host python, no docker. Output: `results/freeze10_s193/events/key2_g511_s197.txt`.
- seed 1 ekf_yaw: t_a 44.995 s, nav_state [4], one counter increment, tilt jump 0.610 deg (limit 1), excursion 0.087 m: PASS. No-event tilt jump range 0.71-1.23 deg (key 2 reads yaw jump 0.61 below the no-event max, so no reset-specific spike).
- seed 1 ekf_xy: tilt jump 7.383 deg (the script's legacy 1 deg rule prints FAIL; Q12 B says not judged on tilt for xy), excursion 0.240 m (limit 0.5): PASS on Q12 B.
- Key 1 and key 2 agree to 0.003 m / 0.001 deg on every value.
- Seeds 2 and 3 do not exist at freeze-10 (nor freeze-9, freeze-8). The only 3-seed G5.11 flights are `results/g511_fix_s161/g5_events_s{1,2,3}` (firmware d1b65d0f09, before freeze-7 to freeze-10 changes); they were not run through key 2 here because D-FREEZE-10 does not carry them over (they would be evidence for a different firmware).

## Gaps
1. G5.11 x2 (ekf_yaw, ekf_xy), G5.8 hover x3, G5.9a-d: seeds 2 and 3 missing (GATES 5b "3 seeds", G5.11 text says 3 seeds explicitly). Smallest action: fly `g5_events.py` seeds 2 and 3 at FREEZE-10 (step `ev` in `results/freeze10_s193/queue.sh`, two flights, about 2 x 5 min), then re-run g5_rows_check, g511_check, g5_rows_key2 and key2_g511 (extend the seed tuple). Alternative with no flight: the orchestrator or owner records that the 1-seed hover confirm of D-FREEZE-6/7 stands for events (precedent in DECISIONS), which is a decision, not a re-score.
2. G5.8 at 3 m/s: written in the row ("each at 3 m/s and at hover") and defined by Q8 add.3 (i); never flown at a freeze, only a pre-amendment probe. Smallest action: flights (`g5_events.py --moving`, runner support exists since S147) with the Q8 add.3 (i) excursion scorer, or an owner/orchestrator decision to drop it. A "3 m/s cut" is mentioned only in `g5_freeze_s157/batch2.sh`, with no decision record found.
3. G5.11 key 2 does not compute oscillation and still prints FAIL for xy on the legacy tilt rule; its excursion values are the Q12 B check. Re-score only: judge xy on the excursion line and read the key-1 oscillation result (no sustained oscillation); no script change made here.
4. Minor, re-score only (no flight): G5.9a key 2 verdict is PASS on the gate definition (+0.00 ms after kill rise); G5_SCORES.md labels it FAIL because it uses the switch reference. G5.9b and G5.9c key 2 print no verdict, values in the limit. G5.3 mission and G5.4 RTL have key 1 only; no key-2 scripts exist for them (as at freeze-9).

## Resolved points
- G5.5: under Q25 B all 24 rows PASS both keys; the single as-written FAIL (o2 s1, 0.5027 vs 0.5) falls under the new limit 0.5685 (the amendment's expected 0.62 assumed cruise speed; the re-score uses the scored window, 0.5685).
- G5.7: 3/3 PASS both keys, was 3/3 FAIL at freeze-9.
