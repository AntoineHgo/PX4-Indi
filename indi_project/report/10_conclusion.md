# 10 Conclusion

## 10.1 Answer to the research question

The question was whether an INDI controller can replace the PID angular-rate loop of a PX4 multicopter and do better, judged by a benchmark whose scenarios, metrics and acceptance criteria were frozen before INDI first flew. In simulation, on the `gz_x500` airframe, the answer is no. Under the frozen rules the outcome is "INDI does not outperform PID" (`results/acceptance_s15.md`).

The verdict follows from two failed criteria. Criterion 3 requires that INDI is not significantly worse by more than 10 % on any held-out scenario, and it fails on H5, the combined mismatch scenario: roll-rate RMS during the rate pulses is 1.58 times that of PID, with 0 of 10 seeds better and p = 0.002 (`results/acceptance_s15.md`). Criterion 1 requires that no INDI run fails, and it fails on H4, the double motor failure, where INDI crashes on 10 of 10 seeds. PID also crashes on 10 of 10, and the two controllers behave alike until impact, but the criterion is stated for INDI alone and was applied as written. The verdict does not depend on H4, because criterion 3 fails on H5 by itself. The spec's "matches" outcome is available only if criteria 1 and 3 hold, so it is unavailable too (`bench/scenarios.md`, section 6; see section 8.2).

This is a loss and is reported as one. Two post-hoc rule changes were considered, averaging the two parts of H5 and excluding H4, and both were rejected because they would not change the outcome and would be made after seeing the data (chapter 9, section 9.1). The result is not evidence that INDI is the worse controller on average, nor that it is the better one. It is evidence that INDI did not meet a strict no-regression standard on this vehicle in this simulator.

## 10.2 Main quantitative findings

**Attitude disturbance rejection is better on all four disturbance scenarios (T6, T7, H2, H3) and at T8 fault onset.** The attitude RMS ratio INDI/PID is 0.16 on the centre-of-mass shift (H3), 0.57 on the diagonal gust (H2), 0.60 on the gust along x (T6) and 0.72 on payload addition (T7), lower on 10 of 10 seeds in each case, with p = 0.002 (`results/heldout_s14.md`). On the motor-loss scenario T8 the peak tilt error at fault onset is 1.6 deg for INDI against 5.1 deg for PID, lower on 10 of 10 seeds, but the whole-window rotation RMS is 14 % worse because of the yaw step that follows (`results/t8_motor_loss_10seeds_s26.md`). On the plant-mismatch scenario T9 (inertia error) the ratio is 0.88, also 10 of 10 seeds. Several of the absolute errors are tenths of a degree, so a low ratio can describe a small quantity (section 9.1).

**Nominal tracking is at parity.** The tuning-set cost of the frozen INDI candidate is 0.978 against about 0.96 for PID, a tie within the hover noise (`results/tuning/r4f.md`). Hover motor-rate effort is 0.0387 against 0.0371 /s, a ratio of 1.04 (`results/acceptance_s15.md`). On the lemniscate (T5) the position RMS ratio is 0.95, with a maximum deviation 1.08 times that of PID (`results/heldout_s15.md`).

**Yaw is worse whenever it is commanded.** On the diagonal step H6 the yaw ratio is 1.31 (`results/heldout_s14.md`), and the yaw sweep of round r4 found no INDI parameter set that beat PID on the yaw step at acceptable effort (`results/tuning/r4.md`; section 9.3).

**Under actuator-model mismatch INDI develops a limit cycle.** In H5 a 5-7 Hz roll limit cycle gives a control effort of 3.08 times PID (`results/heldout_h5_s15.md`). INDI also saturates more than PID on T8: 12 % against 7.5 % (`results/t8_motor_loss_s13.md`).

The PID baseline was searched over 40 candidates and none beat the PX4 defaults, so the comparison is against defaults that a 40-candidate random search did not beat; this shows they are hard to improve by sampling, not that they are optimal (`results/tuning/r2.md`).

## 10.3 The main weakness and its mechanism

The weakness that decides the verdict is the dependence of INDI on its actuator model. The incremental law adds a torque increment to an estimate of the torque already applied, and that estimate depends on the modelled actuator time constant (`MC_INDI_ACT_TC`). The control-law review argues that a model slower than the plant amounts to a gain reduction and should be benign, which the post-acceptance sweep on the stock plant (factor 1.5-3, 3 seeds) is consistent with. The dangerous case is a plant slower than the model, which produces a band-pass boost of the loop near 1/(2 pi sqrt(tau_e tau_t)), with tau_e and tau_t the modelled and true time constants.

The experiments agree with this. In H5, doubling the motor time constant alone reproduces the limit cycle, inertia and mass errors alone do not, and the limit cycle vanishes when `MC_INDI_ACT_TC` is matched (`results/heldout_h5_s15.md`). A post-acceptance sweep (session 17, not part of the frozen result) of `MC_INDI_ACT_TC` from 0.33 to 3 times nominal on the stock plant gave no limit cycle, with roll-rate RMS between 0.129 and 0.161 (`results/act_tc_sweep_s17.md`). The ratio alone therefore does not explain H5: the limit cycle needs a physically slower actuator that the model does not know. The sensitivity is to an actuator slower than modelled; whether lower gains would buy tolerance to it was not evaluated.

## 10.4 Limits and future work

The conclusion rests on one simulated airframe and no hardware flight. The disturbance comparison is also conditional on neither controller having been tuned for disturbance rejection (section 9.1), and a different vehicle could change the ranking either way (section 9.4).

Section 9.5 lists what remains before real flight and is not repeated here. The first item follows directly from this report: decide how the actuator state is obtained on hardware, from ESC telemetry or from a measured and verified time constant, and test sensitivity to mismatch in both directions on more than one airframe. Identification of the control effectiveness and motor time constant on a real vehicle, SIH and hardware-in-the-loop tests, a decision on whether yaw should stay on PID, and a staged flight protocol with criteria fixed in advance complete the list.

On this evidence, INDI is worth pursuing where disturbance rejection matters and the actuator dynamics can be measured. It should not replace the PID rate loop as a default without a way to detect or bound the actuator-model error.

## 10.5 Stage 2: measured actuator state and the v3 blend

Stage 2 moved INDI into its own module (`mc_indi_rate_control`, O-11), gave it the actuator state from simulated ESC
rotor-speed telemetry (v2), added realistic sensing (1 kHz gyro, vibration, eRPM quantisation, latency and drop-outs),
retuned the PID baseline for that simulation, and judged the result on two new held-out sets frozen in advance.

**The answer does not change: INDI does not outperform PID.** INDI v2 lost on V, 8 of 14 entries worse by more than
10 % (section 8.9). INDI v3 reaches parity with the tuned PID on V', within 5 % on every completed entry and never
significantly worse, but better by 10 % on none (section 8.10).

**The stage's main finding is a mechanism.** Feeding the measured rotor speed back as the actuator state makes INDI
exact about the torque the rotors produce and therefore blind to any gap between command and output: the fixed point
holds that gap with a standing rate error, and on a motor fault v2 settled at a 13-14 deg tilt where v1 and PID
recovered (section 8.9). Measured actuator feedback removes the implicit integral action of the model-based INDI. The
v3 blend, measured state above 1/(2 pi Tb) and modelled state below it, restores that action and removes every
actuator-gap failure of v2 (9.1x, 2.7x and 1.9x the tuned PID become 0.95x, 1.01x and 0.99x). Hardware INDI built on
ESC telemetry should be designed with this in mind.

**Hover effort stays about 2x PID's** in every stage-2 version. Most of it is structural: the acceleration feedback
at gain 1/G1 passes 30-80 Hz gyro and vibration noise to the torque command, which only a lower, synchronised INDI
filter cut-off could reduce, at a cost in phase (section 8.10). The ratio itself is fragile: in one re-flown batch the tuned PID's
hover effort doubled (a 2-4 Hz roll mode of unknown cause) and the ratio fell to 0.96, while INDI's stayed the same.

**Two V' entries measure the vehicle, not the controllers**: the x500 cannot hold altitude with one motor at 0.6
thrust, and loses it in about half the runs at 75 % battery thrust, whatever the controller. Their severity was not
checked before V' was frozen.

The outer-loop (linear acceleration) INDI of stage 8 had not been evaluated when this section was written.
