# A-22 closure: links a and b of the roll G1 chain (S44)

Log: `indi_flight/results/stage2_s41/model_long_s2/flight.ulg` (window 52-82 s unless stated). No simulation run. Scratch analysis script: `/tmp/claude-1001/-home-ahugo-Documents-Drotek-Codes-PX4-Indi/61c664ec-a260-4139-882b-0a4be4b38266/scratchpad/s44.py` and the inline emulation in this session (not saved in the repo).

## Result in 6 lines

1. A-22 is closed as a measurement artefact, not a source or parameter effect: in the 52-82 s window the vehicle is in a 17 Hz saturated limit cycle (all three torque axes show a spectral peak at 17.0 Hz; pitch u rms 0.43, yaw u rms 0.22, roll u rms 0.04, versus 0.0011 / 0.0010 / 0.0003 at 32 s on the ground). The onset is at liftoff: pitch u rms 0.004 at 33 s, 0.21 at 34 s, 0.43 at 35 s.
2. Source and log agree wherever the allocator is linear: the actuator_outputs rows t = 31.06-33.66 s (takeoff ramp, a = 0.003 to 0.135) give out/2700 = sqrt(a) to 4 digits (a = 0.0824 -> 775.1 rad/s vs 2700 sqrt(a) = 775.1; a = 0.1308 -> 976.2 vs 976.6). So link b static map is x = a (slope 1.0), exactly as THR_MDL_FAC = 1 predicts. The first row that departs is t = 33.76 s (a = 0.1406, out 871 vs 1012), i.e. the start of the oscillation.
3. In the window the logged motors sit at exactly zero (below 0.005) in 89 % of samples; the pitch/yaw saturation + `desaturateActuators` + clip at 0 remove most of the roll authority. This is what the 0.23 per motor (IV) / 0.344 per motor (LS, lag 0) in link a is. Source linear value 0.7071 per motor, 2.828 differential.
4. The 0.59 of link b is not a map: actuator_outputs alternates between motor pairs (e.g. t = 50.06 s `[1793, 0, 1793, 0]`, t = 50.258 s `[0, 1794, 0, 1794]`), the 4-motor mean (898 median, 974 mean) is the average of a 0/1794 chatter, and the rotor speed w (std 212 rad/s about a mean of 976) is that chatter low-pass filtered by the 33 ms motor. True mean x = E[(w/2700)^2] = 0.1369 (= MPC_THR_HOVER 0.137, 0.61 kg hover), against (E[w]/2700)^2 = 0.1308 (the S43 "0.131") and mean a = 0.2211. The 0.2211 "hover thrust" (hover estimator, `vehicle_thrust_setpoint`) is the limit-cycle value, not the plant hover.
5. Predicted linear static roll G1 = 2.828 x 1.0 x 621 = 1756 (S43 c = 626 gives 1771; closed form below 1759-1762). Measured 340: 5.2x lower, FAILS the 10 % test. But 340 is the effective gain of a saturated limit cycle (0.325 x 0.59 x 1756 = 337), not the small-signal G1 of the plant. The 878 was also wrong (see below), and 1756 is the number the source predicts for any unsaturated hover.
6. Consequence: `MC_INDI_G1_R` 320 (and G1_P 210) are 5.5x (8x) below the source value 1756; INDI adds delta_u = delta_alpha / G1, so the loop gain seen by the plant is 5.5x nominal. This is a candidate cause of the limit cycle (UNVERIFIED, needs a run with G1_R about 1750).

## Link a: torque_setpoint -> actuator_motors roll differential

Responsible code (file:line, checked-out tree = tree at the log's `ver_sw` 32500e0276, `git diff --stat 32500e0276 HEAD` over control_allocation, control_allocator, mixer_module, gz_bridge, mc_indi_rate_control and the 4040 airframe is empty; `run.json` records commit c13b638770 dirty, so the binary may still differ from the tree):

| step | file:line | value for this airframe |
|---|---|---|
| effectiveness column, moment = ct * (p x axis) - ct km axis | `src/modules/control_allocator/VehicleActuatorEffectiveness/ActuatorEffectivenessRotors.cpp:197` | roll row ct*py = 0.5168, thrust row -6.5 |
| pseudo-inverse | `src/lib/control_allocation/control_allocation/ControlAllocationPseudoInverse.cpp:72` (`matrix::geninv`) | roll column 1/(4 ct py) = 0.4838 |
| normalisation scale (roll = pitch = max(sqrt(norm2/(n/2)))), yaw by column max, thrust col so a_i = thrust_sp | `ControlAllocationPseudoInverse.cpp:87-130`, `:155-170` | scale 0.6842 -> roll per motor 0.7071, yaw 1.0, thrust a_i = T |
| CA_METHOD 2 (AUTO) picks sequential desaturation for multirotor, MC_AIRMODE 0 | `src/modules/control_allocator/ControlAllocator.cpp:173-190`; `ControlAllocationSequentialDesaturation.cpp:44-65` | `mixAirmodeDisabled` |
| airmode-disabled mixing: thrust-only-reduce desat, then roll desat, pitch desat, then yaw added, yaw desat (+ MINIMUM_YAW_MARGIN), thrust-only-reduce desat | `ControlAllocationSequentialDesaturation.cpp:204-232` (mixAirmodeDisabled), `:235-255` (mixYaw), `:68-118` (desaturateActuators, computeDesaturationGain) | active whenever any motor leaves [0,1] |
| clip to [0, 1] and publish | `ControlAllocation.cpp` (clipActuatorSetpoint), `ControlAllocator.cpp:446-458` | min 0 set at `ControlAllocator.cpp:536` |

Closed form for a symmetric quad (all |mix_i| equal): mix_i = 1/(n ct py), scale = sqrt(n mix_i^2 / (n/2)) = sqrt(2) mix_i, so a_i = u/sqrt(2) = 0.7071 u. CA_ROTORn_CT and CA_ROTORn_KM cancel from the roll column; CA_ROTORn_PY also cancels (it only changes which physical torque 0.7071 u means). Predicted 0.7071 per motor, differential sum(s_i a_i) = 2.828 u (S43 source reading confirmed; my numpy pseudo-inverse of the effectiveness built from the log's CA_* parameters gives roll `[-0.7071, 0.7071, 0.7071, -0.7071]`, pitch `[0.7071, -0.7071, 0.7071, -0.7071]`, yaw `[1, 1, -1, -1]`, scale 0.6842).

| quantity | predicted (unsaturated) | measured | verdict |
|---|---|---|---|
| roll per-motor gain | 0.7071 | 0.23 (IV, S43), 0.344 (LS lag 0, this session) | does not match; cause identified below |
| roll differential | 2.828 | 0.92 (IV), 1.375 (LS) | same |
| pitch per-motor | 0.7071 | about 0.45 (LS regression on [roll, pitch, yaw, thrust]) | reduced by the same mechanism |
| yaw per-motor | 1.0 | 0.054 | reduced about 18x (yaw has the lowest priority in `mixYaw`) |
| thrust a_i vs -thrust_sp.z | 1.0 | mean 0.22113 vs 0.22113 | matches |

Why the log disagrees (the verdict): `control_allocator_status` in the window has `torque_setpoint_achieved` true in only 11 % of samples, `unallocated_torque[0]` rms 0.031 against roll u rms 0.044 (70 % of the commanded roll torque is not delivered, 0.325 delivered, and 0.23/0.707 = 0.325), `actuator_saturation` mean -0.76 (LOWER = -2 flagged), and 89 % of samples have at least one motor below 0.005. The unsaturated evaluation of the logged u and thrust (no desaturation) has at least one motor below 0 in 89 % of samples (log: 89 % below 0.005). A full replay of the desaturation did not reproduce the logged roll gain (see UNVERIFIED 2). The 0.23 is therefore the delivered fraction of the roll torque once pitch (rms 0.43, i.e. +-0.30 per motor) and yaw saturate the motors; it is not a parameter or scaling effect. Alternative "normalisation / CA_ROTOR_CT / arm geometry / `_normalization_needs_update`" explanations are rejected: they all enter as an unsaturated 0.7071.

## Link b: actuator_motors -> rotor speed

Responsible code:

| step | file:line | value |
|---|---|---|
| thrust model s = -b/(2a) + sqrt(b^2/(4a^2) + a_i/a), a = THR_MDL_FAC, b = 1 - a; THR_MDL_FAC 1 -> s = sqrt(a_i) | `src/lib/mixer_module/functions/FunctionMotors.hpp:81-95` | s = sqrt(a) |
| [0,1] -> [-1,1] remap (non-reversible) | `FunctionMotors.hpp:110-119` | 2s - 1 |
| [-1,1] -> [SIM_GZ_EC_MIN, SIM_GZ_EC_MAX] = [0, 2700] | `src/lib/mixer_module/mixer_module.cpp:565` (`output_limit_calc_single`) | w_cmd = 2700 s |
| gz_bridge scale sqrt(SIM_GZ_THR_SC), param = 1.0 | `src/modules/simulation/gz_bridge/GZMixingInterfaceESC.hpp:82-83`, `GZMixingInterfaceESC.cpp:107-110` | 1 |
| `actuator_outputs` publish (one instance) | `mixer_module.cpp:659-668` | uORB `actuator_outputs`, multi_id 0 only |
| gz velocity motor, kT 1.5e-6, wmax 2700, lag 33 ms | `indi_flight/sim/models/quad5in/model.sdf:12-22` | x = (w/2700)^2 after a 33 ms lag |

Predicted: out = 2700 sqrt(a) and ds/da = 1/(2 sqrt(a)) = 1.06 at a = 0.221 (x = a, slope 1.0 in x per a). Measured on the takeoff ramp (t = 31.06-33.66 s, 27 consecutive 100 ms rows, before the oscillation starts): out/2700 equals sqrt(a) within 1e-3 absolute on every row (table in this session: a = 0.0071 -> 0.0842/0.0844; 0.0555 -> 0.2356/0.2356; 0.1226 -> 0.3500/0.3501; 0.1308 -> 0.3616/0.3617; 0.1352 -> 0.3676/0.3676). Verdict for the map: matches the source. The S43 "0.59" and "ds/da = 0.63" came from the limit-cycle data: after t = 33.76 s the 10 Hz subsample of `actuator_outputs` aliases a 17 Hz bang-bang motor command (pairs 0,2 and 1,3 alternate between 0 and about 1794 = 2700 sqrt(0.44)), the ESC lag and sqrt (Jensen) lower E[x] below E[a], and the clip at 0 raises E[a] above the thrust set point. The hover thrust learned (0.2211) is therefore 1.6x the physical hover (MPC_THR_HOVER 0.137 = E[x_true] 0.1369).

Other checks: `actuator_outputs` has 1 instance (1118 rows, 10 Hz, noutputs 16), `esc_status` 1 instance (789 Hz); the "zero-filled 36 % of rows" of the S43 second key is the 0 half of the 0/1794 chatter, not a second publisher (10 % of rows are fully zero: disarmed before 30 s and after 131 s). esc_rpm -> w = rpm 2pi/60 (code, `GZMixingInterfaceESC.cpp:206-240`; SIM_GZ_ERPM_POL 14 = 7 pole pairs, already undone in the decode): mean w 976.3 rad/s vs mean command 974.5 rad/s, consistent. THR_MDL_FAC and SIM_GZ_EC_* in the log's initial parameters are 1 / 0 / 2700 and `changed_parameters` is empty.

## Predicted G1 and comparison

| factor | value | source |
|---|---|---|
| a (torque_sp -> sum s_i a_i) | 2.828 | link a, unsaturated |
| b (a -> x = (w/wmax)^2, small signal at the hover point) | 1.0 | link b, THR_MDL_FAC 1 |
| c (sum s_i x_i -> alpha, rad/s^2) | 626 measured S43 (621 analytic, kT wmax^2 py / Ixx = 10.935 x 0.0795 / 1.396e-3) | S43 |
| G1 = a b c | 1756 (analytic c), 1771 (measured c) | |
| measured (S43, same log) | 340 | |
| ratio | 5.2x | fails the 10 % test |

The product measured/predicted 340/1756 = 0.194 = 0.325 (delivered torque fraction under saturation) x 0.59 (band-limited, clipped x-per-a of the chatter) which reproduces 337; each factor is a property of the saturated limit cycle, not of the plant, so 340 must not be used as the plant G1. 878 (analytic G1 of `g1_analytic.md`) was wrong only because it used 0.354 per motor for link a (it normalised the forward matrix; the code normalises the pseudo-inverse, 0.7071); the correct linear value is 2 x 878 = 1756.

## What this means for deriving G1 from CA_* parameters

For a quad with equal rotors, THR_MDL_FAC matched to the real thrust curve (then a -> thrust is linear and b = 1), and an allocator that is not saturated, the normalised-torque-to-angular-acceleration gain is G1_roll = sum_i |py_i| T_max,i / (sqrt(2) Ixx) = m g py / (sqrt(2) x_hover Ixx) for a symmetric X quad (T_max,i = kT wmax^2 = m g / (4 x_hover); 0.0795 x 0.61 x 9.81 / (1.414 x 0.137 x 1.396e-3) = 1759). CA_ROTORn_CT and CA_ROTORn_KM do not enter the roll gain at all (they cancel in the pseudo-inverse and normalisation), CA_ROTORn_PX/PY enter once, linearly (arm length); the normalised roll column is 1/sqrt(2) for any n-motor layout whose roll-active rotors have equal |py|, and a general layout needs a_i = mix_i / sqrt(2 sum mix_i^2 / n). The parts that are not in CA_*: the physical thrust at full command (T_max, equivalently hover thrust fraction x_hover and mass) and the moment of inertia Ixx (pitch uses Iyy and px). On an unknown airframe G1 can therefore be derived to better than 5 % only with m, Ixx/Iyy and the hover thrust fraction (MPC_THR_HOVER or `hover_thrust_estimate`, taken from a non-saturated hover; the 0.2211 in this log is the saturated value, 0.137 is right), and with THR_MDL_FAC set so x = a; it must not be regressed from a log that has saturated motors, because the regression returns the delivered fraction (0.19 of the true value here) and then drives the INDI increments 5x too high. Saturation (`torque_setpoint_achieved`, `actuator_saturation`, fraction of samples with a motor at 0) has to be a validity gate for any online G1 estimate.

## UNVERIFIED

1. That the 17 Hz limit cycle is caused by G1_R/G1_P (320/210) being 5.5x/8x too low (INDI loop gain). Only the timing (onset at liftoff, pitch rms 0.004 -> 0.43 between 33 and 35 s) and the 1756 vs 320 factor support it; no run with G1 about 1750 exists. Other causes (rate-loop latency, 20 ms ESC telemetry feedback `MC_INDI_ERPM_*`, yaw channel G1_Y 30) are not excluded. Needs one hover run with MC_INDI_G1_R about 1750 and G1_P scaled by Iyy.
2. The exact allocator output under saturation. A numpy replay of `mixAirmodeDisabled` (logged `vehicle_torque_setpoint` and `vehicle_thrust_setpoint` as inputs, with the final clip to [0,1], MINIMUM_YAW_MARGIN 0.15 = `ControlAllocationSequentialDesaturation.hpp:63`) reproduces the fraction of samples with a motor at 0 (88 % vs 89 %) and the motor correlation (0.93) but NOT the roll gain (replay 0.707 per motor vs 0.344 logged) nor the mean (replay 0.319 vs logged 0.2211, which equals the thrust set point exactly, i.e. the real allocator does not lose or add mean thrust under clipping). So the replay is wrong or incomplete somewhere (candidates: desaturation order or the trim/linearisation point in `ControlAllocation::setEffectivenessMatrix`, the `slew_rate` path, or the binary differing from the tree) and "desaturation + clip explains 0.325 exactly" rests only on the `control_allocator_status` numbers (unallocated roll rms 0.031 vs u rms 0.044, achieved 11 %, saturation code -0.76), and I did not verify whether `unallocated_torque` is computed in normalised or raw units (`ControlAllocator.cpp:~670-686`). The verdict "saturation, not scaling" is therefore strong (89 % of samples have a motor at 0, a 17 Hz limit cycle in all axes, and unsaturated source = 0.707) but the mechanism inside the allocator is not replayed.
3. `ver_sw` 32500e0276 vs `run.json` commit c13b638770 dirty: the binary behind the log may differ from the tree I read (no diff in the relevant source directories against 32500e0276, none checked against the dirty state).
4. 5-inch G1 pitch (Iyy not read) and yaw (G1_Y 30) were not derived.
5. MINIMUM_YAW_MARGIN and the exact line numbers inside `ControlAllocationSequentialDesaturation.cpp` are from my reading of a 260-line file (lines quoted to within a few lines), and `ControlAllocation.cpp` clip line was not opened.
6. In-band 2.5 Hz magnitude (S43 UNVERIFIED 4) is not explained by this; it was measured in the same saturated regime.
