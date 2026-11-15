# Journal (append-only, not read at launch)

- 2026-11-15 S1 (launch 20261115-164208): stage 0. Committed workspace and review (df144c0c4b). Wrote STATE, DECISIONS, ANOMALIES.
- 2026-11-15 S1: T1 reference-airframe data table (sonnet). D-1, D-2 recorded. GATES.md G1 draft. Session ended at budget.
- 2026-11-15 S2 (launch 20261115-170222): D-3 recorded. Launched T3 (gz model quad5in + SITL airframe + PID hover/step check, output design/ref_airframe_model.md) and T4 (outer-loop requirements from mc_pos_control source, output design/outer_loop_requirements.md), both sonnet.
- 2026-11-15 S3: reference airframe quad5in model + SITL airframe committed, flies with stock PID (design/ref_airframe_model.md).
- 2026-11-15 S3: outer-loop requirements R1-R36 written (design/outer_loop_requirements.md); review pending.
- 2026-11-15 S4: requirements review T5 (15 new items, 4 blocking); outer-loop candidates r1 (A preferred); local-position rate 125 Hz in SITL.
- 2026-11-15 S5: outer-loop review r1 (fable): A recommended with 5 conditions, B deferred, C rejected (F10).
- 2026-11-15 S6: route check 05 (balance too design-heavy, bench/G1 next); outer-loop candidates r2 (A amended for F1-F17).
- 2026-11-15 S7: metrics.py ported with analytic trajectory reference (T9), self-test passes; review r2 deferred to a >= $3 session.
- 2026-11-15 S8: T10 metrics time base verified (no t0/origin correction), timebase_check.py added.
- 2026-11-15 S8: T11 second key confirms metrics.py trajectory error (3 digits, 3 runs).
- 2026-11-15 S11: route check 10; outer-loop review r2 (1 blocking, N1) and candidates r3; determinism pre-study reproduces A-7 (arm time spread 2.2 s sim).
- 2026-11-15 S14: moved finished S12/S13 next-action blocks out of STATE: 0'. S12 (done/partly): (a) runner: arm and offboard at fixed sim times, and call metrics.py at the end (sonnet, ~12 calls, two keys: haiku re-checks sends.csv vs run.json); re-fly 3 same-seed hovers (haiku, as T18 brief); if spread persists, the cause is below the runner (gz/PX4 threading), bisect with speed factor. (b) outer-loop review r3, opus, narrow. (c) then final GATES.md G1 and remaining second keys (route check 10). 0. S13: (a) determinism: spreads stay 10-25 % with windows aligned to 0.33 s: (i) why arm lands 0.28-0.61 s after 30 s and why arm_late_s is missing; (ii) cause below the runner (gz/PX4 threading): bisect with speed factor and compare gz ground truth vs PX4 timestamps on r1..r3; then define the G1.6 tolerance in GATES.md.(b) DONE S13 (r4 + Q1). (c) final GATES.md G1 and remaining second keys.
