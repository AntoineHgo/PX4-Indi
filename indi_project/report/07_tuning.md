# 7. Tuning methodology and iteration

This chapter shows how the two controllers were tuned, so a reader can judge whether the PID baseline was tuned fairly and how INDI reached its frozen candidate. The headline: after four tuning rounds and three structural firmware fixes, INDI and PID tie on the tuning cost, J = 0.978 for INDI against about 0.96 for PID, a difference inside the noise of the hover term (`results/tuning/r4f.md`; `DECISIONS.md` D-freeze). On the tuning set this is a tie, not a win. Paths are relative to `indi_project/`. Held-out and disturbance results are in later chapters.

Sources are cited in parentheses as paths relative to `indi_project/`. The chapter covers only the tuning set; the held-out and disturbance results are reported in later chapters.

## 7.1 Tuning principles

**Initial values come from the model and identification.** The INDI control effectiveness G1 is identified, not tuned: roll = pitch = 241 from in-loop fits of 237 and 245 (R^2 0.94 to 0.95), yaw 7.4 from fits of 7.2 to 7.6. An open-loop fit on PID logs (321 and 211) was rejected because it disagreed between two axes of a symmetric vehicle (`DECISIONS.md` D-g1-v1). Round 1 started from K_R = 20, K_P = 20, K_Y = 10, actuator time constant 0.02 s, yaw cut-off 10 Hz and attitude P gains 4, 4, 2.8 (`results/tuning/indi/r1/c00/params`), the time constant being near the Gazebo motor constants of 0.0125 s up and 0.025 s down (`results/tuning/indi_r1.md`). The PID baseline starts from the PX4 defaults; the gz_x500 airframe file sets no rate or attitude gains (`results/tuning/pid_r1.md`).

**Same procedure, same budget.** The fairness rule requires the same sweep design, number of evaluations, cost and scenarios for `pid_tuned` and `indi`, with both tuning logs kept (`bench/scenarios.md` sec. 2). One script, `bench/tune.py`, serves both families (`plan/tuning_driver_spec.md`). It draws a Latin hypercube in log space, each parameter in [centre / span, centre x span] clamped to the PX4 limits, candidate 0 being the centre. Each candidate is flown on every scenario and seed through the same runner and metric code as the plain batches, and rounds are resumable (`bench/tune.py` docstring). This is random search, identical for both controllers; its limit is discussed in 7.6.

The spaces differ in size, which is inherent to the controllers. In `bench/tune.py` PID has 12 parameters (roll and pitch rate P, I, D; yaw rate P, I; MC_YAW_TQ_CUTOFF; three attitude P gains) and INDI has 8 (K_R, K_P, K_Y, MC_INDI_ACT_TC, MC_INDI_YAW_CUT, three attitude P gains). Both yaw filters were put in on purpose, because PID already has a 2 Hz yaw torque low-pass (`DECISIONS.md` D-yawfilt, D-indi-r1).

**Tuning versus held-out set.** The tuning set T (T1 to T9) is used for tuning and development; the held-out set H (H1 to H6) is never used for tuning, and each H scenario is a variant of a T mechanism with other parameters so tuning cannot memorise it. H runs are allowed only for the final validation and at most one intermediate check per iteration, which must not drive gain changes (`bench/scenarios.md` sec. 3.2).

**Stage-1 scope.** Scenarios T5 to T9 needed simulator extensions that did not yet exist, so stage-1 tuning used T1 to T4, with a planned re-tune of both controllers on the full T set later (`bench/scenarios.md`, change log v1.1). The five scenarios used are `hover`, `step_roll`, `step_pitch`, `step_yaw` and `rate_step_roll`, with primary metrics position RMS 3D, RMS attitude error of the stepped axis, and roll-rate RMS (`bench/tune.py`). No full-T re-tune appears in the sources; see Inconsistencies.

**Cost J.** Per (scenario, seed): the ratio of the primary metric to the `pid_default` reference flight on the same scenario and seed, plus 0.2 x (effort ratio - 1) when the motor-rate effort ratio exceeds 1.25, plus 10 for a failed run; J is the mean (`bench/scenarios.md` sec. 5; `bench/tune.py`). J = 1 means "same as the PX4 default reference flights", lower is better. The cost was frozen before INDI flew and never changed, since changing it after seeing INDI lose would be after-the-fact selection (`DECISIONS.md` D-yawsp).

**Seeds and speed factor.** Round 1 used 2 seeds, later rounds 3, to average the non-repeatable hover metric (`DECISIONS.md` D-r2). Attitude and rate scenarios run at speed 4 and hover at speed 1: on `pid_default` seeds 1 to 3, step metrics agree between speeds within the seed spread, but hover position RMS does not, 0.027 m (0.021 to 0.033) at speed 1 against 0.064 m (0.038 to 0.104) at speed 4, cause open (`DECISIONS.md` D-speed). **Stopping rule:** several iterations without improvement, with an explanation of the remaining gap (`DECISIONS.md` D-freeze).

## 7.2 PID baseline retuning

The PID baseline was given two sampling rounds with the shared driver, centred on the PX4 defaults.

| Round | Candidates | Seeds | Flights | Span | Best J | PX4 defaults (c00) J | Source |
|---|---|---|---|---|---|---|---|
| r1 | 24 | 2 | 240 | 2 | 0.946 (c00 itself) | 0.946 | `results/tuning/pid_r1.md` |
| r2 | 16 | 3 | 240 | 1.5 | 0.958 (c10) | 0.964 (re-flown) | `results/tuning/r2.md` |

Both rounds had 0 failures (`results/tuning/pid_r1.md`; `results/tuning/r2.md`). Over the two rounds that is 40 candidates (24 + 16, counted from `results/tuning/pid/r1/summary.csv` and `results/tuning/pid/r2/summary.csv`) and 480 flights.

**Round 1.** No sampled candidate beat the defaults in a factor-2 box; the second best, c12, scored 0.978 and the median of 24 was 1.060. Some candidates improved one axis (step_roll down to 0.78) at the expense of others (`results/tuning/pid_r1.md`). The round also exposed the hover problem of 7.4: the reference gains themselves scored a hover ratio of 0.752 instead of about 1.

**Round 2.** The best candidate, c10, scored J = 0.958 against 0.964 for re-flown defaults, a 0.6 % gain inside the roughly 2 % run-to-run noise. Its ratios were hover 0.876, step_roll 0.873, step_pitch 0.945, step_yaw 1.059, rate_step_roll 0.954; the worst candidate scored 1.145. c10 (roll P 0.1681, pitch P 0.122, attitude P 5.142 and 4.509; `results/tuning/pid/r2/c10/params`) gains on roll and pitch but loses on yaw, and was noted for a confirmation re-fly, not adopted (`results/tuning/r2.md`).

**Outcome.** `pid_tuned` is the PX4 default gains (`results/tuning/r2.md`; `DECISIONS.md` D-freeze), with the effort documented as two rounds, 40 candidates, 480 flights. The defaults are at, or within noise of, the optimum of this cost inside the sampled boxes (`results/tuning/r2.md`). Because `pid_tuned` equals `pid_default`, the benchmark effectively compares INDI against PX4 as shipped. This claim is limited by the search design, see 7.6.

## 7.3 INDI tuning rounds r1 to r4f

INDI went through four sampling rounds (r1 to r4) and four single-candidate re-scores after a firmware change (r2f_yc2, r2f_yawnu, r3f_yawsp, r4f). J is the frozen cost over the five tuning scenarios, except for r4, which flew only step_yaw and hover and is ranked by its step_yaw cost. "PID J" is the best or default PID value from the matching round. Cells marked "n/a" are not given in the cited file.

| Round | Candidates x seeds | What was varied | Best INDI J | PID J | Key finding | Source |
|---|---|---|---|---|---|---|
| r1 | 24 x 2 (240 flights) | all 8 parameters, centre K 20/20/10, ACT_TC 0.02, YAW_CUT 10 Hz, span 2 | 1.167 (c07) | 0.946 | INDI tracks better than PID on all five scenarios but pays 0.32 of J in effort | `results/tuning/indi_r1.md` |
| r2 | 16 x 3 (240) | all 8, centre c07 with YAW_CUT 3.5 Hz, span 1.5 | 1.150 (c11) | 0.958 (best), 0.964 (defaults) | effort still 2.3 to 2.6x PID; traced to the yaw path | `results/tuning/r2.md` |
| r2f_yc2 | 1 x 3 (15) | c11 with YAW_CUT 2 Hz (PID's value) | 1.182 | 0.958 to 0.964 | a_f chatter gone, hover effort still ~2.1x: remaining source is the nu term | `results/tuning/r2f_yc2.md` |
| r2f_yawnu | 1 x 3 (15) | same candidate, firmware D-yawnu | 1.197 | 0.958 to 0.964 | hover effort 1.07 to 1.12x, but step_yaw effort 6.65 to 7.79x | `results/tuning/r2f_yawnu.md` |
| r3 | 16 x 3 (240) | all 8, centre K_Y 3.0, YAW_P 4.0, span 1.5 | 1.055 (c13) | 0.958 to 0.964 | step_yaw effort 4.66 to 5.89x, structural (unfiltered setpoint path) | `results/tuning/r3.md` |
| r3f_yawsp | 1 x 3 (15) | c13, firmware D-yawsp | 1.058 | 0.958 to 0.964 | step_yaw effort 1.42x, yaw ratio 0.876 to 1.056; hover outlier 1.306 | `results/tuning/r3f_yawsp.md` |
| r4 | 12 x 3 on 2 scenarios (72) | K_Y, YAW_CUT, YAW_P only, span 2 around c13 | n/a (best step_yaw cost 1.089, c10) | n/a | no yaw candidate beats PID at acceptable effort | `results/tuning/r4.md` |
| r4f | 1 x 3 (15) | c13 roll/pitch + c10 yaw, firmware D-yawsp | 0.978 | 0.958 to 0.964 | tie within hover noise; frozen | `results/tuning/r4f.md` |

Summing the flight counts in the table gives 852 flights (the four 15-flight re-scores included). The decision log states "~600 flights" for r1 to r4 (`DECISIONS.md` D-freeze); the three 240-flight sampling rounds plus r4's 72 flights alone give 792. See Inconsistencies.

### How each surprise was diagnosed before gains changed

The pattern in every step below is the same: INDI scored worse than PID under the frozen cost, the effort term was identified as the reason, the effort was measured per axis on logs, and a structural change was made only when the measurement located a specific cause. Gain sampling alone never closed the gap.

**Hover effort 44x PID, then 6x (sessions 7 to 8).** With the identified G1_Y = 7.4, yaw acceleration noise reaches the yaw torque through 1/G1_Y, four times more than in the earlier v0 setup that used 30. Hover motor-rate effort was 1.616 against 0.037 for PID, about 44x (`results/yawcut_check_s8.md`). The fix was a yaw low-pass inside the INDI law applied identically to the angular-acceleration and torque feedback paths so they stay synchronised (`DECISIONS.md` D-yawfilt). At 10 Hz this cut hover effort to 0.228, about 6x PID (`results/yawcut_check_s8.md`). Inflating G1_Y to hide the noise was rejected because it detunes the cancellation (`DECISIONS.md` D-yawfilt).

**Round 1.** The best INDI candidate had a lower tracking ratio than PID on all five scenarios (yaw step -15 %, roll step -17 %, pitch step -9 %, hover -10 % relative to PID c00) but J = 1.167 against 0.946, about 0.32 of it effort penalty (`results/tuning/indi_r1.md`). The top candidates sat at the low edge of the yaw cut-off box.

**Which axis? (session 9).** Hover torque statistics per axis showed roll and pitch activity about 2x PID's per sample, but yaw torque standard deviation 9x PID's (0.0027 against 0.0003 at 10 Hz). With G1_yaw = 7.4 against 241, each rad/s^2 of yaw acceleration noise becomes 33x more torque (`results/effort_axes_s9.md`). Round 2 therefore widened the yaw cut-off box toward PID's 2 Hz (`DECISIONS.md` D-r2).

**Round 2 did not close the gap.** J improved only 1.5 % (1.167 to 1.150) and effort stayed at 2.3 to 2.6x PID: a noise-transmission problem, not a gain-tuning one (`results/tuning/r2.md`). A matched-filter control (YAW_CUT = 2 Hz) followed.

**Matched filter and the unfiltered rate term (session 11).** The 2 Hz cut removed the a_f chatter (yaw torque sample-to-sample change 0.00018 to 0.00004) but hover effort stayed ~2.1x PID. The term split located the rest in nu = K_Y (r_sp - r) built from the raw gyro rate, with gain K_Y / G1_Y = 5.83 / 7.4 = 0.79, against PID's yaw P of 0.2 behind a 2 Hz output filter (`results/tuning/r2f_yc2.md`). D-yawnu filters that rate with the same cut-off; filtering the whole increment was rejected because it adds lag in series with the actuator and breaks synchronisation (`DECISIONS.md` D-yawnu). Hover effort became 0.041 to 0.043 against 0.037 for PID (`results/yawnu_check_s11.md`).

**Hover fixed, J unchanged (r2f_yawnu).** Hover effort fell to 1.07 to 1.12x, under the 1.25 threshold, but J rose to 1.197. The remaining penalty was almost entirely step_yaw transient effort at 6.65 to 7.79x PID, worth about 0.24 of J, while yaw tracking was only about 10 % better than PID (`results/tuning/r2f_yawnu.md`). The file labels the cause, an unfiltered setpoint step, as "probable, not yet verified".

**Verified before acting (round 3).** `bench/yaw_step_effort.py` on step_yaw seed 1 showed the setpoint term K_Y r_sp / G1_Y peaking at 2.75 normalised torque, saturating the yaw torque at 1.0 against 0.33 for PID; motor-rate RMS along yaw was 11.1 against 1.55. The yaw loop crossover was near K_Y = 5.8 rad/s against about 1.5 for PID (0.2 x 7.4), so INDI had been tuned about 4x faster in yaw (`DECISIONS.md` D-r3). Round 3 was centred at K_Y 3.0 and YAW_P 4.0, a region never sampled while hover effort dominated the cost, and J improved from 1.197 to 1.055. The yaw torque no longer saturated (peak 0.78) but still jumped at the setpoint step, which PID's 2 Hz output filter smooths; no gain in the box removed it (`results/tuning/r3.md`).

**Structural fix D-yawsp, and its price.** YAW_CUT now filters the yaw rate error including the setpoint, which gives INDI the same structure that PID already has by default (`DECISIONS.md` D-yawsp). A separate setpoint pre-filter was rejected as an INDI-only advantage, and changing the effort metric was rejected as after-the-fact selection (`DECISIONS.md` D-yawsp). Result: step_yaw effort fell from 4.66 to 5.89x to 1.42x, and yaw tracking ratio rose from 0.876 to 1.056 (`results/tuning/r3f_yawsp.md`). INDI paid the same lag PID pays.

**Round 4: the yaw frontier.** With D-yawsp no candidate beat PID on step_yaw at acceptable effort: a ratio of 0.98 needed 3.8x effort (c11), and at no more than 1.25x effort the best ratio was 1.05 to 1.09. The yaw loop is now a P-type rate loop behind a 1.5 to 2 Hz filter, as in PID, so near-parity is expected, and the weak yaw authority (G1_Y = 7.4) leaves little for inversion to gain (`results/tuning/r4.md`). The selection rule was fixed before the results; c10 won it and was combined with the c13 roll and pitch gains (`DECISIONS.md` D-r4). Fairness consequence: INDI received more rounds and structural changes than PID, because PID needed none.

## 7.4 The hover-noise problem and how it limits J

Hover position RMS is not repeatable per seed. The same `pid_default` hover flights re-flown with seeds 1 to 3 gave 0.036, 0.037 and 0.046 m against the reference 0.033, 0.027 and 0.021 m, ratios 1.08, 1.38 and 2.19 (`results/tuning/pid_r1.md`). Step and rate metrics re-fly within about 2 % (`DECISIONS.md` D-hover-noise). The likely source is thread scheduling between PX4 and Gazebo in lockstep, which the seed does not control; this is a hypothesis, not a measurement (`DECISIONS.md` D-hover-noise).

Consequences for the tuning cost:

- The hover ratio of the reference's own gains is biased below 1: PID c00 scored 0.752 in r1 and 0.856 in r2 (`results/tuning/pid_r1.md`; `results/tuning/r2.md`). This is why J below 1 must not be read as "better than PX4 defaults", and why PID's own J is 0.946 to 0.964 and not 1.
- Identical parameters and seeds gave very different hover ratios in different rounds. INDI c13 scored 0.740 in r3 (earlier firmware), 1.306 in r3f_yawsp (one run at 0.067 m with other seeds at 0.017 and 0.026 m) and 0.767 in r4, the last two with the same firmware (`results/tuning/r3.md`; `results/tuning/r3f_yawsp.md`; `results/tuning/r4.md`). Similarly the c10 yaw set scored 0.782 in r4 and the same parameters 0.945 in r4f (`results/tuning/r4.md`; `results/tuning/r4f.md`).
- The 3-D hover RMS is driven by sporadic vertical excursions that occur for PID too. The horizontal RMS, the part attitude control acts on, is tight and equal: median 0.0204 m (max 0.0253) for the 48 PID r2 candidates and 0.0194 m (max 0.0242) for the 48 INDI r3 candidates; vertical medians are 0.0075 m and 0.0072 m but the maxima reach 0.0699 m and 0.0410 m (`results/tuning/r3f_yawsp.md`). The cause of the excursions is open.
- With 3 seeds, one such run moves the hover ratio by about 0.5 and J by about 0.1 (`results/tuning/r3f_yawsp.md`). The tuning rule that follows: J differences below about 0.1 are not meaningful (`DECISIONS.md` D-hovernoise). The tie of INDI at 0.978 with PID at about 0.96 is a 0.02 gap, well under that threshold.

The remedy chosen was to average hover over more seeds (3 in tuning, at least 8 in the final benchmark) and to report the horizontal and vertical split next to the frozen metric (`DECISIONS.md` D-hover-noise, D-hovernoise). The frozen cost was left unchanged.

## 7.5 Frozen candidates and per-scenario ratios

**PID tuned** is the PX4 default set (`results/tuning/pid/r2/c00/params`): roll and pitch rate P 0.15, I 0.2, D 0.003; yaw rate P 0.2, I 0.1; MC_YAW_TQ_CUTOFF 2 Hz; attitude P 4, 4 and 2.8 for roll, pitch and yaw.

**INDI tuned** is `results/tuning/indi/r4f/c00/params`, frozen by D-freeze (`DECISIONS.md`):

| Parameter | Value | Origin |
|---|---|---|
| MC_RATE_CTL_TYPE | 1 | selects INDI |
| MC_INDI_G1_R, MC_INDI_G1_P | 241, 241 | identified, not tuned |
| MC_INDI_G1_Y | 7.4 | identified, not tuned |
| MC_INDI_K_R | 23.89 | r3 c13 |
| MC_INDI_K_P | 12.29 | r3 c13 |
| MC_INDI_K_Y | 2.118 | r4 c10 |
| MC_INDI_ACT_TC | 0.01142 s | r3 c13 |
| MC_INDI_YAW_CUT | 1.572 Hz | r4 c10 |
| MC_ROLL_P, MC_PITCH_P | 6.275, 6.185 | r3 c13 |
| MC_YAW_P | 3.308 | r4 c10 |

(Parameter values: `results/tuning/indi/r4f/c00/params`; origin: `results/tuning/r3.md`, `results/tuning/r4.md`, `results/tuning/r4f.md`.) The firmware is the D-yawsp build, commit 99634a6b71 (`results/tuning/r4f.md`).

**Ratios to PID defaults on the tuning set**, mean over seeds 1 to 3, lower is better (`results/tuning/r4f.md`):

| | J | hover | step_roll | step_pitch | step_yaw | rate_step_roll |
|---|---|---|---|---|---|---|
| PID defaults (r2) | 0.958 to 0.964 | 1 | 1 | 1 | 1 | 1 |
| INDI r4f | 0.978 | 0.945 | 0.878 | 0.935 | 1.096 | 1.021 |
| INDI motor-rate effort ratio | | 0.99-1.03 | 1.16-1.26 | 0.63-0.71 | 1.11-1.15 | 0.67 |

The reading is: INDI tracks roll steps 12 % and pitch steps 7 % better (pitch with about 30 % less effort), equals PID on rate pulses (+2 %, with 33 % less effort) and on hover, and is 10 % worse on yaw steps, a structural consequence (`results/tuning/r4f.md`; `results/tuning/r4.md`). The hover ratio of 0.945 is not a meaningful advantage given 7.4. The PID row is the reference itself, so its 1.0 entries are by construction; its J of about 0.96 is below 1 only because of the hover reference noise (7.4). Per-scenario ratios on the held-out and disturbance scenarios are outside the sources of this chapter and are not quoted here.

## 7.6 Threats to validity

- **Noise.** Hover is non-repeatable (7.4), and J differences under about 0.1 are not meaningful (`DECISIONS.md` D-hovernoise). The tie, 0.978 against about 0.96, cannot rank the controllers either way. Step and rate metrics are more stable, about 2 % re-fly noise (`results/tuning/r2.md`).
- **Few seeds.** Tuning used 2 seeds in round 1 and 3 afterwards, and the final re-score r4f used 3. Candidate differences of a few percent per scenario are within that noise. The benchmark's statistical test (10 seeds, paired Wilcoxon) applies only to the final validation (`bench/scenarios.md` sec. 6), not to tuning.
- **Tuning on five scenarios only.** The frozen parameters were optimised for hover, three attitude steps and one rate pulse series. Gust, payload, motor-loss, trajectory and mismatch scenarios (T5 to T9) played no role in tuning in the documented rounds, and the held-out scenarios were not used. This is safe against leakage but means the candidates may be suboptimal where INDI is expected to differ from PID, namely disturbance rejection and plant change (`bench/scenarios.md` sec. 1).
- **Random search, small budget.** The PID search was 24 candidates in a 12-dimensional box and 16 in a narrower one. "No candidate beat the defaults" supports "the defaults are hard to beat by random sampling", not "the defaults are the optimum". A per-axis or gradient-based search might find a better PID, and PID candidate c10 improved roll and pitch steps by 13 % and 5.5 % at a cost on yaw (`results/tuning/r2.md`). The same limit applies to INDI.
- **Unequal effort.** PID got two rounds and 480 flights; INDI got four rounds, three structural fixes and 852 flights. The fairness rule asks for equal budgets (`bench/scenarios.md` sec. 2); PID stopped early because defaults won, but a reader may still view this as an asymmetry in INDI's favour. 
- **The cost is relative to the default reference.** J is a ratio to `pid_default` flights, so the PID default is advantaged by construction on J = 1, and the effort penalty only charges noise above 1.25x. The cost function was frozen before INDI flew and never changed.
- **Structural changes were made on the tuning set and affect INDI only.** D-yawfilt, D-yawnu and D-yawsp were motivated by effort measured on tuning scenarios. They were justified as giving INDI the same filtering structure PID already has, but the PID baseline did not get an equivalent search over its own structure (for example its D-term filtering).
- **Simulator limits.** Hover non-determinism of unknown origin, and a speed factor of 4 validated only on `pid_default` seeds 1 to 3 (`DECISIONS.md` D-speed).

## Inconsistencies and unverified claims

1. **PID candidate count.** `DECISIONS.md` D-freeze and `results/tuning/r2.md` say "64 candidates over two rounds". The same `results/tuning/r2.md` says "40 sampled PID candidates" for r1 plus r2, and the summary files hold 24 + 16 = 40 rows (`results/tuning/pid/r1/summary.csv`, `results/tuning/pid/r2/summary.csv`). This chapter uses 40. The 480 flights quoted in both files agree with 40 candidates.
2. **INDI flight count.** D-freeze says "~600 flights" for r1 to r4 (`DECISIONS.md`); the per-round counts in the result files give 792 for the four rounds and 852 with the four re-scores.
3. **PID default hover effort.** `results/yawcut_check_s8.md` gives 0.037 1/s for `pid_default` hover (seed 1), and `results/effort_axes_s9.md` gives 0.054 for the same scenario and seed. The "44x" and "6x PID" ratios of 7.3 use 0.037; with 0.054 they would be about 30x and 4x.
4. **PID J.** The PID value is quoted as 0.96 (`DECISIONS.md` D-freeze), 0.946 (r1, `results/tuning/pid_r1.md`), 0.958 for the best and 0.964 for re-flown defaults (r2, `results/tuning/r2.md`), and "0.958 to 0.964" (`results/tuning/r4f.md`). The differences come from hover noise, not from different parameters.
5. **Same parameters, different J.** INDI c13 hover 0.740, 1.306, 0.767 and c10 hover 0.782 against 0.945 (7.4). These are same-parameter re-flights and are reported as noise by the source files, not corrected.
6. **Tuning space size.** `plan/tuning_driver_spec.md` lists 11 PID and 7 INDI dimensions; `bench/tune.py` has 12 and 8 because MC_YAW_TQ_CUTOFF and MC_INDI_YAW_CUT were added (`DECISIONS.md` D-yawfilt).
7. **Planned re-tune on the full T set.** `bench/scenarios.md` (v1.1) says both controllers are re-tuned on the full T set once T5 to T9 exist. No such round appears in the sources read; D-freeze moves directly to the held-out scenarios. Whether a re-tune was done is unverified.
8. **Unverified causal claims in the sources.** The scheduling explanation of hover non-determinism, the cause of vertical hover excursions, and the explanation of the c07 and c08 yaw behaviour in `results/tuning/r4.md` ("probably a lag-limited yaw oscillation, not checked") are hypotheses, not measurements.
