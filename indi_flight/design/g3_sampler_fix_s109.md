# G3 sampler fix, S109 (D-G3-SAMPLER-K108)

Files: bench/g3_sample.py, bench/tests/test_g3_sample.py. Self-test (no pyc, isolated):
`python3 -B -I bench/tests/test_g3_sample.py` (from indi_flight/; also runs under pytest).

## Changes
- M2 wind: peak U[3,9] total, steady U[0, min(5, peak-1)] (LHS unit sample mapped through the conditional law).
  C4 pins wind_s = 1.0 (a free draw never yields 1.0): steady 5, peak U[6,9]. Gust amp = peak - steady >= 1, peak <= 9.
- M4 G1: e (log U[0.5,2]) is the realised controller/plant ratio. Per axis k = e / I_scale (roll->ixx, pitch->iyy,
  yaw->izz). New record fields factors.g1_ratio {roll,pitch,yaw}, factors.g1_ctrl_mult {roll,pitch,yaw,i_scale{...}}.
  factors.g1_err kept (= e, same values). hooks.px4_params.MC_INDI_G1_{R,P,Y}.x_nominal now carries k (was e).
- M3/m7: new tests test_laws_decode_grid (exact law at u = .25/.5/.75, motor index at 4 u values, durations, ramp,
  mismatch constant) and test_laws_campaign_distributions (seeds 11-15: asym share below sqrt3, GNSS latency share,
  mismatch both signs, motor index shares >= 8 %). test_ranges line 99 rewritten, no and/or mix; adds gust >= 1,
  peak <= 9, steady <= min(5, peak-1), k * I_scale == e. LHS strata test: steady replaced by peak and steady/min(5,peak-1).

## Mutation table (mutant sampler in scratchpad, test run against it)
| mutation | result |
|---|---|
| asym log -> linear | CAUGHT (decode_grid, campaign_distributions) |
| GNSS latency uniform -> log | CAUGHT (decode_grid, campaign_distributions) |
| mismatch range (-100,0) | CAUGHT (decode_grid, campaign_distributions) |
| sag scale uniform -> log | CAUGHT (decode_grid only; log vs uniform on [0.7,1] differ 1.5 % in median, not separable statistically at n=96) |
| weak scale uniform -> log | CAUGHT (decode_grid only, same reason) |
| weak motor index fixed 0 | CAUGHT (decode_grid, campaign_distributions) |
| loss motor index fixed 0 | CAUGHT (decode_grid, campaign_distributions) |
| frozen motor index fixed 0 | CAUGHT (decode_grid, campaign_distributions) |
| loss duration 2 -> 3 s | CAUGHT (decode_grid) |
| frozen duration 1 -> 2 s | CAUGHT (decode_grid) |
| sag ramp 10 -> 5 s | CAUGHT (decode_grid) |
| M2 old gust law (steady U[0,5], amp = max(peak-steady,0)) | CAUGHT (ranges, lhs_stratification) |
| M2 min gust 1 -> 0.5 m/s | CAUGHT (ranges, lhs_stratification) |
| M2 C4 peak U[6,9] -> U[3,9] | CAUGHT (ranges, corner_pins_exact) |
| M4 k = e (no division by I_scale) | CAUGHT (ranges) |
| M4 k = e * I_scale | CAUGHT (ranges) |

Determinism: `campaign 7` written twice, `diff -r` identical; test_determinism_bytes also green.
Self-test: all 11 tests pass; campaign-distribution test loops master seeds 11-15.
Not verified: consumers outside bench (run_scenario / g3 runner) of MC_INDI_G1_* x_nominal now receiving k instead of e; none searched beyond bench/.
