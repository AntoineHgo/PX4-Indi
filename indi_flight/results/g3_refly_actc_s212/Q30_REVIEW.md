# Q30 independent review (S214, 2026-11-23, read-only reviewer agent)
Verdict on option B: AGREE WITH CHANGES (written rule right; as proposed it puts a transient in the hold and the
override mechanism cannot lengthen a hold).
- Evidence correction: ITEM3_DECOMP "gust onset 58.12 s = after window" mixes time bases. 58.12 is the PX4-time onset
  of the gust_x profile at traj start (run_022/disturbance_trigger.json, sched.txt); the window 54.42-57.42 is on the
  ulog base (offset 21.41 s). The gust runs onset+12..13 s = ~48.7-49.7 s ulog, ~5 s before the window, inside traj.
- Transient placement: AGREE WITH CHANGES. All G3 events are anchored at the main segment start (g3_run.py:165-221,
  run_scenario.py:1200): saturation/weak motor +0, eRPM loss/frozen +1..5 s, gust +12..13 s. A longer hold moves none
  of them into it, but the gust_x profile ends at onset+28 s (~10.2 s into a 20 s hold) and disturbance.py:362-367
  clears the whole wrench (steady wind and drag). Sag ramps over the whole scenario (run_scenario.py:1226). Needed:
  steady wind to the scenario end, sag ramp fixed at its drawn 10 s. GATES 2 and 3 do not conflict; GATES 3 "injected
  at the start of the hold" contradicts the code (traj start).
- Stop C212 rather than finish: AGREE, moot (C212 halted on the run-024 LOC; G1.6 sequential rule GATES:22, :300; any
  change touches frozen files g3_chain.sh:52-60). C212 items 1-2 remain evidence, not pooled.
- Hold via per-run overrides: DISAGREE. scenario_overrides.py:22 ALLOWED has no segment/hold key. Add G3-only scenarios
  (`_traj_segments(LEMNISCATE_O1, 20.0)`, pattern scenarios.py:102-108) and update the o1_lemniscate references in
  g3_score.sh:26, g3_checks_key2.py:225, g3_run.py:30-33. o1_lemniscate is used by G5 (g5_freeze_s157,
  g55_rescore_q25.py:67, lag_chain.py:146): leave it.
- Scorer: g3_score.sh:25 t0 = t1 - hold dur_s (whole hold) -> t1 - 10. Key 2 takes key 1's t0/t1 (g3_chain.sh:523-529):
  not independent; its own default (key2:100) already follows the spec.
- Cost: +17 s sim = +4.25 s wall at speed 4 (~+8 % of the 55.4 s cycle, ~+21 min per 300 runs).
- Stick scenario stick_zsine_o6 has the same 3 s hold (scenarios.py:163); item 6 needs the last 20 s at zero sticks;
  neither key implements items 5 or 6.
- Thresholds: no change.
