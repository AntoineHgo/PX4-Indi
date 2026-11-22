# Self-test of bench/ident_actc.py (ACT_TC output-error estimator)

Run: `python3 bench/tests/test_ident_actc.py` (prints all rows) or pytest on the same file. Needs numpy only (scipy and
pytest are not installed on the host; the refinement is a pattern search, no scipy). Runtime 258 s single core.
Synthetic data only, no SITL, no firmware.

## What is tested
Plant at 800 Hz: asymmetric first-order lag (exact discretisation), integer-sample delay, y = 0.02 + 0.95 x,
rpm_max 10000, hover 0.4. Command: 12-tone multisine 3-60 Hz, 0.025 per tone. tau_slow in {16.5, 33, 99} ms x asymmetry
{1, 3 down-slow, 3 up-slow} (slow/3 on the fast side, so tau down to 5.5 ms). Noisy cases: rpm noise 25 rpm rms, rpm
quantised to 20 rpm. Telemetry frames = whole 1.25 ms samples of extra delay.

## Results (GATES 6c estimator limits)
| Case | Limit | Worst result | Status |
|---|---|---|---|
| Noise-free, 9 plants x delay/frames (0,0) (10,0) (5,2) | each tau 2 %, d within 1 sample, quality pass | tau 0.19 %, d exact | met |
| Noisy, 9 plants x (0,0) (10 ms,3) (4 ms,1) | each tau 10 %, quality pass | tau 0.67 %, d within 0.25 ms | met |
| Closed loop (u = multisine - 1.5 x noisy delayed y), 9 plants, 10 ms + 3 frames | 10 %, quality pass | tau 1.02 %, d exact | met |
| Fit forced 10 ms off (d=2 and d=18 samples vs true 10), 3 plants x noise/no noise | must fail quality | 12 of 12 fail | met |
| Constant command (noise / no noise), and 0.002 per tone with noise | must fail quality | all fail | met |

Informational, asymmetric 3: tau_sym = 0.61-0.62 x tau_slow and 0.91-0.94 x tau_mean (tau_up 5.5/tau_down 16.5: 10.3 ms;
11/33: 20.4 ms; 33/99: 60.2 ms), so the symmetric tau sits well below the slow one; the asymmetric pair is recovered.

## Quality check (thresholds chosen from this test, before SITL)
Fail if any of: normalised residual rms/std(y_hat) > 0.35 (good fits <= 0.28, noise dominated at tau 99 ms);
residual autocorrelation magnitude at 25-125 ms lags > 0.08, evaluated only when the normalised residual > 0.05 (good
noisy fits <= 0.02, forced mismatch 0.12-0.44); curvature Hessian at the minimum not positive definite, or 1-sigma
relative se of tau_up/tau_down > 10 %, or delay se > 1.5 samples (good fits <= 0.8 % / 0.04 samples; these never
triggered on the mismatch cases because the inflated noise estimate stays small, the residual checks do the work); command
std < 0.004; delay or tau at the search bound. Both residual checks are needed: tau 99 ms mismatch cases pass one of them.
These thresholds are tuned to my assumed noise (25 rpm) and signal (0.025 per tone); real SITL residuals may need review
before the grid is judged (a pass in SITL is not implied).

## Breakage check
On a copy of the estimator, (a) tau_up/tau_down assignment swapped: test_noise_free fails on the first asymmetric plant
(5.5/16.5 estimated as 16.5/5.5); (b) delay removed from the model: test_noise_free fails (quality flag, delay unrecoverable).
Done on a scratch copy, not the repository file, which was never modified; the repository version passes.

## Not met / unverified
- Nothing in the synthetic limits is unmet.
- Second key (independent review against the design page) not done.
- Real ulg loading (`load_ulg`, CLI, rpm_max from params) untested: no log run here; no known log parameter for rpm_max
  (candidates tried: SIM_GZ_RPM_MAX, MC_INDI_RPM_MAX, ESC_RPM_MAX), so --rpm-max is effectively required.
- Delay is integer samples of the log period (1.25 ms); fractional delays not fitted.
- Closed-loop case uses one gain (1.5) and one noise level.
