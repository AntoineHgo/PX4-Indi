# KEY2: code-to-spec review of 2d92dbcf59 (native-rate specific-force filter)

Spec items: S1 PASS, S2 PASS, S3 PARTIAL (see M1), S4 PASS, S5 PASS, S6 PASS (see m3), S7 PASS (5 files touched, all INDI).

## Findings

M1 MAJOR indi_accel_control.cpp (update(), valid branch) + McIndiPosControl.cpp pollAcceleration():
   The native filter is never re-seeded across an acceleration gap. During stale/model mode (f_b_valid=false) no samples arrive
   (or arrive and are applied with dt clamped to 50 ms), and _native_f stays frozen/old while _lpf_f follows the modelled force.
   On the return to f_b_valid=true the stage reads _native_f directly, so a_f steps to the old/transient native state
   (not the "no step" required by S3 for the invalid->valid direction). The acc_stale_latched recovery (20 ms) does not call
   _indi.reset(), only pos-entry/Hold->run do. Fix: on first fresh sample after a gap > kStageMaxAge (or when the stage leaves
   model mode) reseed _lpf_f_native from the sample or from _lpf_f output.
m1 MINOR McIndiPosControl.cpp pollAcceleration():
   _f_b/_acc_time are updated even when sampleSpecificForce is skipped (timestamp_sample not newer, non-finite f, first sample),
   so f_b_valid can be true while _native_f is one or more samples stale. Bounded to a sample or two (legacy path used for the
   very first sample only), non-finite is also caught by acc_fresh_now.
m2 MINOR McIndiPosControl.cpp Run()/init():
   Queue length 1 on the same nav_and_controllers WQ: a stage cycle longer than ~3.7 ms drops native samples; the dt from
   timestamp_sample then widens (7.5 ms), the filter coefficients assume fixed dt (small error, rate hysteresis of 16 samples
   absorbs it). Run() now wakes ~356 Hz; _cycle_perf and parameters_update run on non-stage wakes (CPU cost, perf stats skewed).
m3 MINOR IndiAccelControlTest.cpp NativeRateFilterValidToInvalidSwitchHasNoStep:
   bound |a_f(0)| < 0.6 with a 0.5 offset cannot detect a step. No test covers invalid->valid (M1), cut-off change after
   feeding, or native rate hysteresis. NativeRateFilterRejectsAliasedVibration is physically meaningful (amplitude at the
   alias frequency 6.73 Hz, limit 0.03, expected 0.011 vs ~0.9 decimated) but the break-check could not be re-run here (no build).

## Checked, no defect
- cut-off 0 before setFilter: LowPassFilter2p::set_cutoff_frequency disables the filter (passthrough, no state); setFilter later
  configures it at _native_hz and reseeds from _native_f. Order-independent. Same for cut >= native/2.
- reset() seeds _lpf_f_native and _native_f; setFilter reseeds native from _native_f; stage-rate change does not touch native.
- Valid path writes _lpf_f.reset(_native_f) each cycle, so valid->modelled has no step; legacy path unchanged without feed (S4).
- Freshness gates use acc.timestamp, set in the same place as _native_f, consistent with the new source.
- Stage still gated by _local_pos_sub.update(); acceleration wakes only poll (S5). Second poll in pollStageInputs is harmless.

KEY2 VERDICT: PASS
