# Route check 122 (S122)
Inputs: STATE.md, DECISIONS.md (headings, overturn lines, D-IDENT, D-G3-*), ANOMALIES.md, JOURNAL tail, RC118.
No flights run for this check; evidence is what STATE/JOURNAL record.

## 1. Still on the shortest path? What slipped
No, not yet. RC118 set stage 4 (identification) at S119-S121 with "first G6 evidence early". Delivered by S121:
- S119: concept note, D-IDENT proposed, ident_iv killed by OOM. No flight.
- S120: Q6 decided (B), K120 key of the offline estimator, M3a signal survey. Still no flight.
- S121: found that ~94 G3 INDI runs flew the stock rate loop (no MC_RATE_CTL_TYPE 1). Sessions went to the runner
  fix and re-flies of idx 21, 0, 49. S122 is still spent on re-flies.
Net: zero identification flights, G5 build (S122-S125) cannot start on time, G3 has no valid INDI evidence at all
(T118 INDI half, P117, ladder all void). Slip is about 3 sessions on the stage-4 flight and 1 on G5.
Why: (a) Q6=B made the estimator the product: five acceptance conditions (start independence, F-stat, mismatch
self-test, 4 directions, PID cross-check) before any flight counts; (b) the probes flew a controller nobody had
verified from the log; (c) the keyed-estimator-before-data order repeated the pattern RC108/RC113 warned about.
Not slipped: G1 passed; stop rules held (no new anomaly chases).

## 2. Which decision is this a consequence of
D-IDENT with owner Q6=B (INDI flies its own identification) is the cause of the stage-4 delay: it needs a working
INDI flight in ident configuration, a signal path (actuator_torque_measured is absent from the log), and an
estimator proven on flights that did not exist. Root of the void runs: D-GATES-G3G8 (S94) put a 300-run campaign
ahead of defaults and the outer loop, so probes ran for 8 sessions with no wiring check. The base-params overlay
design (pop of MC_* keys into boot env in run_scenario.py) is the mechanism that dropped the flag silently.

## 3. Fresh start on stage 4
- Fly first, estimate second: one hover with the M3a multisine under INDI ident config, log checked for the
  signals the estimator needs (torque measured, esc_status, indi_rate_status c/d/u) before writing keys.
- Build the estimator on that one log, run the x2/x0.5 starts on the same log offline (cheap, no new flights),
  key it only once it has converged on real data.
- Run conditions (i)-(v) as a checklist of cheap offline tests, not a pre-condition to the first flight.
- Put the controller fingerprint (section 4) in before the first flight, since this stage trusts the log most.

## 4. What else may be silently wrong; one check for every run
Candidates (same class: a param or module that never reached the vehicle):
- MC_INDI_POS_EN: S118 note says G3/o1 flew with POS_EN=0 (stock mc_pos_control). All "outer-loop" G3 results
  are stock-position + INDI-rate at best. Stage-5 evidence needs POS_EN=1 in base params.
- Other MC_INDI_* params set after boot (set_param) or popped from the overlay, e.g. injection, ACT_BLD, LEAD,
  ACT_TC, gain scales: an overlay key that is not in the ulog is never proof of use.
- PID runs: could a "pid" run have INDI modules left on? Same fingerprint covers it.
- Defaults file (stage 4 output) values not read by the module (typo, wrong group name).
Single check (add to g3_run.py / run_scenario.py post-flight, write into g3_done.json, mark run VOID on failure):
  controller fingerprint from the ulog =
  (1) every key requested in the run's param overlay equals the ulog initial/changed parameter value;
  (2) indi runs: indi_rate_status has samples at >= 90 % of the expected rate in the flight window and
      rate_ctrl_status/stock MC_RATE_* output absent; POS_EN=1 runs: indi_pos_status present for pos modes;
  (3) pid runs: neither indi topic present.
Cost: one session of ~0.5 (a 40-line script plus a test that a run without MC_RATE_CTL_TYPE fails it), then free
on every future run. Run it retroactively over results/ to list every other void run.

## 5. Next three sessions
- S122 (this one, ~0.5 session): finish R122 idx 0/49 re-fly, commit; write the fingerprint check (section 4) with
  its test and run it over g3_refly_s121 and the last 3 result dirs. Mark void dirs in their README.
- S123 (1 session): stage 4 flight: M3a hover on quad5in under INDI ident config, POS_EN=0 and 1 each one run;
  resolve actuator_torque_measured missing; confirm signals. Only then run ident_iv on that log offline,
  from G1 x0.5/x1/x2 starts. Time-box: if no log, fix the logger only.
- S124 (1 session): estimator verdict on conditions (i)-(iii) offline; defaults file draft (ident config) and one
  G2 cell at x0.5 if the estimate converges. Start G5 build list (base A, POS_EN=1 in base params) in the last
  quarter of the session. If (i) fails, apply the D-IDENT overturn line (fall back to offline ident, Q6 re-ask).
Then RC at S125: G5 build slips to S125-S128; G3 campaign stays deferred until defaults and G5 exist.
