# Report consistency audit (partial, incremental)

## Item 1 - stale code descriptions
- 01_introduction.md:32 "selected at arming by the parameter `MC_RATE_CTL_TYPE`, and the PID path is the default" -- MC_RATE_CTL_TYPE has 0 hits in src/. Final tree uses separate module mc_indi_rate_control (MC_INDI_EN in McIndiRateControl.cpp / yaml). Stale.
- 01_introduction.md:21 "The attitude and position loops are the standard PX4 controllers in both configurations" -- stale after stage 8 (mc_indi_pos_control exists).
- 01_introduction.md:33 "integrated in the multicopter rate-control module" -- stale; module is src/modules/mc_indi_rate_control.

## Item 2 - drafting artefacts
- 05_design_implementation.md:300 "## 5.8 Discrepancies found"; :313 "Unverified: the 18-test count ... not re-run for this chapter"
- 07_tuning.md:210 "## Inconsistencies and unverified claims"; :17 "see Inconsistencies"; :55 "See Inconsistencies"; :219 item 8 "Unverified causal claims"
- 08_results.md:27 "inline script that is not yet in bench/ ... TODO in that file"; :225 "(inline script, session 15)"; :241 "inline script ... had not been made" (to-do)
- 10_conclusion.md:67 "The outer-loop (linear acceleration) INDI of stage 8 had not been evaluated when this section was written."  (stale: stage 8 was evaluated; check)
- 11_appendix_reproduce.md:90, :109 "inline scripts that are not yet in bench/"
- 09_discussion.md:71 "Reproducibility gaps ... inline scripts not yet in bench/"
- 04_px4_architecture.md:50 "A TODO states that the unallocated value itself should be used (:223)" (refers to upstream PX4 code, verify)
- 02_state_of_the_art.md:83 "with a TODO for the missing excitation check" (refers to paparazzi; ok but check context)
- No "[TO VERIFY]" or "[GAP]" markers found (grep -i verify/gap/tbd/todo/fixme).

## Item 1 (continued) - chapter 04/05 stale claims (verified in tree)
- Final tree: MC_RATE_CTL_TYPE absent (0 hits in src/). MC_INDI_EN in src/modules/mc_indi_rate_control/mc_indi_rate_control_params.yaml:5. mc_rate_control has no INDI code (only stock refs; grep indi -> 0 in mc_rate_control/Kconfig and params yaml).
- 04_px4_architecture.md:3 "the working branch has INDI additions that shift lines" in MulticopterRateControl.cpp -- stale (INDI now in own module; mc_rate_control diff vs main: see below).
- 05_design_implementation.md:11 "MC_RATE_CTL_TYPE defaults to 0 (PID)" -- stale name.
- 05_design_implementation.md:130 "one enum parameter MC_RATE_CTL_TYPE ... latched while disarmed" and :211 "While disarmed ... latches _use_indi = (MC_RATE_CTL_TYPE == 1)" -- stale; superseded at :134 but :128-130 and :209-216 still stated as current (section 5.5.2 is titled as runtime description, not marked historical).
- 05_design_implementation.md:203-205 files table: src/modules/mc_rate_control/MulticopterRateControl.{hpp,cpp}, mc_rate_control_params.yaml, msg IndiRateStatus -- stale; real module src/modules/mc_indi_rate_control/{McIndiRateControl,IndiMeasuredTorque}.
- 05_design_implementation.md:226 param table: MC_RATE_CTL_TYPE row "latched while disarmed" -- stale; table omits MC_INDI_EN, MC_INDI_W_MAX, MC_INDI_ERPM_DLY, MC_INDI_ERPM_TO, MC_INDI_ACT_BLD (all in final yaml).
- 05_design_implementation.md:259 "published by mc_rate_control only while INDI is selected" -- stale.
- 05_design_implementation.md:138 "Gazebo's esc_status.esc_rpm only echoes the command ... Rejected: ESC feedback" -- contradicted by final code: McIndiRateControl.cpp:141-158 subscribes esc_status and builds actuator_torque_measured (stage 2 v2). Chapter 05 never documents this path.
- 05_design_implementation.md:298 "Single airframe, single loop rate. The parameters were identified at 250 Hz" -- IMU rate used by v2/v3 benches is 1000 Hz (scenarios.md section 8 line 148/209; run_scenario.py:390 default 250, --imu-rate 1000 for v2). Gyro publication (loop rate) is 400 Hz (IMU_GYRO_RATEMAX default, no bench override; imu_gyro_parameters.yaml:63).
- 05_design_implementation.md:86 "in the Gazebo x500 both are 250 Hz" -- stale for v2/v3 (1000 Hz IMU).
- 05_design_implementation.md:400, :427 "125 Hz loop" for outer loop -- check against stage-8 run (not verified).
- 05_design_implementation.md:6-7 "Outer-loop INDI is stage 2" vs stage 8 elsewhere: stage numbering conflict (5.1 line 7 says stage 2 = outer loop; 5.3.2 line 134 says stage 2 = separate module; 5.9 says stage 8 is outer loop).
- 05_design_implementation.md:146-ish "MC_INDI_ACT_TC default 0.02" OK vs yaml default 0.02 (yaml:107) -- consistent.
- 05_design_implementation.md:226-236 defaults for G1_R 320, G1_P 210, G1_Y 30, K 20/20/10, DT_MAX 1.0, YAW_CUT 0, DELAY 0 match yaml. OK.
- 05_design_implementation.md:231 K_R/K_P/K_Y default "20, 20, 10" match yaml (74,85,96). OK.
- 05_design_implementation.md:237 says tuned "later in-loop values (241, 241, 7.4)"; frozen indi_v3.params sets G1_R=174, G1_P=174, G1_Y=12.2 (bench/params/indi_v3.params). Numeric conflict (05:114,227 vs params).
- 05_design_implementation.md:232 ACT_TC range 0.001-0.2 and ERPM etc. -- ok.
- 05_design_implementation.md:274 "18 gtests" -- tree has 40 TEST cases in src/lib/indi_rate_control/indi_rate_control_test.cpp (grep '^TEST' = 40). 05:313 says "not re-run". IndiAccelControlTest: 19 (matches 5.9.6).
- 05_design_implementation.md:298 also "Single loop rate" conflicts with 04:60/112 "400 Hz".
- 05 has NO control-law section for the measured-torque (omega^2 / actuator_torque_measured) path or MC_INDI_ACT_BLD blend; only the v1 law (5.2) and outer loop (5.9). (grep ACT_BLD/omega^2/blend in ch05: 0 hits except :134 revision note.)
- 05_design_implementation.md:103 yaw G2 default 0 -- yaml default 0 OK.

## Item 4 - 08_results.md section 8.10 (lines 391-463) vs scenarios.md sec. 9 (line 175+), scenarios.py:162-168, results/vprime.md
Spec (scenarios.md sec.9 table) -> chapter (08:394-395, 403-409) -> vprime.md:
- W1 vp_loss1_06: spec motor 1 at 0.6, T8 pattern, metric roll+pitch attitude RMS "as T8". Chapter: same motor/scale OK, but 08:400-401 says W1/W2 judged on TILT RMS "as no attitude setpoint pattern is flown there (D-vprime-metric)". Spec sec.9 has no such amendment -> metric differs from frozen spec. vprime.md:9 agrees with chapter (tilt), so it is a spec deviation not recorded in sec.9.
- W2 vp_loss2_08: motor 2 at 0.8, T8. Chapter OK (table row 406, 0.95, 10/10, p 0.002). Consistent with vprime.md:14.
- W3 (spec): motors 0 AND 3 at 0.85 each, H5 att step, fault "up", roll RMS. Chapter 08:394-395 calls W3 "actuator time constant x2 with motor 2 at 0.8 on attitude steps" -> that is spec W5 (vp_tau2_loss2_att). MISMATCH. Chapter row 407 (ratio 0.99, 8/10, p 0.049, effort 1.17, v2 1.93) = vprime.md:18 which is vp_tau2_loss2_att. So W3 label carries the W5 data.
- W4 vp_sag75_att: 75 % sag. Chapter OK. Row 408 numbers match vprime.md:19 (0.96, 2/3, 0.75, 1.00). Note chapter says "(4 runs)" for both PID and INDI and "2/3" paired: vprime.md shows fails 6/6 so 4 complete runs per controller, but 2/3 paired wins — chapter labels "2/3" yet cites 4 runs; minor inconsistency to confirm.
- W5 (spec): motor time constants x2 (V1 hook) + motor 2 at 0.8 from "up". Chapter 08:395 calls W5 "eRPM gain error 0.3 on attitude steps" -> CONFIRMED WRONG: no eRPM-gain entry exists in scenarios.md sec.9 or scenarios.py (grep vp_ shows only tau2 + motor2 for W5; eRPM gain not in any vp entry). Chapter row 409 (ratio 1.01, 6/10, p 0.85, effort 1.16, v2 2.71) = vprime.md:17 which is vp_gain03_att = spec W3 (motors 0,3 at 0.85). MISMATCH.
- Conclusion: W3 and W5 are swapped in both label and data rows (user suspicion confirmed); "eRPM gain error 0.3" refuted (it is the description of nothing in the spec; the spec entry is motors 0+3 at 0.85 for W3).
- Chapter 08:396-397 "5 entries x 10 seeds x four controllers ... 200 flights" consistent with vprime.md:3-4; spec sec.9 says speed 4 for attitude patterns and 1 for T8 — chapter silent (not wrong).
- Chapter 08:411-412 watchdog counts (W1 10/10 all, W4 PID default 7, tuned 6, v2 3, v3 6) match vprime.md:50-ish lines exactly.
- Chapter 08:414-416 verdict: criteria 1,2,4 fail; criterion 3 met — matches vprime.md:37-39 but vprime says "Complete entries (10 paired seeds): 3/5": chapter says "5 entries" flown, W1 (no data) not complete for compare — chapter 8.10 table gives W1 "10/10 fail", fine.
- Chapter 08:416 "hover effort 2.14x" matches vprime.md:33 (5 seeds). Chapter 08:437 & 8.11 "2.02x on 10 seeds" -> different quantity; see item 5.
- Spec sec.9 also lists criteria "4. hover effort at most 1.5x" OK.
- Chapter 08:403 header "effort ratio" column value W2 0.78 matches vprime.md:14 (0.78).

## Item 1 - chapters 06, 09, 10, 11 stale claims
- 06_simulation.md:41 "Rotor speed feedback: none measured; esc_rpm echoes the command"; :54 "gz provides no rotor-speed feedback" -- stale: src/modules/simulation/gz_bridge/GZMixingInterfaceESC.hpp:116 SIM_GZ_ESC_FB (0 echo, 1 joint velocity, 2 eRPM model); run_scenario.py:431 sets it for v2.
- 06_simulation.md:42 "IMU rate 250 Hz" -- section 8 and V' use --imu-rate 1000 (scenarios.md:148, :209).
- 09_discussion.md:35 "Measured rotor speed ... cannot be tested in the present simulator"; :57 "esc_rpm echoes the command, so INDI uses an onboard model" -- stale.
- 09_discussion.md:81 item 5 "MC_RATE_CTL_TYPE is latched while disarmed" -- stale.
- 09_discussion.md:69(e) "controller selection is latched while disarmed" -- stale.
- 09_discussion.md:82 item 6 "Only the rate loop is incremental ... An INDI outer loop is not implemented and not evaluated" -- contradicted by 05:315-493 and 08:466-510.
- 10_conclusion.md:67 "outer-loop INDI of stage 8 had not been evaluated when this section was written" -- drafting artefact; contradicted by 10.6 (:69-84).
- 01_introduction.md:21 and :24 scope: "Only the inner rate loop is replaced ... comparison is against the PX4 PID rate controller" -- stale after stage 8.
- 01_introduction.md:30-35 contributions list only stage-1 work (no stage 2 module, measured torque, v3 blend, stage 8).
- 11_appendix_reproduce.md:36 "--controller is pid_default or indi_tuned" -- stale; run_scenario.py:381 has no choices. 11:57-64 "There is no indi_tuned.params ... Run indi_tuned" -- stale names; bench/params holds indi_v3.params, indi_pos_v3.params.
- 09_discussion.md:55 "G1 identified at a loop rate of 250 Hz" -- stage-1 only.

## Item 2 - drafting artefacts (grep: TO VERIFY, GAP, TODO, Unverified, not re-run, inline script, had not been evaluated, Inconsistencies, Discrepancies)
- 05_design_implementation.md:300 "## 5.8 Discrepancies found"; :313 "Unverified: ... not re-run for this chapter"; :459 "TEST_F count ... the tests were not run for this chapter"
- 07_tuning.md:17, :55 "see/See Inconsistencies"; :210 "## Inconsistencies and unverified claims"; :219 item 8 "Unverified causal claims"
- 08_results.md:27 "inline script ... TODO in that file"; :225 "inline script, session 15"; :241 "inline script ... had not been moved into bench/ ... to-do ... had not been made"
- 09_discussion.md:71 "Reproducibility gaps ... inline scripts not yet in bench/"; 11_appendix_reproduce.md:90, :109 inline scripts
- 10_conclusion.md:67 "had not been evaluated when this section was written"
- 04_px4_architecture.md:50 "A TODO states..." and 02_state_of_the_art.md:83 "a TODO for the missing excitation check" refer to upstream/Paparazzi code; acceptable only if so labelled.
- No literal "[TO VERIFY]" or "[GAP]" found.

## Item 3 - completeness of final-controller description
- Missing in ch05: control law for the measured-torque path (tau_meas = B(u_meas - u_trim), omega^2 thrust model, MC_INDI_W_MAX, MC_INDI_ERPM_DLY, MC_INDI_ERPM_TO). Only a revision note (05:134); 5.3.3 still says ESC feedback rejected (05:138-142).
- Missing: complementary blend MC_INDI_ACT_BLD law. Zero hits for ACT_BLD in ch05 (descriptive mentions only in 07:178, 08:373-374, 08:420, 10:50-52).
- Missing: final frozen parameter table. 05:224-235 is the v1 table (MC_RATE_CTL_TYPE, G1 320/210/30); 07:100-109 is the stage-1 r4f table (G1 241/7.4, ACT_TC 0.01142); bench/params/indi_v3.params (G1 174/174/12.2, K_R 28.77, K_P 16.76, K_Y 2.733, ACT_TC 0.0125, ACT_BLD 0.3, YAW_CUT 3.0, ROLL_P 5.122, PITCH_P 5.797, YAW_P 3.238, THR_MDL_FAC 0.683, CA_R_W_MAX 1000) appears nowhere in the report. Only the INDI POS table exists (05:445-453).
- Block diagram: none for INDI (04:9-28 is the stock PX4 data flow).
- Figures: 9 PNGs in report/figures; 9 embeds in 08/09 (8.1-8.8, 9.1). All stage 1 only (indi_tuned r4f vs PID; act_tc sweep s17). None for stage 2 (v2/v3) or stage 8 (INDI POS, set O). figures/README.md says "INDI tuned = red".
- Stage-8 control law is complete (05:331-400).

## Item 5 - numbers differing between chapters
- Hover effort stage 1: 1.04 (08:39, 08:144, 10:15): consistent.
- Hover effort stage 2 (indi_v3): 2.14x (08:416, 5 seeds; 07:199) vs "about 2x" (08:434; 10:55) vs "about 1.7 times" for the inner loop alone (05:439) vs 2.02x for stage 8 total (10:76; 08:489; 09:100). 05:489 "about 2.7 times" on two seeds at freeze.
- Tuned PID hover range: 0.022-0.063 (08:457) vs 0.022-0.066 (10:59).
- Yaw step ratio: 1.096 (08:173; 09:42) vs 1.089 for the frozen c10 (08:173; 07:52; 09:49).
- H3: attitude ratio 0.16 (08:47; 10:13; 09:7) vs "H3, roll 0.13x" (09:9).
- Flight counts: PID 480 (07:38; 09:63-65); INDI 852 (07:129) vs 792 (09:65) vs "~600" (07:55).
- Unit tests of indi_rate_control: 18 (05:274, 05:313) vs 14 (05:274) vs 19 (09:69). Tree: 40 TEST cases in src/lib/indi_rate_control/indi_rate_control_test.cpp. indi_accel: 19 (05:459) matches tree.
- Loop/IMU rate: 250 Hz (05:86, 05:298, 06:42, 09:55, 09:57) vs 1000 Hz IMU for v2/v3 (scenarios.md:148,209; run_scenario.py:390 default 250) and 400 Hz gyro publication (04:60, 04:112; imu_gyro_parameters.yaml:63, no bench override). 05:400/427 "125 Hz loop" not verified.
- G1 and ACT_TC: 241/241/7.4 and 0.0114 (07:101-106, 09:29, 09:44) vs 320/210/30 and 0.02 defaults (05:227-232) vs 174/174/12.2 and 0.0125 in indi_v3.params (05:140 and 06:39 use 0.0125 as plant value, not the controller value).
- K_R: 23.9 (09:23; 07:103) vs 28.77 in indi_v3.params.
- Best PID wording: 08:14 "no retuned PID candidate beat the defaults" vs "best 0.958 against 0.964" (08:14, 07:36, 09:63).
- W4 counts: 08:408 "3.10 (4 runs)" and "2/3" paired vs vprime.md:19 (6 failures of 10 per controller = 4 completes) -- unexplained paired count.
- Stage 8 O6: 10:72-74 "on every one of 10 seeds" vs 08:489-ish table (8.11) row O6 8/10 seeds (p 0.010).
- 09:94-96 "without the disturbance ... 4 % (O6)": O6 is the mass x1.15 entry, not the undisturbed reference of O5.

## Item 6 - bibliography
- All keys cited in chapters 02-05 (acquatella2017, smeur2016, smeur2018, tal2021, wang2019, blaha2024, steffensen2023, impl_paparazzi, impl_px4_prior, review_s16) exist in 12_bibliography.md.
- All except review_s16 exist in research/sources.md (review_s16 is internal; expected).
- Error: 05_design_implementation.md:311 says wang2019 "is not in research/sources.md": FALSE, research/sources.md:15 lists it.
- 12_bibliography.md:13 tal2021 venue "not confirmed in text" -- flagged as unverified by the chapter itself.
