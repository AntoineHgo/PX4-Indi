# T126 second key: rate-setpoint lead on the setpoint path (S62)

Reviewed: commit da64bc26b3 ("feat(indi_rate_control): rate-setpoint lead on the setpoint path")
Against: `indi_flight/DECISIONS.md` L395-412, D-S3-ATT-STEP.
Method: read of the commit diff and the surrounding code. No builds, no tests run.

Line references are to the working tree at HEAD (b225d264b1).

## 1. The law: OK

- `src/lib/indi_rate_control/indi_rate_control.cpp:455`:
  `numerator = nu - (1 + c) a_f + c * r_dot_f + g2_over_dt * prev_inc`.
  This matches the spec numerator `nu - (1 + c) a_f + c r_dot_f`.
- `c` is `lead_gain(i)` (L449): `landed ? 0 : min(lead_scale * K_i * tau_c, kMaxLeadGain)`. The same `c` multiplies the feedback and the setpoint derivative, as specified.
- Units: `rate_sp_dot` is `(sp - sp_prev)/dt` in rad/s^2, the same unit as `a_f`. Sign: positive `r_dot` for a rising setpoint adds to the increment, as the spec's `c r_dot` term requires.
- Note (minor, not a law error): the spec text (DECISIONS.md L400) puts `c r_dot` inside `nu`. The code puts it in the numerator and keeps `nu = K (rate_sp - rate)` (L~412). The numerator is identical. The logged `nu` (`getNu`, `indi_rate_status.nu`) therefore excludes the lead term. Either move the term into `nu` for logging or reword the spec.

## 2. r_dot_f: OK

- Filter: `sp_alpha = dt / (kSetpointLeadTc + dt)` (L396), `y += alpha (raw - y)`. This is the standard discretisation of a first-order low pass with the actual `dt`. `kSetpointLeadTc = 0.01 s` (header).
- Clamp: `constrain(filtered, -kMaxRateSpDot, kMaxRateSpDot)`, `kMaxRateSpDot = 1000 rad/s^2` (L401).
- Yaw: when `_yaw_filter_active`, `rate_sp_eff(2) = _yaw_sp_lpf.apply(rate_sp(2))` (L387-389). The derivative therefore uses the same filtered setpoint that enters the filtered yaw error (`rate_error(2) = lpf(rate_sp - rate)`, L110). Consistent.
- Design note only: the yaw setpoint is a 2nd-order filter (`_yaw_sp_lpf`) before a further 10 ms low pass. The yaw lead therefore has extra group delay. This is a tuning consideration, not a defect.

## 3. No impulse: ISSUE (one path, minor)

Paths checked:
- First cycle: `_sp_lead_reset{true}` in the header (`.hpp`, `_sp_lead_reset`). OK.
- After `reset()`: zeroes `_rate_sp_prev` and sets the flag (L195-196). OK.
- After `resetSetpointLead()`: flag set; the next update zeroes `r_dot` and re-seeds `_rate_sp_prev` at L405. OK.
- Landed: L391 zeroes `r_dot` and consumes the flag. L405 runs on landed cycles too, so `_rate_sp_prev` tracks the setpoint on the ground. The landed->flight edge therefore starts from a current previous value, not a stale one. OK.
- Fault before 6c (invalid dt at L228-236, input rejection): `faultOutput()` sets the flag and zeroes `r_dot` (L203-204). `_rate_sp_prev` is not updated on the rejected cycle, which is harmless because the flag forces zero and re-seeds on the next valid cycle. OK.
- Fault after 6c (`!dt_cmd.isAllFinite()`, L461): `_rate_sp_prev` was updated this cycle and the flag is set for the next. OK.
- Invalid dt: same as the fault path above. OK.
- ISSUE (minor), yaw filter disable toggle: `designYawFilters()` (L121-131) sets `_yaw_filter_active` and `_yaw_filter_reset_pending`. When the filter goes from active to inactive, L387 stops applying the filter, so `rate_sp_eff(2)` becomes the raw setpoint at L385-389. `_rate_sp_prev(2)` still holds the previous cycle's *filtered* value, and no flag is set. The first cycle after the toggle therefore differentiates raw minus filtered, which for a moving setpoint is about rate * filter lag / dt. This is a one-cycle transient, bounded by the 10 ms low pass and the clamp, not unbounded, but it is an impulse the reset does not catch, and it is outside the spec's stated reset set. Fix: set `_sp_lead_reset = true` in `designYawFilters()` when `_yaw_filter_active` changes, or re-seed `_rate_sp_prev(2)` at that point. No test covers it.

## 4. Module (McIndiRateControl.cpp): OK

- The reset is at L370-379, inside `Run()`, computed from the control-mode flags (attitude, rates, manual, offboard) and the watchdog `wd.stale` (bit 4). The acro branch is derived from manual and attitude, both included. The flags and the watchdog stale state cover the stated sources.
- Order: the `resetSetpointLead()` call (L376) comes before `_rates_setpoint.zero()` (zero_rates), before `runIndiRateControl()` (L406) and therefore before `_indi.update()` (L231). The reset applies to the same cycle's setpoint. OK.
- `_sp_source_prev{0xff}` makes the first cycle reset too. OK.
- `_indi.reset()` on disarm (L393) also resets the flag. OK.

## 5. Tests (indi_rate_control_test.cpp, L1882-end): mostly OK, gaps listed

- `AttitudeStepOvershootBounded`: asserts overshoot <= 5 %. The commit states the pre-change overshoot is 12.6-14.2 %, so the test would fail if the setpoint term were removed. OK. The helper takes `lead_scale` but the test only uses 1.0, so there is no baseline assertion in the test.
- `NoImpulseFromSetpointStepOrReset`: asserts zero on the first cycle, on `resetSetpointLead()`, on `reset()` and on the cycle after a NaN rejection. Each assertion would fail if its reset path were broken: the NaN case shows stale-prev would produce a non-zero derivative (`-25 -> -5`). The clamp is checked exactly (`-500 -> -1000`). OK.
- `LandedHoldsZeroAndTakeoffStartsAtZero`: the first in-flight cycle with an unchanged setpoint must be zero. This fails if `_rate_sp_prev` were not tracked while landed. OK.
- `LeadZeroIsPreviousLawOnRandomInput`: the name says "previous law", but it compares two lead-0 controllers, one of which is reset every cycle. At lead 0 the derivative term is multiplied by zero, so the test only catches a missing `lead_gain` multiplier on `r_dot`. It does not compare against the previous commit's law. Misleading name, weak check.
- Gaps (untested paths):
  - a direct assertion that `dt_cmd` contains `+c r_dot` with the correct sign and magnitude (only indirect, via the overshoot test);
  - the yaw `r_dot` path (filtered yaw setpoint);
  - the yaw filter enable/disable toggle (item 3 issue);
  - the invalid-dt fault path (L228-236);
  - the `states_corrupted` fault path;
  - the module's `sp_source` reset (no module-level test).

## 6. Logging field rate_sp_dot: OK

- `msg/IndiRateStatus.msg`: `float32[3] rate_sp_dot` added after `lead_gain`, with the zero-on-landed comment.
- `McIndiRateControl.cpp:252`: `_indi.getRateSpDot().copyTo(indi_rate_status.rate_sp_dot);` in `runIndiRateControl()`, next to `lead_gain`. This is filled every cycle the rate loop runs, the same as the other status fields. When `flag_control_rates_enabled` is false, `runIndiRateControl()` is not called and the message is not updated, which matches the existing fields.

## Overall verdict: AGREE-WITH-ISSUES

Issues to address before freeze:
1. Yaw filter disable toggle leaves `_rate_sp_prev(2)` stale (item 3); add a reset on the toggle and a test.
2. Logged `nu` excludes `c r_dot` while the spec places it in `nu` (item 1); align the logging or the spec wording.
3. Rename or strengthen `LeadZeroIsPreviousLawOnRandomInput`; add a direct sign/magnitude test of `+c r_dot` in `dt_cmd`, and tests for the yaw derivative and the invalid-dt fault path (item 5).
