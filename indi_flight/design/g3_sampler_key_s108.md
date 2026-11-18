# G3 sampler second key (S108): `bench/g3_sample.py` and `bench/tests/test_g3_sample.py` vs GATES.md 196-305

Read-only review. Independent check: `campaign 11 --n 300` regenerated to a scratch dir and recomputed from the JSON with
`scratchpad/chk.py`; 20 mutation runs of the self-test (a mutated copy of the sampler plus the unchanged test file).
Process note: the design note and the code were fetched in one parallel call, so I had the author's text in view before
writing section 1. Section 1 findings are from code, spec and my own runs. The saturation and wind points were
already in my notes from reading the code.

Totals: BLOCKING 0, MAJOR 4, MINOR 8.

## 1. Findings (code to spec)

### What matches (recomputed, n=300, master 11)
- Ranges, min/max over 300 runs: G1 err 0.5-2.0 on all three axes; tau 0.5-3.0; asym 0.352-3.0 (no value <1 without the
  inverted flag); delay 0-10 ms on 1.25 steps; mass 0.7004-1.3; inertia 0.70-1.30; sag 0.70-0.995; weak 0.70-0.998; telemetry
  latency 0-3; dropout 0.002-0.2; vibration 1.005-5.0; GNSS 80-250; steady wind 0.007-5.0; gust peak 3.02-9.0; loss start 1.01-4.98.
- Conditional shares in the 240 LHS runs: sag 0.40, weak 0.30, dropout 0.40, loss 0.20, frozen 0.20, inverted 0.10,
  GNSS matched 0.50. Modes 0.70 / 0.20 / 0.10 (LHS), 0.70 / 0.197 / 0.103 (all 300).
- Laws: asym log mean/ln3 = 0.503 (log-uniform; linear would give about 0.41). LHS in log space for vib, tau, G1 roll: all
  240 strata hit once. Sampler seeds 300 distinct, gz seeds 300 distinct.
- GNSS: matched runs 0 violations of ekf == latency; no mismatch beyond 100 ms. One mismatched run has offset 0 (ekf == latency), harmless.
- Corners: 10 each of C1-C6. C1, C2, C4, C5, C6 pins are exact. C3 pins saturation, gust peak 9.0 and mass 1.3. Saturation
  scale is 0.351 = 0.27 x 1.3 (consistent with spec "2.0 x hover of the drawn mass").

### MAJOR
- M1 Saturation share is 10 runs (3.3 % of 300, 16.7 % of corners), C3 only. The spec row reads "10 % of runs (inside the
  corner set)", which is 30 runs, or at least reading 10 % of the corner set. The code takes a third reading, and the
  test asserts it (test_ranges: `sat["on"] -> corner == "C3"`; LHS never saturates). It is disclosed (design choice 4) but
  not resolved: owner or orchestrator must pick, because the saturation corner is the only draw that saturates and 10 runs
  is the whole evidence for it. Evidence: chk.py `share sat all 0.033`.
- M2 C4 and, to a lesser degree, the LHS runs have no gust. `gust_amp = max(peak - steady, 0)` with peak U[3,9] total and
  steady U[0,5]: P(peak < steady) is about 6.7 % analytically (4.2 % in the LHS runs, 3 of 10 C4 runs measured). Spec C4
  is "wind 5 m/s plus gust" and pass item 5 recovers "after each injected event (gust...)". Steady 5 forces no-gust whenever peak < 5. Fix: pin or
  redraw so the gust amplitude is above 0, or define the draw as gust amplitude on top of steady (then total can reach 10, past the owner "9 m/s peak").
  Evidence: C4 `nogust 3`, all-run `nogust 0.043`.
- M3 Self-test does not guard the stated laws for several factors (mutation runs, test file unchanged, mutated sampler):
  asym log -> linear SURVIVES (the spec's only explicit "log-uniform" asym law; the design break-check claims "log
  replaced by linear fails", which is true only for the 11 factors in the stratification list, not asym); GNSS
  latency uniform -> log SURVIVES; mismatch range (-100,0) instead of (-100,100) SURVIVES (range test only checks the bound);
  sag and weak scale uniform -> log SURVIVE; weak/loss motor index fixed at 0 SURVIVES; loss duration 2 -> 3 s and frozen
  1 -> 2 s: loss SURVIVES (the frozen duration mutation also survives, in the clean run); sag ramp 10 -> 5 s SURVIVES. These
  caught correctly: vib/tau linear, sag/weak/inverted/loss/match fractions, delay split, C1/C3/C4/C5/C6 pins, LHS-iid, sat leak into
  LHS, vib x1 constant, mode mix, gz seed duplicates, drop range, fault start range, EKF delay clamp.
  Note: a first batch of mutations was invalid (stale .pyc; `python -I` ignores PYTHONPYCACHEPREFIX); the
  list above is from the clean re-run.
- M4 G1 error is a multiplier on the nominal controller G1, not controller/true-plant (design choice 14). The plant G1 moves
  with the drawn inertia (about 1/I), so the realised controller/plant ratio is e x I_scale: up to 2 x 1.3 = 2.6 (C1 has
  inertia freely drawn) and as low as 0.5 x 0.7 = 0.35, outside the owner x[0.5, 2]. In C2 the pinned inertia +30 %
  lifts the realised ratio to 0.65, so "gain worst" is milder than named. Spec text (S64: "controller G1 / plant G1") is
  the plant-relative reading. Needs an owner or orchestrator choice, then the sampler should record the realised ratio.

### MINOR
- m1 Weak motor can coexist with saturation in C3 (3 of 10 runs): one motor at 0.7 x 0.351 gives about 1.85 x hover total,
  below the 2.0 x of the spec.
- m2 Loop-delay split: code puts half the delay on each path (each 0-5 ms, never above 5 ms on a path). The spec "split 50 %
  actuator path, 50 % IMU path" can also mean half the runs per path. The hook takes integer ms and act/imu emitted 0.625-step floats (design admits).
- m3 Tau asymmetry is applied on top of tau_scale (tau_down up to 9 x nominal, tau_up = tau_scale). The spec table
  does not say whether the owner x3 applies to tau_down; choice 5 states it.
- m4 Telemetry loss / frozen start in [1, 5] s of the final hold only. Spec: "start drawn inside the hold segments" (plural,
  hover hold too) and the flight text says "injected at the start of the hold".
- m5 Corner runs draw the other factors iid, so campaign-level shares drift from the table: matched 0.467, weak 0.323,
  frozen 0.233 (corners C5/C6 pin frozen/weak on 10 runs each). LHS exact. Spec says "every other factor drawn", so only a reporting point.
- m6 LHS stratifies the conditional gate dimension but not the value inside the on-subset (sag values in 5 bins: 14, 22, 21, 23,
  16 of 96); the self-test checks strata only for unconditional factors.
- m7 test_ranges line 99 mixes `and`/`or` without brackets: the `or steady > peak - EPS` clause turns off the peak range
  and amplitude identity for those runs. gz_seed (30 bit) uniqueness is checked for master 11 only, and not enforced in
  the code (collision chance about 4e-5 per campaign).
- m8 Pretest: 15 extremes, one end only (G1 x2 but not x0.5, asym 3 but not inverted 1/3, mass +30 only); latency+dropout and
  GNSS latency+EKF mismatch are in one run each, which confounds attribution. Fits 15 + 5 = 20.

## 2. Self-test: does it assert what it claims
Passes at 9/9. Its guarantees are real for: counts, seed distinctness, determinism, all pins C1-C6, conditional fractions to
+-0.02 (a 0.31 weak fraction mutation fails only above 0.32; it caught 0.35), LHS strata on 11 continuous factors, matched
GNSS rule. See M3 for what it does not catch.

## 3. Design note vs spec (read after section 1)
- Saturation only in C3 (choice 4): a reading, not stated by the spec; spec says "10 % of runs". A deviation from
  the plain number, flagged in the note for the orchestrator. See M1.
- Wind in every run (choice 8): consistent with the spec (no conditional share for wind). Side effect is correctly
  noted: "calm" limits of item 3 never apply to the LHS set. The note does not mention the no-gust runs (M2).
- Pretest grouping (choice 12): the note says the table has 17 rows; I count 15 rows in GATES.md 258-274 (the telemetry fault row is one row with three
  injectors). Grouping to 15 extremes + 5 sampled = 20 agrees with the spec totals, so it is consistent; the merged pairs
  and single end are my m8.
- Note section 3 break-check claim is true for the cases it names, but over-generalised (M3).
