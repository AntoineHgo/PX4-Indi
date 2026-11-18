# T193 independent review: ratesp_csv.py (code to spec, attitude_break_s86 section 6)

Verdict: AGREE WITH MINOR.

- Sign/direction: OK. margins_est._finish L = -Gyd/Gxd with Gyd=Syd/Sdd, Gxd=Sxd/Sdd, i.e. L = -Y/X (y=-Lx). Fields read
  match spec (pre_inject=y, inject=d, applied=x, timestamp_sample). Mutant (L=+Gyd/Gxd) fails test_known_loop (PM -104.4 vs 75.6);
  x/y swap gives 1/L0 and test_swapped_xy_detected passes. Self-test would catch both.
- Bins: log_bins(fmin,fmax,Tp) is the same grid the C++ generator uses per the test (not re-verified against the firmware generator).
- Whole periods: FFT path uses len//N periods from window start, discard 1; LS path floors on (T+dt)/Tp. Truncated partial period and
  3 dropped samples (LS path) give exact PM in a scratch run.
- MINOR: window() is first..last d!=0 and does not detect interior d==0 gaps (gate reopen restarts the sequence, see
  IndiInjectionStep.cpp); validity() only reports max|x-y-d| (flags a zeroed-d gap at 0.52 but nothing enforces it) and max_gap in time.
  Suggest also reporting count of d==0 samples inside the window.
- MINOR: validity n_periods_complete uses floor(T/Tp) (spec-side count is (T+dt)/Tp); can under-report by one.
- MINOR: x,y are float32 in the log; the 1e-6 bound on |x-y-d| from the spec may be hit by rounding when rates > ~4 rad/s.
- MINOR: the test never exercises jittered timestamp_sample (the real-log LS path is only checked in my scratch with dropped samples),
  nor held/duplicated rows. ratesp_csv.main has no test.
