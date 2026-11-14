# 10 Conclusion

## 10.1 Answer to the research question

The question was whether an INDI controller can replace the PID angular-rate loop of a PX4 multicopter and do better, judged by a benchmark whose scenarios, metrics and acceptance criteria were frozen before INDI first flew. In simulation, on the `gz_x500` airframe, the answer is no. Under the frozen rules the outcome is "INDI does not outperform PID" (`results/acceptance_s15.md`).

The verdict follows from two failed criteria. Criterion 3 requires that INDI is not significantly worse by more than 10 % on any held-out scenario, and it fails on H5, the combined mismatch scenario: roll-rate RMS during the rate pulses is 1.58 times that of PID, with 0 of 10 seeds better and p = 0.002 (`results/acceptance_s15.md`). Criterion 1 requires that no INDI run fails, and it fails on H4, the double motor failure, where INDI crashes on 10 of 10 seeds. PID also crashes on 10 of 10, and the two controllers behave alike until impact, but the criterion is stated for INDI alone and was applied as written. The verdict does not depend on H4, because criterion 3 fails on H5 by itself. The spec's "matches" outcome is available only if criteria 1 and 3 hold, so it is unavailable too (`bench/scenarios.md`, section 6; see section 8.2).

This is a loss and is reported as one. Two post-hoc rule changes were considered, averaging the two parts of H5 and excluding H4, and both were rejected because they would not change the outcome and would be made after seeing the data (chapter 9, section 9.1). The result is not evidence that INDI is the worse controller on average. It is evidence that INDI did not meet a strict no-regression standard on this vehicle in this simulator.

## 10.2 Main quantitative findings

**Disturbance rejection is better on every disturbance scenario.** The attitude RMS ratio INDI/PID is 0.16 on the centre-of-mass shift (H3), 0.57 on the diagonal gust (H2), 0.60 on the gust along x (T6), 0.72 on payload addition (T7) and 0.88 on inertia mismatch (T9), lower on 10 of 10 seeds in each case, with p = 0.002 (`results/heldout_s14.md`). On the motor-loss scenario T8, with 3 seeds, the peak tilt error at fault onset is 1.6 deg for INDI against 5.1 deg for PID (`results/t8_motor_loss_s13.md`). Several of the absolute errors are tenths of a degree, so a low ratio can describe a small quantity (section 9.1).

**Nominal tracking is at parity.** The tuning-set cost of the frozen INDI candidate is 0.978 against about 0.96 for PID, a tie within the hover noise (`results/tuning/r4f.md`). Hover motor-rate effort is 0.0387 against 0.0371 /s, a ratio of 1.04 (`results/acceptance_s15.md`). On the lemniscate (T5) the position RMS ratio is 0.95, with a maximum deviation 1.08 times that of PID (`results/heldout_s15.md`).

**Yaw is worse whenever it is commanded.** On the diagonal step H6 the yaw ratio is 1.31 (`results/heldout_s14.md`), and the yaw sweep of round r4 found no INDI parameter set that beat PID on the yaw step at acceptable effort (`results/tuning/r4.md`; section 9.3).

**Under actuator-model mismatch INDI develops a limit cycle.** In H5 a 5-7 Hz roll limit cycle gives a control effort of 3.08 times PID (`results/heldout_h5_s15.md`). INDI also saturates more than PID on T8: 12 % against 7.5 % (`results/t8_motor_loss_s13.md`).

The PID baseline was searched over 64 candidates and none beat the PX4 defaults, so the comparison is against defaults that were confirmed, not assumed (`results/tuning/r2.md`).

## 10.3 The main weakness and its mechanism

The weakness that decides the verdict is the dependence of INDI on its actuator model. The incremental law adds a torque increment to an estimate of the torque already applied, and that estimate depends on the modelled actuator time constant (`MC_INDI_ACT_TC`). The control-law review found that a model slower than the plant amounts to a gain reduction and is safe. The dangerous case is a plant slower than the model, which produces a band-pass boost of the loop near 1/(2 pi sqrt(tau_e tau_t)), with tau_e and tau_t the modelled and true time constants.

The experiments agree with this. In H5, doubling the motor time constant alone reproduces the limit cycle, inertia and mass errors alone do not, and the limit cycle vanishes when `MC_INDI_ACT_TC` is matched (`results/heldout_h5_s15.md`). A later sweep of `MC_INDI_ACT_TC` from 0.33 to 3 times nominal on the stock plant gave no limit cycle, with roll-rate RMS between 0.129 and 0.161 (`results/act_tc_sweep_s17.md`). The ratio alone therefore does not explain H5: the limit cycle needs a physically slower actuator that the model does not know. This is why the weakness is an actuator-model problem and not a gain-tuning problem.

## 10.4 Limits and future work

The conclusion rests on one simulated airframe and no hardware flight. The disturbance comparison is also conditional on neither controller having been tuned for disturbance rejection (section 9.1), and a different vehicle could change the ranking either way (section 9.4).

Section 9.5 lists what remains before real flight and is not repeated here. The first item follows directly from this report: decide how the actuator state is obtained on hardware, from ESC telemetry or from a measured and verified time constant, and test sensitivity to mismatch in both directions on more than one airframe. Identification of the control effectiveness and motor time constant on a real vehicle, SIH and hardware-in-the-loop tests, a decision on whether yaw should stay on PID, and a staged flight protocol with criteria fixed in advance complete the list.

On this evidence, INDI is worth pursuing where disturbance rejection matters and the actuator dynamics can be measured. It should not replace the PID rate loop as a default without a way to detect or bound the actuator-model error.
