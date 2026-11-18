# Second key: D-G3-SAMPLER-K108 code review (commit 3a245d1590)
Self-test run: all PASS, failures: 0.
No BLOCKING. No MAJOR.
(1) M2 matches spec: g3_sample.py:200-205 (peak U[3,9]; steady U[0,min(5,pk-1)]; C4 via wind_s>=1.0 gives steady 5, peak U[6,9]).
  C4 pin is wind_s=1 (line 63). It cannot come from a free draw if LHS u is in [0,1) (not verified here). Other corners leave wind_s at 0 (line 91), so there is no leak.
  Test guards: test_ranges (amp>=1, peak<=9, steady<=min(5,pk-1)) catches a dropped floor or cap. The C4 test (steady==5, peak>=6) catches a wrong C4 peak range. The stratification test covers the peak and the steady/min(5,pk-1) ratio.
(2) M4 correct: g3_sample.py:136,141 (k=e/isc, isc from the same lin(u[ix..iz]) as inertia_scale at :154-155 and as model_variant at :241). The C2 inertia pin (ix=iy=iz=1, line 61) goes through u, so it is consistent. The hooks MC_INDI_G1_R/P/Y use g1_ctrl_mult (:71-73).
  Test (test_g3_sample.py:90-94) asserts k*I==e per axis, isc==inertia_scale, and the hook value==k. It would catch k=e, k=e*I, an axis swap, and the hook still reading g1_err.
MINOR-1: the I_scale-to-plant link is checked via the factors dict only, not against r["hooks"]["model_variant"] ixx/iyy/izz. A mutation in :241 alone would pass.
MINOR-2: nothing asserts that LHS never produces wind_s>=1.0, so the C4 branch could leak if the LHS ever emitted u==1.0. Add assert max(u["wind_s"]) < 1 on LHS runs.
