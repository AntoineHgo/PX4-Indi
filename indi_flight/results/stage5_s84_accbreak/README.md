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
