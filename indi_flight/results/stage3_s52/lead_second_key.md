# Second key: rate-prediction lead (working tree, uncommitted)

Scope: spec `indi_flight/design/rate_lead_note.md` sections 1.1, 1.3, 1.4, 3 plus the S52 amendments. Code read:
`src/lib/indi_rate_control/indi_rate_control.{cpp,hpp}`, `src/modules/mc_indi_rate_control/McIndiRateControl.{cpp,hpp}`,
`mc_indi_rate_control_params.yaml`, `msg/IndiRateStatus.msg`. `results/stage3_s52/` not read.

## Per item

1. Numerator. AGREE. `indi_rate_control.cpp:388`:
   `numerator = nu(i) - (1.f + lead_gain(i)) * a_f(i) + g2_over_dt * (t_f(i) - _t_f_prev(i))`.
   `a_f` is the local that the optional yaw LPF2p overwrites at `cpp:362` (`a_f(2) = _yaw_lpf_accel.apply(a_f(2))`),
   so the lead uses the post-filter value, as specified. `nu` is K e (`cpp:368`).

2. Lead outside denominator, getNu, blend, t_f, measured path. AGREE.
   - Denominator is `_g1(i) + g2_over_dt` (`cpp:389`), no lead.
   - `nu = _gain_k.emult(rate_error)` (`cpp:368`), no lead; `_nu = nu` (`cpp:412`), so `getNu()` is unchanged.
   - Blend (`cpp:320-340`), `t_f` (`cpp:315`, `cpp:339`, `cpp:363`) and measured-path filters (`cpp:284-309`) do not reference `lead_gain`/`_lead_scale`.
   - Only other lead reference is `_lead_gain = lead_gain` at `cpp:414` (logging).

3. Landed gating. AGREE. `lead_gain(i) = landed ? 0.f : ...` (`cpp:383`) uses the `landed` parameter of `update()`
   (`cpp:210`), the same flag that gates `t_fb` (`cpp:373`), the blend (`cpp:322`) and yaw reset (`cpp:342`).
   The module passes `_maybe_landed || _landed` (`McIndiRateControl.cpp:336`), same as the rest of the law.

4. `_actuator_tc`. AGREE. Single variable: setter `cpp:46-50` (constrain 0.001..0.2 s, non-finite -> 0.02), used for the
   actuator model `cpp:257` (`exp(-dt / _actuator_tc)`, dt in s) and for the lead `cpp:383`. Param unit `s`
   (`mc_indi_rate_control_params.yaml:102-110`, MC_INDI_ACT_TC). No second time constant.

5. Parameter wiring and status fill. AGREE on the normal path, DISAGREE on the fault/hold path.
   - Wired: param registered `McIndiRateControl.hpp:195`; `_indi.setLeadScale(_param_mc_indi_lead.get())` at
     `McIndiRateControl.cpp:90`; yaml entry `mc_indi_rate_control_params.yaml:113-124` (default 1, min 0, max 1,
     increment 0.05, decimal 2, matching spec section 3).
   - Setter `indi_rate_control.hpp:126`: `isFinite ? constrain(scale, 0, 1) : 0` (NaN and negative -> 0, >1 -> 1). Matches spec.
   - Status: `_indi.getLeadGain().copyTo(indi_rate_status.lead_gain)` at `McIndiRateControl.cpp:222`, published at `:229`,
     every cycle. Msg field `msg/IndiRateStatus.msg:9`.
   - Fault/hold path: `_lead_gain` is written only at `cpp:414`, which is after every early return. Invalid inputs or
     params return `faultOutput(false)` (`cpp:225`), and a non-finite `dt_cmd` returns `faultOutput(true)` (`cpp:396`),
     both before `cpp:414`. `faultOutput()` (`cpp:191-207`) does not touch `_lead_gain`. So on those cycles the published
     `lead_gain` is the value from the last successful cycle, while `fault` is true and the output is held (or zero).
     Spec says `lead_gain` is "c_i applied this cycle"; on a fault cycle nothing is applied, so the stale value is wrong.
     Worse, `reset()` (`cpp:179-189`) zeroes `_nu`, `_a_f`, `_dt_cmd`, `_t_cmd_last` but not `_lead_gain`. When the
     hold expires (`cpp:205`, `reset()`), nu, a_f and dt_cmd are zero while `lead_gain` keeps its old value. Inconsistent.
     Fix: zero `_lead_gain` in `reset()` and at the top of the fault path (or at `faultOutput`), or write it before the
     returns. Pre-existing fields `_nu`/`_a_f` have the same stale-on-invalid-input behaviour, so this is a consistency
     gap rather than a safety issue; the lead itself is not applied on those cycles since the output is held.

6. Other contradictions with spec.
   - Cap: `math::min(_lead_scale * _gain_k(i) * _actuator_tc, kMaxLeadGain)` with `kMaxLeadGain = 2.f`
     (`cpp:383`, `hpp:262`). Matches amendment. Note that `min` has no lower bound: a negative K (param min not checked here)
     would give negative c. UNVERIFIED whether MC_INDI_K_* min is > 0 (yaml not read for K).
   - Getter returns c, not K tau_c a_f as spec 1.3 said (`hpp:129`). This is the S52 amendment (IndiRateStatus lead_gain = c_i), so AGREE.
   - Header comment shows the new nu line (`hpp:52-55`, `hpp:63-64`). Matches 1.3.
   - Yaml long text says "(at most 2)" and matches the cap. Fine.
   - Yaw uses `_gain_k(2)` = K_Y via the same loop (`cpp:382-384`). Matches 1.2.
   - Lead computed after `t_fb` and before the loop (`cpp:380-384`), as specified 1.3.
   - No new state, no new reset line beyond the `_lead_gain` gap in item 5.

## Verdict summary
| # | Item | Verdict |
|---|------|---------|
| 1 | numerator = nu - (1+c) a_f(post-yaw-LPF) + g2/dt dt-term | AGREE |
| 2 | lead not in denominator, getNu, blend, t_f, measured path | AGREE |
| 3 | landed gating uses update()'s `landed` | AGREE |
| 4 | `_actuator_tc` shared with actuator model, seconds | AGREE |
| 5 | param wiring and per-cycle status | AGREE on normal path; DISAGREE on fault/hold (stale `lead_gain`, not zeroed in `reset()`) |
| 6 | other spec items | AGREE (getter is c per amendment); minor: no lower bound on c (UNVERIFIED K min) |

## Disposition (orchestrator, S52)
- Item 5: `reset()` now zeroes `_lead_gain` (as `_nu`, `_a_f`). On the fault/hold return the logged lead_gain keeps the
  last value, as nu and angular_accel_filtered already do; the `fault` flag of the same message marks those cycles. No change.
- Item 6: K < 0 is rejected by paramsValid (K >= 0 and finite), so c >= 0. No change.
