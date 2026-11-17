# Errata to archived and earlier results

Corrections to numbers of the archive (`indi_project/`, F-4) and of earlier sessions of this project. One entry per
defect: what was wrong, which results it touches, the corrected value or the re-run that replaces it.

## E-1 Disturbance wrench applied twice (A-31, found S66, fixed S67)

- Defect: `src/modules/simulation/gz_bridge/server.config` loads the ApplyLinkWrench system for worlds without
  `<plugin>` (default.sdf). The disturbance injector (`indi_project/bench/disturbance.py` and its copy in
  `indi_flight/bench/`) added a second instance at runtime, so every one-step wrench was applied twice.
- Touches: every disturbance result before fc8905cf90: archive T6 gust_x, T7 payload_add, H2 gust_diag, H3 com_shift
  on the x500 (same default world and runtime add; UNVERIFIED per archived run log) (applied wrench was 2x the logged/stated value), and `results/g15_dist_s66/`.
- Evidence of the fix: `results/a31_fix_s67/README.md` (rpm^2 ratio 1.497 -> 1.249 for 25 % W payload) and the
  independent check `results/a31_fix_s67/second_key.md` (1.2490 vs expected 1.2497).
- Correction: archived disturbance verdicts stand as history; the disturbance magnitudes they state are half of what
  was flown. New disturbance evidence comes only from runs after fc8905cf90.
