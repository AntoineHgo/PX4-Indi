# Second key, ident_actc.py vs actc_ident_s208.md + GATES 6c (S208), reviewer without author report
1. Model: PASS. Asymmetric lag, exact alpha, delay via padded u[0] (no roll, correct sign), (a,b) LS, symmetric fit, saturation
   + 0.25 s window, NaN gaps never held in the residual: all as specified. Alignment is latest-at-or-before with 1.5-period age
   limit. timestamp_sample: EscStatus has only `timestamp`, ActuatorMotors has both; code uses timestamp_sample for cmd and
   timestamp for esc (ident_actc.py:263-264). In the pos0 log they are identical, so harmless there. MINOR: use `timestamp` for cmd.
   MINOR ident_actc.py:~245: `tu in (TAU_MIN_S/2, ...)` float equality; exp(log(0.0025)) != 0.0025, so lower tau_at_bound never fires.
2. Self-test independence: plant is its own loop (test_ident_actc.py:30-49), no shared lag code; but it shares the estimator's
   discretisation convention (ZOH, x updated with u[k-d], integer-sample delays only: 0/10 ms + k*1.25 ms, 5+2.5, 4+1.25 ...).
   My independent plant (/tmp/claude-1001/k2/indep*.py: 0.125 ms sub-stepped ODE, tau_up 33/tau_down 99 and inverse and 33/33,
   delay 10 ms total incl. 2 frames, 30 rpm noise + 20 rpm quantisation, closed loop K=1.5): with a ZOH, integer-sample delay
   noise-free: 32.9/99.0/32.9 (exact). With noise: up/down 30.9/95.5 (33/99), 31.5/31.3 (33/33), 95.5/31.4 (99/33), i.e. 3-7 %
   low, delay 10.00 exact; closed loop 31.3/94.1, 30.7/30.6, 93.8/31.1.
   FINDING (MINOR for 6c, would be BLOCKING as a stand-alone acceptance claim): sub-sample delay is not covered. With a plant
   delay 0.625 ms off the sample grid (noise-free, 45 Hz top tone): 33/33 -> 27.7 ms (-16 %, flagged residual_structured),
   33/99 -> 30.4/94.6 (-8 %, PASS), 99/33 -> 92.3/29.4 (-7 %, flagged). So tau can be biased up to ~16 % in the estimator, the
   quality check catches only some of it, and the "within 2 %/10 %" acceptance holds only for grid-aligned delays. Real SITL
   delays and the cmd/esc phase offset are not grid-aligned. Fix: fractional delay (linear interpolation of u) in _stats, or
   add non-integer delays (e.g. 7.3 ms, 4.4 ms + 1.5 frames) to the self-test and report the bias.
3. Thresholds: reasonable, not tuned to pass in a visible way. Residual 0.35 is loose (real log 0.067) but OE white noise does
   not bias tau, so loose is acceptable; structure 0.08 is the sharp one (it caught the fractional-delay misfit), se 10 %,
   delay se 1.5 samples, cmd std 0.004 are plausible. MINOR: with my noisier plant at tau 99 ms (std of signal ~ noise) the
   slow cells give residual_high (norm >0.35), a correct fail but expect SNR-driven invalid cells in the 6c grid (count them).
4. Real-log smoke: results/ident_m3a_s123/pos0/flight.ulg, --t0 21 --t1 78, plant tau 33 ms symmetric. rpm_max 25783 (2700 rad/s
   in rpm) and 20000: ACTC PASS tau_up 34.8 tau_down 33.1 tau_sym 33.9 ms, delay 2.50 ms, resid 0.067, identical taus, gain differs
   (1.013 vs 1.684) as expected. Runtime 25 s each. (esc_rpm there peaks 10371 and median 9500, so true units/scale look to
   be rpm vs 25783 rad/s-derived max: unit of --rpm-max is worth stating in the CLI help; taus unaffected.)
Verdict: 1 PASS (2 MINOR), 2 FINDING (sub-sample delay untested, shared ZOH convention), 3 PASS, 4 PASS.
