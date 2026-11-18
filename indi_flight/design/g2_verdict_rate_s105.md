# G2 verdict note: INDI v2 rate loop (S105)

Scope: the 24 INDI v2 rate cells of `results/g2_rate_table_s99.md` ("S101 update", keyed K100 + K101) against the
G2 linear-model cross-check (GATES.md G2: |dPM| <= 10 deg, |dGM| <= 3 dB). Evidence: `design/g2_crosscheck_s105.md`
(X105, sonnet, offline). Not a freeze: the stage-6 frozen pair re-flies all G2 cells.

## Verdict per cell group

| Group | Cells | Measured (GM / PM / DM) | Model cross-check | Status |
|---|---|---|---|---|
| Roll, pitch; 800, 400 Hz; measured and model-only torque | 16 | all PASS | all within tolerance; worst dPM 4.7 deg, dGM 1.86 dB | PASS (preliminary, pre-freeze) |
| Yaw; 800, 400 Hz; both paths | 8 | all PASS | none: yaw not modelled (`bench/margins_models.py:162`) | OPEN: cross-check missing |
| 267 Hz (250 Hz report row) | - | not measured | analytic only | OPEN (report-only row) |
| Attitude, velocity, position, accel-INDI breaks | - | see GATES.md cell table | - | OPEN |

## Findings
1. Filter models verified against source: AlphaFilter (`AlphaFilter.hpp:69-79,169`) and LowPassFilter2p
   (`LowPassFilter2p.hpp:77-86`) match `margins_models.py`; removes two items of the T78 UNVERIFIED list.
2. A-21 (18 deg PM gap) concerned the v1 sim, model-only path at S41 without the attitude loop in the model; closed
   S48 (`ANOMALIES_CLOSED.md:12`). It does not apply to the v2 cells: the model config `HEAD_FLIGHT` includes it.
3. Residual pattern: at 400 Hz the model GM is 1.7-1.9 dB optimistic and PM 4.2-4.7 deg pessimistic; model-only GM
   1.3-2.4 dB optimistic. Likely cause (UNVERIFIED, not fitted): measured-torque latency modelled as one sample,
   not as a fixed time. Within tolerance, so not an anomaly; recorded as a model limit.
4. The second keys re-score the same ulogs with independent code (lesson 1 satisfied); plant variation is G3's job.

## Remaining for the rate-loop G2 row
- Yaw linear model (drag-torque path plus spin-up term of decision 5) in `margins_models.py`, then the 8 yaw cells.
- Pitch model uses roll defaults (UNVERIFIED that the S99/S100 parameter files match beyond G1, ACT_TC, LEAD).
