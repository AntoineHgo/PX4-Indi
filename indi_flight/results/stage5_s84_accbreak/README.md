# S84 T174: INDI acceleration-loop break at the stage output (MC_INDI_PINJ_PT 1), z pre-test

Brief: `design/brief_accbreak_s84.md`. Agent notes: `NOTES.md`. One flight, pre-test only (not a G2 cell result).

## Configuration
quad5in, INDI stack, 400 Hz, z axis, MC_INDI_PINJ_PT 1, TB (MC_INDI_ACT_BLD) 1.0 s, AMP 0.04, DLY 20 s, NP 5,
seed 1, speed 4, same band as S83 (`results/stage5_s83_velbreak/README.md`). Params: `pt1.params`.
Analysis: `bench/pinj_csv.py --point output` -> `pt1_pinj_z.csv`, `pt1_margins.json`.

## Result
| quantity | value |
|---|---|
| crossover | 0.62 Hz |
| PM | 58.7 deg |
| delay margin | 0.26 s |
| GM | no -180 deg crossing in band; abs(L) at 8 Hz = -11.3 dB |
| abs(L) | 4.67 (0.2 Hz), 1.03 (0.6), 0.49 (1), 0.27 (2), 0.06-0.30 (3.2-8) |
| peak abs(u) | 10.2 m/s^2 (no saturation seen) |

## Interpretation (orchestrator, S84)
- A break at the stage output is the loop at the plant input of the whole cascade: L contains the INDI incremental
  path AND the velocity/position loops (through a_ref). With a matched actuator model the INDI part cancels
  (t_c = t_f + a_ref - a_f, where t_f and a_f both carry u: c depends on u only through the mismatch, the blend and
  the outer loops), so the low-frequency L is the outer loop. The result agreeing with the S83 input break (PM 57.3,
  0.67 Hz) is what this predicts, not a defect. It is still the G2 cell "INDI acceleration loop, break at plant
  input" by the GATES.md definition (every feedback path through the break closed).
- The INDI-specific part (mismatch, D-GAP blend HF mode) shows above about 3 Hz, where coherence on the output channel
  is 0.12-0.67: those bins are not usable. The D-GAP HF-mode check needs a band-limited, higher-amplitude excitation
  over 2-20 Hz (or more periods) before it is read.

## Open (before this counts in G2)
AX = 0 / PT = 0 behaviour-identical flight (code inspection only so far); second key of the code against the brief;
x and y axes; 800 Hz; two seeds; hole report (evidence limit 1); linear-model cross-check of the output-break L.

## Second key (T175, S84): AGREE WITH MINOR (`second_key.md`)
Fixed: param long texts no longer re-list enum options (PINJ_PT, PINJ_AX). Accepted as bench limits (PT 1 only):
`_coll_clamped`, `omega_ff` and the logged `q_d` come from t_c, not u_o; u_o bypasses the library tilt/collective
clamps (keep AMP below the hover vertical thrust margin; a z AMP above ~g could invert the vector). The unit test
does not exercise the clamp; the pinj_csv self-test checks the column mapping only (pyulog mocked).

## HF re-fly (S84, orchestrator, UNKEYED)
`hf.params`: PT 1, z, band 1.5-10 Hz, AMP 0.12, TP 5, NP 8 (stage runs at ~89 Hz, so 10 Hz < 0.4x rate). The
`pinj_csv.py --margins` step crashed (no crossover in band, empty interpolation: `hf_margins.err`; a pinj_csv defect
to fix: report "no crossover" instead of raising). FRF by an inline per-bin least-squares fit, first period dropped:
`hf_frf.txt`. abs(L) -10.1 dB at 1.6 Hz falling to -22.9 dB at 3.8 Hz, then -17 to -18 dB over 7.6-9.4 Hz; arg L
-62 to -131 deg; no -180 deg crossing in 1.6-9.4 Hz, so the INDI/D-GAP high-frequency part has GM > 17 dB in this
band. No coherence computed (single run, single script): second key and margins_est coherence before use.

## HF second key (S85, T176 + orchestrator): AGREE (`hf_second_key.md`, `hf_margins_s85.json`)
Independent per-period LS phasor + H1 re-computation matches `hf_frf.txt` within 0.05 dB / 0.2 deg at all 9 bins,
coherence >= 0.985. The S84 `--margins` crash was a `margins_est._ls_phasors` defect (no constant column: the z
signals have a mean near -g, which biased every phasor on the non-uniform time base and rejected all bins), not only
the missing crossover. Fixed S85 (constant column added; `bench/tests/test_margins_selftest.py` ALL PASS); pinj_csv
now reports "no crossover in band" explicitly (two tests, failed before the fix). Re-run: all 9 bins accepted,
coh_y >= 0.987, max |L| -10.1 dB at 1.6 Hz, lowest arg L -131.0 deg at 9.4 Hz, Ms 1.26 dB. Reading: no gain or phase
crossover in 1.6-9.4 Hz; GM > 17 dB is a bound for this band only (phase still falling at 9.4 Hz, stage at 89 Hz).
Earlier margins_est results used zero-mean rate/attitude signals or the uniform-grid FFT path; whether any earlier
non-uniform LS result had a signal mean is NOT yet checked (open: re-run the S82-S84 velbreak/pt1 margins).
Re-run of earlier LS-path margins with the fixed estimator (S85): S83 velbreak tb10 PM 57.28 / tb033 59.10 deg,
unchanged (< 0.001 deg; input-break signals have no mean). S84 pt1 (output break, z accel mean near -g) CHANGED:
old 7/16 bins accepted, PM 58.7 deg at 0.62 Hz; new 13/16 bins, PM 61.3 deg at 0.64 Hz (`pt1_margins_s85.json`).
The S84 pt1 number above is superseded by this one (errata: defect in margins_est, not in the flight).
