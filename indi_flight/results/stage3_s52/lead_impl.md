# S52 D-RATE-LEAD implementation

Status: implemented in the working tree, NOT committed. Tests: `make tests TESTFILTER=indi_rate_control` passes (all tests); `make px4_sitl_default` builds.

## Files changed
- `src/lib/indi_rate_control/indi_rate_control.cpp`: step 8, `c = landed ? 0 : min(lead_scale K_i tau_c, kMaxLeadGain=2)` as Vector3f before the loop; `num_i = nu_i - (1+c_i) a_f_i + g2/dt (t_f - t_f_prev)`; `_lead_gain` stored for logging. getNu() unchanged.
- `src/lib/indi_rate_control/indi_rate_control.hpp`: `_lead_scale{1}`, `setLeadScale()` (non finite or <0 -> 0, >1 -> 1), `getLeadGain()`, `kMaxLeadGain`, header law comment updated.
- `src/modules/mc_indi_rate_control/`: `MC_INDI_LEAD` (yaml, DEFINE_PARAMETERS, parameters_updated), `lead_gain` filled in indi_rate_status.
- `msg/IndiRateStatus.msg`: `float32[3] lead_gain`.
- `src/lib/indi_rate_control/indi_rate_control_test.cpp`: makeController() sets lead 0; 13 new tests (suite IndiRateControlLeadTest).
- `indi_flight/design/rate_lead_note.md`: Status "implemented S52", sentence on the setpoint path fixed.
- (`indi_flight/STATE.md` shows modified in the tree: not by this task.)

## Tests and what each breaks on
| test | breaks on |
|---|---|
| LeadZeroIsBitIdentical | lead not gated by scale (0, NaN, negative all equal the old law, checked against (K e - a)/G1 exactly). Deviation from the note: the default scale is 1, so "never called setter" cannot equal scale 0; the check is against the written-out old law |
| DefaultScaleIsOne | default not 1 |
| LeadAddsKTauAccel | sign flip, tau ignored, nu changed |
| LeadUsesActuatorTc | hard-coded or separate tau_c |
| LeadPerAxisGain | wrong axis index or one K for all; a_f on pitch only leaks into roll/yaw |
| LeadRateErrorUnchanged | lead touching K e or getNu |
| LeadOffWhenLanded | lead active on ground (bit-identical to scale 0, lead_gain 0) |
| LeadYawWithSpinUp | lead outside the (G1+G2/dt) denominator, wrong K_Y |
| LeadScaleInvalidAndClamped | NaN/inf/negative not -> 0, >1 not -> 1, fault set |
| LeadGainIsClampedToTwo | K 100, tau 0.05: c = 2 not 5 |
| LeadKeepsFaultHold | NaN a_f not holding last output with lead on |
| MeasuredPathStaysBumplessWithLead | step at measured-path switch with lead 1 |
| LeadImprovesPhaseMargin | closed loop PM/GM thresholds (below) |

## Closed loop (RollPlantLag, tau 0.033, 1 sample delay, kDt 0.00125, P_att 8, K 20, loop closed through u = c + d, L = -c/u)
12 log points 0.5-30 Hz plus 40-170 Hz for the GM; amp 0.01, 10 integer periods, transient >= 4 s. Crossover/PM/GM by interpolation on log f. Sign check: L at 0.5 Hz has |L| 24.8 dB, arg -165 deg (integrator-like, attitude P loop on top), falling through 0 dB near 3 Hz.

| case | PM deg | GM dB | crossover Hz |
|---|---|---|---|
| lead 0 (ACT_TC 0.033) | 33.7 | 18.1 | 3.00 |
| lead 1 matched | 65.5 | 15.7 | 3.28 |
| lead 1, ACT_TC x0.6 (0.0198) | 44.9 | 9.5 | 3.58 |
| lead 1, ACT_TC x1.4 (0.0462) | 83.3 | 13.1 | 4.11 |

Asserted (as specified, all met): PM(lead1) >= 50 (65.5), PM gain >= 20 (31.8), GM(lead1) >= 10 dB (15.7); other rows only finite and PM > 0. GM < 6 dB at x1.4: NO (13.1 dB). Lowest margin is the under-estimated tau (x0.6): GM 9.5 dB, PM 44.9. The default ACT_TC 0.02 is about x0.6 of the 0.033 plant, so with the default the margins are those of the x0.6 row. The model has only the one-sample delay (no 3-5 ms loop delay), S48 found GM optimistic by 2-3.5 dB, so x0.6 GM could be ~6-7 dB in flight (UNVERIFIED).
The crossover assertion of the note (within 30 percent of K/2pi = 3.18 Hz): 3.28 Hz, not asserted.

## Break-check
Flipped the term to (1 - c): 7 tests failed: LeadAddsKTauAccel, LeadUsesActuatorTc, LeadPerAxisGain, LeadYawWithSpinUp, LeadScaleInvalidAndClamped, LeadGainIsClampedToTwo, LeadImprovesPhaseMargin (PM 1.1 deg, GM 0.3 dB). Restored: all pass. (LeadZeroIsBitIdentical, landed, rate-error tests do not detect a sign flip by design.)

## Unverified
- Formatting: clang-format absent in the container; `make format` and the astyle script ran silently, diff not checked against CI `make check_format`.
- Not flown; yaw lead, measured path in flight, noise (G4) as in the note.
- Param description wording against the parameters guideline (kept short; note text condensed). `make px4_sitl_default` compiled the module and msg but SITL was not run.
- Step overshoot test of the note was not added.
