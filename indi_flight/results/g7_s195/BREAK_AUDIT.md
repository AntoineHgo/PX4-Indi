# G7(b) break-check audit (S195)

Scope: src/lib/indi_rate_control, src/lib/indi_accel_control, and the extracted helpers in mc_indi_rate_control / mc_indi_pos_control. Module glue out of scope (D-G7-HARNESS).
Method: one minimal semantic mutation at a time, `make tests TESTFILTER=<regex>` in Docker (image px4-indi-sim, same one that configured build/px4_sitl_test; the px4io/px4-dev image fails the protobuf cmake check on this build dir), `git checkout -- <file>` right after each run. build/px4_sitl_default untouched. "killed" = at least one gtest failed (names are failing tests, first 1-3 listed). Each run was an incremental rebuild (about 15 s).
Prior records: indi_flight/design/t206_lib_mutation_tests_log.md (accel, T206 items 1-5, 9 mutations); indi_project/review/external_review_s59_notes/test_review.md is a mutation-by-reading review (not executed runs), so it is NOT counted as a break-check.

## 1. Inventory (behaviour, tests, existing break-check)
| # | behaviour | asserting test(s) | existing break-check |
|---|---|---|---|
| 1 | rate INDI increment dt_cmd = (nu - (1+lead)*a_f + ...)/g1, t_cmd = t_fb + dt_cmd | RateStepResponse, ConstantDisturbanceRejected..., LeadAddsKTauAccel | none -> M1-M3 |
| 2 | rate P term nu = K*(rate_sp - rate) | RateStepResponse, ConstantDisturbance... | none -> M1 |
| 3 | actuator model first-order, delay buffer, 3-axis | PassThroughFiltersAndDelay, DelayChangeMidRun... | none -> M9, M15 |
| 4 | blend of measured/modelled torque (t_f_meas + blend) | IndiRateControlBlendTest.*, WeakMotorStandingError... | none -> M4, M7 |
| 5 | measurement validity counting / switch to measured | IndiRateControlMeasurementTest.* | none -> M8 |
| 6 | landed handling (t_fb zero, ramp, lead off, blend track) | LandedTest.* , LandedKeepsActuatorModelRunning | none -> M5, M6, M13 |
| 7 | rate lead (K*tau gain, setpoint derivative, clamp) | IndiRateControlLeadTest.*, SetpointLeadTest.* | none -> M2, M11, M14 |
| 8 | yaw increment inversion (g2/dt * prev increment) | YawInvTest.* | none -> M10, M16 |
| 9 | yaw filters | YawCutoff*, YawRateFilter* | none -> M18 |
| 10 | dt validity / fault hold | InvalidInputsHoldLastOutputAndFault, LeadKeepsFaultHold | none -> M12 |
| 11 | max increment clamp | InvalidMaxIncrementKeepsLastValidLimit | none -> M12b |
| 12 | blend rate (time constant) and maybe_landed freeze, blend clamp | BlendTest.* | none -> M7, M19, M20 |
| 13 | accel: t_c = t_f + (a_c - a_f) | IndiAccelControlTest, AccelBlendTest | none -> A1 |
| 14 | accel velocity/position P terms, limits (xy scale, z clamp) | ReferenceHandlingAndVelocityLimits | none -> A2-A6 |
| 15 | accel blend sign / frozen conditions (hold, alloc_sat, coll clamp, u at limit) | AccelBlendTest.Frozen* | none -> A7-A11 |
| 16 | jerk difference clamp / hold / filtered source | JerkBackwardDifferenceAndHold, A18* | none -> A12, A13, A18 |
| 17 | jerk feedforward omega_ff sign | A18CircleAnalyticBodyRates, JerkFeedforwardSign | none -> A4 |
| 18 | accel dt clamp (kMinDt/kMaxDt) | (none found for kMaxDt) | none -> A14 |
| 19 | tilt limit, collective limits, z-only | TiltLimitKeepsVertical..., IndiAccelZOnlyTest.* | T206 items 1-5 (killed) ; tilt scale A15 new |
| 20 | measurement delay index | FilterMatching, MeasurementDelayClamp | none -> A16 |
| 21 | yawspeed feedforward pass-through | NaNYawKeepsCurrentYaw | none -> A17 |
| 22 | stage mode selection, want, model-force, dt gate, hold fallback, resets (IndiStageMode) | IndiStageModeTest.* | none -> H1-H8 |
| 23 | failsafe setpoint | FailsafeSetpointTest.* | none -> H9, H10 |
| 24 | EKF reset detect | EkfResetDetectTest.* | none -> H11, H12 |
| 25 | setpoint extrapolation (cap, 0.5 a t^2) | SetpointExtrapolationTest.* | none -> H13, H14 |
| 26 | measured torque: frozen-telemetry detection, staleness, rpm to u, dropped-sample | IndiMeasuredTorqueTest.*, IndiFrozenRpmTest.* | none -> H15-H20 |
| 27 | rate feedforward gate | IndiRateFeedforwardGateTest.* | none -> H21, H22 |
| 28 | setpoint timeout watchdog | IndiRateSetpointWatchdogTest.* | none -> H23-H25 |
| 29 | torque stamp tracker (foreign stamp) | IndiTorqueStampTrackerTest.* | none -> H26, H27 |
| 30 | IndiInjection / IndiInjectionStep / IndiPosInjection (excitation waveform) | IndiInjection*Test, IndiPosInjectionTest | S196: 67 mutations, 58 killed, 9 equivalent, 0 survived; 14 real pre-fix survivors killed by 8 new tests, see g7_s196/INJECTION_BREAK_CHECK.md |

Already break-checked before this task: 1 behaviour group (accel z-only/thrust-direction items, T206: 9 mutations, all killed). Behaviours 1-29 otherwise had no record.

## 2. Mutation table
Abbrev: R = src/lib/indi_rate_control/indi_rate_control.cpp, A = src/lib/indi_accel_control/indi_accel_control.cpp, P = src/modules/mc_indi_pos_control, M = src/modules/mc_indi_rate_control.
| id | file:line | mutation | result |
|---|---|---|---|
| M1 | R:411 | nu = K*(-rate_error) (sign) | killed: 18 tests, e.g. ConstantDisturbanceRejectedWithoutIntegrator, LeadZeroIsBitIdentical |
| M2 | R:458 | (1+lead)*a_f -> lead*a_f (dropped term) | killed: LeadAddsKTauAccel, LeadPerAxisGain, LeadGainIsClampedToTwo |
| M3 | R:472 | t_cmd = dt_cmd (t_fb dropped) | killed: FollowsMeasurementWhenModelIsWrong, TakeoffRamp-class tests |
| M4 | R:356 | t_f_meas + blend -> t_f_meas | killed: SteadyGapConvergesToModel, SwitchFromModelToMeasurementIsBumpless, WeakMotorStandingError... |
| M5 | R:336 | blend update `&& !landed` removed | killed: LandedBlendTracksWithoutAccumulating, LandedToAirborneWithSteadyGapHasNoBlendStep |
| M6 | R:416 | landed ? 0 : t_f -> t_f | killed: TakeoffRamp, TouchdownRamp, LandedKeepsActuatorModelRunning |
| M7 | R:339 | blend alpha dt/(tc+dt) -> dt/(tc+2dt) | **SURVIVED** |
| M8 | R:328 | valid cycles `>=` -> `>` | killed: HighFrequencyFollowsMeasurement, DisabledIsBitIdentical... |
| M9 | R:271 | actuator alpha time constant x2 | killed: PassThroughFiltersAndDelay, MeasurementEqualToModelSwitchesWithoutTransient |
| M10 | R:457 | yaw prev_inc term dropped | killed: ClosedLoopYawStepSettlesWithoutOscillation, DcGainAndTimeConstantIndependentOfDt |
| M11 | R:458 | lead * rate_sp_dot sign flipped | killed: AttitudeStepOvershootBounded |
| M12 | R:231 | dt <= kMaxDt check removed | killed: InvalidInputsHoldLastOutputAndFault |
| M12b | R:471 | max_increment clamp removed | killed: InvalidMaxIncrementKeepsLastValidLimit, LandedKeepsActuatorModelRunning |
| M13 | R:433 | landed ramp slew clamp removed | killed: TakeoffRamp, LandedBlendTracksWithoutAccumulating |
| M14 | R:404 | rate_sp_dot clamp removed | killed: NoImpulseFromSetpointStepOrReset |
| M15 | R:285 | delay index ignores delay | killed: PassThroughFiltersAndDelay |
| M16 | R:477 | _yaw_inc_prev = 0 | killed: ClosedLoopYawStepSettlesWithoutOscillation, DcGainAndTimeConstantIndependentOfDt |
| M18 | R:380 | yaw accel LPF bypassed | killed: YawCutoffReducesYawNoiseOnly |
| M19 | R:338 | maybe_landed blend freeze removed (`if (true)`) | **SURVIVED** |
| M20 | R:352 | blend clamp +-kMaxBlend removed | **SURVIVED** |
| M21 | R:268 | torque_allocated_prev clamp +-1 widened to +-100 | **SURVIVED** |
| A1 | A:425 | t_c = t_f + a_c (a_f dropped) | killed: ConvergesToThrustGap, ConvergesToLargeThrustGap04 |
| A2 | A:362 | velocity P sign flipped | killed: ReferenceHandlingAndVelocityLimits |
| A3 | A:325 | position P sign flipped | killed: ReferenceHandlingAndVelocityLimits |
| A4 | A:506 | omega_ff pitch sign flipped | killed: A18CircleAnalyticBodyRates, A18StepThenHoldGivesZeroJerk |
| A5 | A:357 | vz clamp uses up-limit for down | killed: ReferenceHandlingAndVelocityLimits |
| A6 | A:352 | xy velocity scale -> 1 (limit off) | killed: ReferenceHandlingAndVelocityLimits |
| A7 | A:416 | blend gap sign flipped | killed: ConvergesToThrustGap, ConvergesToLargeThrustGap04 |
| A8 | A:413 | frozen: alloc_saturated removed | killed: FrozenWhenAllocatorSaturated |
| A9 | A:412 | u_at_limit forced false (first try, removing it from line 413, was an unused-variable compile error, invalid) | killed: FrozenWhenMeasuredUAtLimit |
| A10 | A:413 | frozen: _coll_clamped removed | killed: FrozenWhileCollectiveClamped |
| A11 | A:413 | frozen: _blend_hold removed | killed: FrozenAtE7EdgeSingleCycle, FrozenOnLandedHold |
| A12 | A:219 | jerk clamp removed | killed: JerkBackwardDifferenceAndHold |
| A13 | A:342 | jerk from difference -> 0 | killed: A18ResetMidRampGivesNoPulse, A18StepThenHoldGivesZeroJerk |
| A14 | A:309 | `in.dt > kMaxDt` rejection removed | **SURVIVED** |
| A15 | A:445 | tilt tan(tilt_max)*2 | killed: TiltLimitKeepsVerticalComponent, VerticalDemandNotLimitedByThreeAxisTiltLimit |
| A16 | A:374 | measurement delay ignored | killed: FilterMatching, MeasurementDelayClamp |
| A17 | A:518 | yawspeed_ff always 0 | killed: NaNYawKeepsCurrentYaw |
| A18 | A:223 | jerk hold never expires | killed: A18StepThenHoldGivesZeroJerk |
| H1 | P/IndiStageMode.hpp:36 | ignore model_force | killed: ModelForceSelectsModelAccelEvenWithFreshAccel |
| H2 | P/IndiStageMode.hpp:32 | !rate_ok no longer holds | killed: OtherFailuresHold, SampleIntervalGate |
| H3 | P/IndiStageMode.hpp:42 | armed dropped from want | killed: ComputeWantIndi |
| H4 | P/IndiStageMode.hpp:52 | maybe_landed dropped from modelled force | killed: GroundAndRampUseModelledForce |
| H5 | P/IndiStageMode.hpp:101 | interval limit 0.2 -> 10 s | killed: SampleIntervalGate |
| H6 | P/IndiStageMode.hpp:107 | dt min clamp removed | killed: SampleIntervalGate |
| H7 | P/IndiStageMode.hpp:74 | hold fallback thrust 0.5 -> 0 | killed: HoldFallbackNeverHoverThrustOnGround |
| H8 | P/IndiStageMode.hpp:80 | arm-edge reset -> false | killed: ArmEdgesResetStageState |
| H9 | P/FailsafeSetpoint.hpp:54 | blind-land speed -> 0 | killed: MatchesStockRuleTableOnAllCombinations, NamedCases |
| H10 | P/FailsafeSetpoint.hpp:67 | blind-descent accel 0.3 -> 0 | killed: MatchesStockRuleTableOnAllCombinations, NamedCases |
| H11 | P/EkfResetDetect.hpp:26 | heading counter ignored | killed: EachCounterBumpIsDetectedOnce |
| H12 | P/EkfResetDetect.hpp:24 | `_initialized` -> true (first sample reports reset) | killed: FirstSampleDoesNotReset (first attempt, a multi-line edit, failed to apply and was repeated) |
| H13 | P/SetpointExtrapolation.hpp:36 | max_dt cap removed | killed: DtIsCapped |
| H14 | P/SetpointExtrapolation.hpp:50 | 0.5*acc -> acc | killed: DtIsCapped, PositionVelocityAndAcceleration |
| H15 | M/IndiMeasuredTorque.cpp:135 | frozen test `>` -> `<` | killed: ArmingEdgeStartsANewWindow, ConstantRpmConstantCommandStaysValid |
| H16 | M/IndiMeasuredTorque.cpp:186 | `omega >= 0` guard removed | **SURVIVED** |
| H17 | M/IndiMeasuredTorque.cpp:222 | sample max age x100 | killed: RotorSpeedsGiveAllocatedTorque |
| H18 | M/IndiMeasuredTorque.cpp:187 | u = ratio instead of ratio^2 | killed: RotorSpeedsGiveAllocatedTorque |
| H19 | M/IndiMeasuredTorque.cpp:175 | dropped-sample (error_count change) detection off | **SURVIVED** |
| H20 | M/IndiMeasuredTorque.cpp:70 | small-row threshold 0.05 -> 5 | killed: ActuatorsMapBackToAllocatedControl, RotorSpeedsGiveAllocatedTorque |
| H21 | M/IndiRateFeedforwardGate.cpp:39 | landed no longer blocks | killed: LandedBlocks |
| H22 | M/IndiRateFeedforwardGate.cpp:45 | max age x10 | killed: StaleBlocks |
| H23 | M/RateSetpointWatchdog.cpp:42 | timeout x10 | killed: StaleAfterTimeoutZeroesRates, FreshMessageClearsInOneCycle |
| H24 | M/RateSetpointWatchdog.cpp:40 | armed dropped | killed: InactiveDisarmedOrAcro |
| H25 | M/RateSetpointWatchdog.cpp:48 | warn rate limit off | killed: WarningIsRateLimited |
| H26 | M/TorqueStampTracker.cpp:41 | `timestamp != 0` guard removed | **SURVIVED** |
| H27 | M/TorqueStampTracker.cpp:50 | CLEAR_COUNT -> 1 | **SURVIVED** |

Counts: 66 valid new mutations (21 rate lib, 18 accel lib, 27 helpers): 57 killed, 9 survived (M7, M19, M20, M21, A14, H16, H19, H26, H27). Two further attempts were invalid (compile error / failed to apply) and repeated as A9 and H12. (T206 prior: 9 mutations, 9 killed, not re-run.)

## 3. Survivors (no new tests written, per task)
| id | mutation | why tests miss it | test that would kill it |
|---|---|---|---|
| M7 | blend alpha dt/(tc+dt) -> dt/(tc+2dt) | blend tests assert only convergence/boundedness, with tolerances looser than a 2x change of tc | drive a constant gap and assert the blend after N cycles equals gap*(1-(tc/(tc+dt))^N) within 1% |
| M19 | maybe_landed freeze of blend removed | MaybeLandedPulseNoStep checks the output step, which the blend does not produce in the pulse length used | hold a nonzero gap change across a maybe_landed pulse and assert _blend (t_f) unchanged while maybe_landed |
| M20 | +-kMaxBlend clamp removed | no test feeds a gap above kMaxBlend | feed a measurement offset greater than kMaxBlend, assert blend saturates at kMaxBlend |
| M21 | allocated torque clamp to +-1 widened | downstream t_cmd clamp hides it; no out-of-range torque_allocated_prev input | pass torque_allocated_prev = 5 and compare to the same run with 1 (t_f_model must be identical) |
| A14 | in.dt > kMaxDt no longer returns false | no test passes dt above kMaxDt (kMinDt side is covered by other tests, kMaxDt only by stage helper) | call update with dt = kMaxDt*1.1 and expect false with output untouched |
| H16 | negative-rpm guard (omega >= 0) removed | no test feeds a negative rpm | setMotorSample(rpm = -5000) then expect motor not valid / result.valid false |
| H19 | error_count change no longer drops the sample | tests never change error_count between samples with a changed rpm | second sample with a different error_count and a wildly different rpm; expect it ignored (timestamp_good and u unchanged) |
| H26 | timestamp 0 accepted as own (zero-initialised ring) | no test passes timestamp 0 to checkReceived | checkReceived(0) on fresh tracker must return true (foreign) |
| H27 | CLEAR_COUNT -> 1 | tests do not check that foreign stays set until CLEAR_COUNT consecutive own stamps | after a foreign stamp, send CLEAR_COUNT-1 own stamps and assert still foreign, then one more and assert cleared |

## 4. Tree state
Every mutation was reverted with `git checkout -- <file>` right after its run. Final check:
`git status --short -- src` : (empty output); `git diff --stat -- src` : (empty).
Note: indi_flight/STATE.md was already modified before the audit (unrelated); no commit was made. No container left running.

## 5. Unverified
- Behaviour 30 (IndiInjection, IndiInjectionStep, IndiPosInjection): break-checked in S196, 67 mutations, 58 killed, 9 equivalent by reading, 0 survived (g7_s196/INJECTION_BREAK_CHECK.md; its Unverified section lists the open points).
- Several mutation rows list only the first 1-3 failing tests (full lists are in the run output, not saved).
- Tests were run per ctest regex filter; the full-suite pass of the unmutated tree is the earlier 13/13 record (NUTTX_FIX.md), not re-run here.
- Not mutated: yaw-cutoff design branch, sample-rate redesign, measurement-delay slew, accel reset(), bodyzToAttitude, zero-thrust-dir helper, shouldResetOnPosControlEntry/HoldToRun, deriveZOnly.
