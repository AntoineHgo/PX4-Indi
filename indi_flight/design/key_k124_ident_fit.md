# K124: second-key review of bench/ident_fit.py (+ tests/test_ident_fit.py) against D-IDENT (ii)(iii), ident_concept sec 2

Reviewer did not read results/ident_m3a_s123/fit_s124.md. Scratch mutations in /tmp/k124 (repo untouched).
Library ident_iv.py taken as reviewed (K120); only its use here is judged.

## Mutation results (test functions called directly, 3 tests)
| mutation (scratch) | result |
|---|---|
| none | 3/3 pass |
| g1 := OLS instead of IV | 3/3 FAIL (good) |
| instrument := regressor x | 3/3 FAIL (good) |
| regressor time-shifted +5 samples, latency compensation ON (default) | 3/3 PASS (test blind) |
| shift +5, compensation OFF | 3/3 PASS for 2 tests; recover test with delay=2 and comp OFF fails (G1 1594) and nocomp+shift5 3/3 fail |
| regressor filtered with 5 taps vs 15 for y and z (full driver, comp ON) | no test exists; G1 = 924 vs truth 1700 (-46 %), CI +-27, J = 103 (df 8), F fine, nothing flags it |
| regressor = ZOH every 5 samples | G1 1701, comp lag 3.6 samples, J 32.6 (test absent) |

## Findings

### BLOCKING
1. BLOCKING (iii). No deliberate-mismatch self-test exists that fails. test_ident_fit.py has three tests (recovery, OLS bias, saturation) and
   none injects a filter or delay mismatch between regressor and regressand. Worse, the J-scan compensation (ident_fit.py:40-48) absorbs a
   +5-sample regressor shift (mutation passes 3/3), so a delay mismatch cannot be made to fail through the driver at all; a filter
   mismatch (5 vs 15 taps) gives a G1 error of -46 % with a tight CI (+-27) and nothing in the driver or CLI rejects it.
   Fix: add tests that (a) call iv.prepare_regression-level code with a different tap count on x and assert |G1 error| > 10 % AND J gate
   trips; (b) shift x by >= 5 samples outside the scan range (or with compensate_latency=False) and assert failure; (c) add a driver-level
   verdict (item 2) so that "fails" is observable as a returned flag.
2. BLOCKING (ii). Weak-instrument and misalignment are reported but never gated. fit_axis/main (ident_fit.py:104-114) print F and J and
   return exit code 0 whatever the values; only the test asserts f > 10. D-IDENT (ii) says weak instrument = failed ident. Fix: return a
   `verdict` dict (F per axis >= 10 on a HAC/robust first-stage F, J p-value > chosen alpha, shift not on scan boundary, CI/G1 < limit,
   excl_frac < limit) and a nonzero exit code when failing.
3. BLOCKING (ii). The first-stage F (ident_iv.py:187-194) is the classical homoskedastic F on 17 lagged instruments while the disturbance
   (and the regressor, which is feedback-driven) is strongly autocorrelated; the HAC treatment applied to se/J is not applied to F, so F is
   overstated and the "F > 10" threshold is not what it claims. Driver should report a HAC (Kleibergen-Paap-style or Newey-West Wald)
   first-stage statistic, or at least F computed with the same hac_lags; and report it for the regressor after the chosen shift.

### MAJOR
4. MAJOR (iii, item 3). Latency shift chosen by minimising J (ident_fit.py:40-48) is a pre-test: the reported se/CI (ident_fit.py:48-49,66)
   are conditional on the chosen shift and take no account of its selection variance; I measured a 1.57-sample pick for a true 2-sample delay
   (base G1 1660, -2.4 %, CI +-60 so within CI, but the shift error is a systematic bias channel). Minimising J selects the shift that makes
   residuals least correlated with the instrument, which also absorbs other misalignment (any x/y phase error, the staircase of item 6) into a
   "latency", i.e. it hides a (iii) violation instead of reporting it. Scan uses hac_lags=40 and the final fit 400 (ident_fit.py:41,48), so J
   at selection differs from the J reported. Candidates are only 0..8 samples, one sided, with no boundary check (ident_fit.py:40): a true
   lag of 9+ or negative lag gives a boundary minimum silently. Not tested (no test with delay != 2, non-integer, or out of range).
   Fix: scan symmetric range wider than any physical latency; fail if argmin on the boundary; report the J curve and the shift; widen CI by
   profile over shifts within J_min + chi2 band (or bootstrap the choice); use same hac_lags in scan and final; state the selected lag as an
   estimate of ERPM_DLY and compare with the independent M3 estimate.
5. MAJOR (iii). Filters are not actually identical on both sides. Regressand = np.gradient (central difference, gain sinc(w dt), -3.6 % at
   60 Hz, ident_iv.py:77) then 15-tap MA; regressor/instrument get only the MA. The differentiator is an extra filter on y only. Also the
   shift for non-integer c is done by np.interp on the regressor only (ident_fit.py:41,48): half-sample linear interpolation attenuates x
   by cos(pi f dt), 2.8 % at 60 Hz, again only on x. These are in the 60 Hz upper end of the multisine and bias G1 by up to a few % (sign:
   y smaller or x smaller respectively, partially cancelling, not guaranteed). Fix: apply the same differentiator to x and z (differentiate
   nothing on x; instead filter x with the central-difference transfer function, or use a one-sided difference on both through a common
   FIR), and apply the fractional delay to y/z/x consistently or restrict to integer-sample shifts with the residual in a fractional-delay
   FIR applied to all three.
6. MAJOR (item 1, zero-order hold). The regressor is a ZOH of a decimated topic. In results/ident_m3a_s123/pos0/flight.ulg
   actuator_torque_measured has 800 Hz timestamps, but its value changes only every 2.4 samples on average (65 % of consecutive samples
   identical; timestamp_sample advances on 92 % of the unchanged samples), so timestamp_sample is not the time of the underlying ESC
   sample and the 800 Hz resample guard in resample_to_grid (ident_iv.py:36) cannot detect it. The driver linearly interpolates a staircase and
   the J scan then absorbs the mean hold delay (about 0.9 ms) into the "latency". Mutation with a 5-sample hold shows the J scan picks
   3.6 samples and J rises to 33. Fix: in load() detect repeated values (changes per second) and either decimate the grid to the true
   telemetry rate (<= measured update rate) or refuse; use the telemetry update timestamps (esc_status) as sample times; also drop
   actuator_torque_measured rows with valid == false (the field `valid` is not read, ident_fit.py:75-86).
7. MAJOR (item 4). Saturation mask is a ZOH of a 200 Hz topic and is not per-axis: control_allocator_status has only the scalar
   torque_setpoint_achieved (checked in the log), so the per-axis branch at ident_fit.py:85-86 is dead and one saturated motor excludes
   data on all axes (acceptable, conservative, but should be stated). The mask uses `timestamp` (publish time) while everything else uses
   timestamp_sample (ident_fit.py:84), and exclusion is only +-7 samples (the MA support, ident_iv.py:86) around a 5 ms hold, so the 5 ms
   before a flag publication and the time from sample to publish are not covered; the 32 instrument lags are also not masked (a z lag
   reaching into a saturated period is legal, since z is exogenous, ok). Exclusion applies to y and x rows together (both sides), good.
   Fix: dilate the mask by the filter support plus the hold period plus the maximum shift, and use timestamp_sample if available.
8. MAJOR (self-test realism, item 5). The synthetic plant shares the driver's assumptions: delay is an integer number of samples implemented by
   np.roll (test:35) which is exactly what the shift step can undo; gyro is the exact integral of alpha (no gyro filter, no actuator
   lag), u acts instantly (no ACT_TC), the same 800 Hz grid for all topics, no ZOH telemetry, no sub-sample delay, no non-white
   quantisation. np.roll also wraps the last samples to the start (harmless inside the 4-56 s window). Loop gain is only 25 rad/s
   (alpha = -25 w) so feedback is weak; INDI at higher bandwidth was not exercised. Only one delay (2) and one seed per test. The "OLS is biased" test
   compares |IV err| < |OLS err| only; it does not check that OLS is biased by a meaningful margin. Fix: add first-order actuator
   (tau ~ 20 ms) + a fractional telemetry delay with ZOH decimation, vary delay in {0,1,3,6,2.5}, add a mismatch family (item 1).
9. MAJOR (iii/item 4 reporting). Reported CI is conditional on shift and uses 95 % = 1.96 se with HAC lags 400 at 800 Hz (0.5 s); the first stage
   uses only injection lags 0..32 step 2 (40 ms span) although the closed-loop path from z to x is longer if the loop has low bandwidth;
   not tested. Minor in effect, stated for completeness.

### MINOR
10. MINOR. Window trimming: t_grid = arange(t0, t1) (ident_fit.py:57) in log seconds; MA edges (7 samples) and shift (<= 8 samples) NaN
   rows are dropped by keep (OK). No transient-start check (the window must be chosen by hand with no check that the multisine has
   started; CLI requires --t0/--t1 so fine). `fs=800` hard-coded (ident_fit.py:25, main) while the guard only checks the grid is not finer than
   the sources; a log with gyro at 1 kHz would be silently decimated by interpolation without anti-alias.
11. MINOR. Intercept present (ident_iv.py:162, in both IV and OLS) and reported (intercept field). Level regression with intercept is
   equivalent to the increment form as stated in the docstring (OK). The instrument z is indi_rate_status.inject (exogenous, command side),
   resampled at timestamp_sample (gyro cycle time) and not shifted: correct in principle. However z is the injection in controller
   command space while x is the measured response; it is never checked that inject[] and torque[] are in the same axis order (roll=0), cheap
   assertion.
12. MINOR. ident_fit.py:64-65 passes `exclude` as NaN into latency_by_xcorr via beta*x, using the OLS-like G1 scale; result is only
   reported ("lat_s"), not used for the shift, but its docstring (line 29-33) still says pass 1 fits by xcorr and "lag from the J scan"
   inline, which is confusing; update the docstring.
13. MINOR. Test file has no ulog-load test (load() untested, including the sat field fallback line 85-86 and the t_log0 subtraction that
   assumes timestamp_sample shares the clock of ul.start_timestamp).

## Summary of answers to the five asks
1. Units/signals: regressor is actuator_torque_measured.torque[k] (omega/W_MAX)^2 normalised, regressand gyro derivative, instrument inject[k]
   (not derived from feedback): OK. Time base timestamp_sample except the sat mask (publish time). ZOH present in the regressor (finding 6),
   and in the sat mask (finding 7).
2. Same filter and delay: MA identical, differentiator and fractional shift are not (finding 5). No failing mismatch self-test (finding 1).
3. J shift: not statistically clean; CI conditional; boundary unchecked; barely tested (finding 4).
4. Intercept yes; saturation both sides yes but flag coarse (7); window trimming by NaN drop OK (10).
5. Self-test closed-loop yes but shares assumptions (8); mutation table above: OLS/no-instrument break it, delay mismatch and filter mismatch do not.

BLOCKING count: 3 (findings 1, 2, 3).
