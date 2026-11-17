# D-GAP implementation brief (S71, for one sonnet agent in S72; ~30 tool calls, ~$0.6)

Goal: remove the standing altitude error of the INDI outer loop under a thrust gap (decision 2, outer loop), by the
accepted D-GAP law. Serves G3 (weak motor, sag) and lesson 9.

Spec (normative): `DECISIONS.md` section `## D-GAP`, the S71 amendment items 1-5 only. Background if needed:
`design/dgap_review_r1.md` (Q1-Q3). Do not copy the rate-loop blend's reset logic
(`src/lib/indi_rate_control/indi_rate_control.cpp:336-345` snaps the state; D-GAP freezes it).

Code (firmware commit separate from tests and results):
- `src/lib/indi_accel_control/`: blend state b (u units, |b| <= 0.3), coll_model path = previous clamped collective
  through a delay/LPF matching the measured path; coll_f = coll_meas + b; freeze API (hold flag) used by the module;
  reset() leaves b alone; b = 0 only at construction. Time constant tb from a new parameter (default 1.0 s,
  0 = disabled), declared in the module's params/YAML per `.github/instructions/*.instructions.md` matching the paths.
- `src/modules/mc_indi_pos_control/McIndiPosControl.cpp` (~:95-215): pass the hold flag (landed or maybe_landed,
  A3/A8 bypass, e7 edge, mean_u invalid -> also coll_f = coll_model, collective clamped); log b and the hold flag in
  indi_pos_status. Stock modules stay at zero diff against main.
- Unit tests in the lib's test file: amendment item 5 (convergence with tb = 1 s, negative control tb = 0, six
  freeze/recovery cases). Break each rule once (snap or reset b), confirm the test fails, restore; record that in the
  output file.

Flights (Docker only, `indi_project/docker/run.sh`; scenarios and params as in `results/stage5_s70/README.md`):
pre-test gap085_indi_htoff, then loss08_indi, SEQUENTIAL, seed 1, MC_INDI_W_MAX 2700. Score with
`bench/s5_gap_check.py`. Pass: standing |dz| < 0.06 m. Then one land/re-take-off flight with the gap present if the
runner supports it, else write down what is missing.

Output: `results/stage5_s72/README.md` written as you go (diff summary, test results incl. the break checks, flight
table, anything unverified). Commit metrics/run.json/README, not raw logs. A haiku second key on dz follows.
