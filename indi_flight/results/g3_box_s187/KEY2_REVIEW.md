# KEY2 review: G3 box (Q22) code against GATES.md S187 amendment

Scope: git diff of bench/g3_sample.py, g3_run.py, tests/test_g3_sample.py; model_variant.py path. Read-only.

1. G1 error: OK. `G1_ERR=(0.8,1.2)`, `logu` per axis (g3_sample.py:29, :169). e = controller/plant. The controller side is changed:
   k = e / I_scale is written to MC_INDI_G1_R/P/Y = base x k (g3_run.py:98-109). The plant G1 follows the inertia draw (I_scale). Direction correct.
2. tau: OK. slow = tau draw, fast = max(tau/asym, 0.5) (g3_sample.py:176-182). Not inverted: down slow. Inverted (10 %): up slow.
   Hook sends tau, tau_up/tau, tau_down/tau (g3_sample.py:291-293). model_variant.py:98-99 multiplies tau x own, so the sdf gets
   tau_up and tau_down exactly (to 1e-6 r6 rounding). Nothing downstream multiplies by asym. Tests confirm mv["tau"]*mv["tau_up"] = f["tau_up"].
3. Corners: OK. C1/C2/C4 pin g1 u = 1 / 0 / 1, which gives 1.2 / 0.8 / 1.2 (test_corner_pins_exact). Other pins unchanged.
4. Seed behaviour: OK. Campaign seed 173, n 300, HEAD against working tree: all 300 runs identical in every factor except g1_err, g1_ctrl_mult,
   tau_up/down/asym. px4_params other than MC_INDI_G1_*, and model_variant keys other than tau*, also identical. tau_scale value is identical
   (its unit string changed only; meaning is now "slow direction").
5. Tests: test_g3_sample.py failures 0 (incl. new test_q22_box_2000_draws); test_g3_run.py all PASS.

Findings
- BLOCKING: none.
- MAJOR: none.
- MINOR: bench/g3_osc_margins.py:52-53,93-94 still use the old meaning (down = scale x asym). Valid only on the old S173 draws.
  Do not point it at new-box draws (g3_box_margins.py is the new tool).
- MINOR (design consequence, not a bug): the fast side floor makes asymmetry vanish for tau <= ~0.5 x asym. In the first 20 draws, 9 of 20
  have tau_up = 0.5 exactly and tau_down = tau_scale. C5 (tau x0.5) is therefore symmetric. Note it in the pre-test report.
- MINOR: tau_asym.value is now the realised ratio (g3_sample.py:182). The drawn ratio is in "drawn_ratio". Readers of old scripts that
  use tau_asym.value as the draw may misread it.

Verdict: OK to fly the pre-test.
