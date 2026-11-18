# Rate-loop actuator blend (MC_INDI_ACT_BLD) survey, S74

Read-only survey. No code edited. Line numbers as of HEAD (branch feat/indi-flight).

## 1. Parameter

- Definition: `src/modules/mc_indi_rate_control/mc_indi_rate_control_params.yaml:153-164`
  - `MC_INDI_ACT_BLD`, type float, default **0.0** (off), min 0.0, max 10.0, unit s, decimal 2, increment 0.05.
  - Long text: "Only used when MC_INDI_W_MAX is set. Set to 0 to disable (measured torque only)."
- Read: `src/modules/mc_indi_rate_control/McIndiRateControl.hpp:207` (ParamFloat binding), and
  `src/modules/mc_indi_rate_control/McIndiRateControl.cpp:101` (`_indi.setActuatorBlendTimeConstant(_param_mc_indi_act_bld.get());`).
- Setter: `src/lib/indi_rate_control/indi_rate_control.cpp:52-56`. Non-finite or <= 0 stored as 0; clamped to `kMaxBlendTimeConstant = 10 s` (`indi_rate_control.hpp:302`).
- Gating: the param text says "only used when MC_INDI_W_MAX is set". I found no explicit W_MAX check in the blend code. The gate is indirect: the measured torque (`t_f_meas`) only exists when W_MAX is set (`McIndiRateControl.cpp:129`, `McIndiRateControl.cpp:507`). Without W_MAX, `_meas_in_use` should stay false and the blend just tracks the gap. Not verified at runtime.

## 2. Blend update (quoted)

`src/lib/indi_rate_control/indi_rate_control.cpp:331-356`:

```
// 5d. complementary blend: ...
const Vector3f t_gap = t_f_model - t_f_meas;

if (_meas_in_use && (_blend_tc > 0.f) && !landed) {
    // maybe_landed freezes the slow integrator only (D-S3-LANDED), ...
    if (!maybe_landed) {
        const float blend_alpha = dt / (_blend_tc + dt);
        _blend += blend_alpha * (t_gap - _blend);
    }
} else {
    _blend = t_gap;
}
for (...) { non-finite -> t_gap or 0; _blend = constrain(_blend, -kMaxBlend, kMaxBlend); }
if (_meas_in_use) {
    t_f = (_blend_tc > 0.f) ? (t_f_meas + _blend) : t_f_meas;
}
```

`kMaxBlend = 2` (`indi_rate_control.hpp:303`). Header comment at `indi_rate_control.hpp:70-73`.

## 3. Edge behaviour (rate loop)

Key point: the rate blend has **no freeze on telemetry loss**. It snaps to tracking the instantaneous gap (`_blend = t_gap`) whenever it is not active.

| Edge | Behaviour | Code |
|---|---|---|
| Telemetry invalid (`meas_valid` false) | **Track gap (snap-to-instantaneous each cycle)**. `_meas_valid_cycles = 0`, `_meas_in_use = false`, so the else branch runs. | `indi_rate_control.cpp:328` (`_meas_in_use = (_meas_valid_cycles >= kMeasValidCycles)`), `:336`, `:343-344` |
| Telemetry frozen/lost but cycle still valid | Not detected separately. Only the `meas_valid` flag counts. A frozen-but-valid stream is not handled by the blend. | not in blend code |
| Invalid inputs / params / dt (fault path) | **Freeze**. Function returns early; `_blend` is not touched. | `indi_rate_control.cpp:236-240` (`_meas_in_use = false; return faultOutput(false);`) |
| Telemetry recovered | Blend resumes from its tracked value after `kMeasValidCycles` consecutive valid cycles. Bumpless because `_blend` tracked `t_gap` during the gap. | `indi_rate_control.cpp:328`; test `indi_rate_control_test.cpp:1206` |
| Landed (`landed`) | **Track gap** (snap-to-instantaneous). Not frozen. | `:336` (`!landed` fails -> else `_blend = t_gap`) |
| maybe_landed | **Freeze the integrator only**; `_blend` holds, the rest runs. | `:337-342` (`if (!maybe_landed)`) |
| Disarmed | No explicit blend handling in the lib. Module calls `reset()` in some paths; see below. | `McIndiRateControl.cpp:393` |
| `reset()` | **Snap to zero**: `_blend.zero()` inside `resetStates()`. Next update then re-tracks gap. Callers: `indi_rate_control.cpp:210` (`resetStates()`) and `:219` (`reset()`). | `indi_rate_control.cpp:181`, `:188` |
| Parameter change (`MC_INDI_ACT_BLD`) | Setter runs every cycle (`McIndiRateControl.cpp:101`) but only stores `_blend_tc`. Does not touch `_blend`, so no snap on change. Setting to 0 makes the else branch track gap and output `t_f_meas` (blend unused). Re-enabling starts from tracked gap (bumpless). | `indi_rate_control.cpp:52-56`, `:356` |

Note: the `_blend_tc == 0` case in the else branch means `_blend` still tracks gap while disabled, so re-enable is bumpless.

## 4. Outer-loop D-GAP collective blend (comparison)

Library: `src/lib/indi_accel_control/indi_accel_control.cpp`. Consumer: `src/modules/mc_indi_pos_control/McIndiPosControl.cpp`.

Update, `indi_accel_control.cpp:292-298`:
```
// D-GAP blend: b = LP_tb(u_model - u_meas), held (never reset) on the ground, at bypass edges (hold flag),
// while the telemetry is invalid and while the collective is clamped (anti-windup)
const bool blend_frozen = _blend_hold || !in.mean_u_valid || _coll_clamped;
if ((_tb > 0.f) && !blend_frozen) { _b += ...; _b = constrain(_b, -kMaxBlend, kMaxBlend); }
```

| Edge | Behaviour | Code |
|---|---|---|
| Telemetry invalid (`!mean_u_valid`) | **Freeze** | `indi_accel_control.cpp:294` |
| Landed / maybe_landed | **Freeze** via `setBlendHold(landed \|\| maybe_landed)` | `McIndiPosControl.cpp:193-194`, `indi_accel_control.cpp:294` |
| Bypass | **Freeze** via `setBlendHold(true)` | `McIndiPosControl.cpp:224`, `indi_accel_control.cpp:294` |
| Collective clamped (anti-windup) | **Freeze** | `indi_accel_control.cpp:294` |
| `reset()` | **Hold (never reset)**: keeps `_b`, restarts model path at `u + _b`, no innovation across the edge | `indi_accel_control.cpp:111-112`; `McIndiPosControl.cpp:224` comment |
| Disable (`tb <= eps`) | **Snap to zero**: `_tb = 0; _b = 0;` | `indi_accel_control.cpp:100-102` |
| Parameter change (`MPC/INDI tb`) | Setter at `McIndiPosControl.cpp:357` in the param-update block. Only sets `_tb`; `_b` not touched unless disabled. | `indi_accel_control.cpp:95-103` |

So the outer loop **freezes** on every edge (landed, bypass, telemetry loss, clamp) and only snaps on explicit disable. The rate blend **tracks the gap** on landed and telemetry loss and **freezes** only on the fault path and maybe_landed integrator.

## 5. Existing unit tests

Rate lib: `src/lib/indi_rate_control/indi_rate_control_test.cpp`
- `:1140` `IndiRateControlBlendTest.DisabledIsBitIdenticalToNoSetterCall`
- `:1164` `IndiRateControlBlendTest.SteadyGapConvergesToModel`
- `:1185` `IndiRateControlBlendTest.HighFrequencyFollowsMeasurement`
- `:1206` `IndiRateControlBlendTest.SwitchFromModelToMeasurementIsBumpless`
- `:1237` `IndiRateControlBlendTest.LandedBlendTracksWithoutAccumulating`
- `:1798` `IndiRateControlLandedTest.MaybeLandedPulseNoStep` (touches frozen integrator under maybe_landed)

Outer loop: `src/lib/indi_accel_control/IndiAccelControlTest.cpp`, fixture `IndiAccelBlendTest`
- `:721` `ConvergesToThrustGap`
- `:730` `NegativeControlDisabledKeepsGap`
- `:739` `FrozenOnLandedHold`
- `:751` `FrozenOnTelemetryLossAndRecovery`
- `:761` `ModuleResetDoesNotTouchBlend`
- `:770` `FrozenWhileCollectiveClamped`
- `:786` `FrozenAtBypassA3A8`
- `:803` `NoDriftAfterResetWithoutHold`
- `:821` `FrozenAtE7EdgeSingleCycle`

Gap for the brief: no rate-lib test covers `reset()` zeroing `_blend`, or the parameter-change edge (live setter call). The `FrozenOnTelemetryLossAndRecovery` pattern in the outer loop has no rate-loop counterpart, and the rate loop tracks rather than freezes on telemetry loss, so a freeze-vs-track decision is needed before porting.

## Open items for the implementation brief

- Decide whether the rate blend should freeze on telemetry loss (as D-GAP does) or track. Current code tracks; this is the main asymmetry with D-GAP.
- Confirm the W_MAX gating (no explicit check found in the blend path).
- Conditions for `resetStates()` at `indi_rate_control.cpp:210` and `McIndiRateControl.cpp:393` were not re-read.
