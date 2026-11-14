# v3 regression smoke: MC_INDI_ACT_BLD 0 reproduces v2 (session 46)

Script `bench/v3_smoke.sh`, 2026-11-15 00:31-00:35, v3 binary (px4_sitl_default incl. 3a47bf746e), frozen indi_v2
params + `MC_INDI_ACT_BLD 0` (`bench/params/indi_v3_bld0.params`), v2 sim config, seed 1. Reference: seen-set
indi_v2 seed 1 (`results/s2_seen_v2/runs/`, v2 binary).

| entry | metric | indi_v2 (seen) | v3, ACT_BLD 0 |
|---|---|---|---|
| step_roll (x4) | roll attitude RMS (deg) | 3.622 | 3.630 |
| step_roll (x4) | roll rate RMS (rad/s) | 0.0600 | 0.0621 |
| step_roll (x4) | motor-rate effort | 0.552 | 0.519 |
| hover (x1) | position RMS 3D (m) | 0.069 | 0.023 |
| hover (x1) | motor-rate effort | 0.044 | 0.056 |

Both runs exit ok, no saturation. step_roll agrees within 0.3 % on the primary metric. The hover differences are of
the size of the documented hover run-to-run noise (D-hovernoise: 2-3x on position RMS for the same params and seed);
the step entry is the discriminating check. Verdict: with the blend disabled the v3 binary flies as v2, as the unit
tests (40/40, bit-identical outputs at Tb = 0) predict.
