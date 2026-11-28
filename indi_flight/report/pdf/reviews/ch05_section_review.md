# Review of chapter 5 (chapters/05_analysis.tex, 311 lines): section review, level 7a/7b

Reviewer: agent that did not write the chapter. Read-only review. Sources read: g2_margins.md, GATES.md (G2 section, freeze-10 verdict),
results/freeze10_s193/G2_SCORES.md, results/stage5_s91_attbreak/model_vs_measured.md, bench/margins_models.py, design/t195_att_outer_key.md,
design/attitude_break_s86.md, results/freeze10_s193/g2s/roll800_fwdef_s2/margins.txt, FIGURES.md, figures/g2_margins.pdf (rendered), ch03 Bode figure.

## Settled source disagreements (NOTES_F)

1. Lowest controller rate: 267 Hz (266.7) is right. GATES.md G2 "Configurations" defines the reported rate as 267 Hz, the nearest integer divisor of
   the 800 Hz IMU rate to the mission's 250 Hz; a true 250 Hz flight was rejected by the runner. The freeze-10 verdict line "250 Hz not measured" is a
   loose reference to the mission rate. The chapter text (line 90) is right; the figure caption (line 235, copied from FIGURES.md) says 250 Hz and must
   be changed to "The reported 267 Hz controller rate was not measured on the final configuration." See R1.
2. Vertical cells without gain margin: 7 of 8 is right for the primary scorer (G2_SCORES.md: pt0 D 4 of 4 "n/a"; pt1 D 3 of 4 "n/a", only the 800 Hz
   seed-2 cell has 22.4 dB). The ch02 "4 of 8" is an older (pre-final) count, to be corrected in ch02. Caveat for the chapter: one of the 7 (400 Hz seed 2,
   pt1 D) has a gain margin of 16.3 dB in the second key, and the four pt0 D cells have a plateau GM of about 28 dB in the second key. See R6.
3. The re-fly values (PM 56.9, GM 13.9, DM 485) match GATES.md freeze-10 verdict ("re-fly PM 56.9, GM 13.9, holes PASS"). Correct choice.

## Verified without finding

- Table an_outer, every range, recomputed from G2_SCORES.md (with the re-fly for the E, pt1 row): GM, PM and DM ranges for all six rows; "one cell blocked" (N, pt1),
  "two cells blocked" (D, pt1), "one cell re-flown" (E, pt1), "22.4 in one cell".
- 24 cells = 3 axes x 2 break points x 2 rates x 2 seeds. Min PM 49.1 (+4.1 over 45), min horizontal GM 13.5, min plateau GM 12.88 (12.9), min DM 229 ms.
- Three blocked cells and their numbers (71.3/67.8 with dPM -3.48; 58.7/58.2 with key 2 GM 16.3; 22.4/17.8 with dGM -4.6); thresholds 3 deg and 1 dB; both keys above limits.
- Spot cells: rate roll 800 Hz PM 46.9, GM 15.7, DM 75.5; attitude pitch 400 Hz PM 48.0, GM 13.7 at 4.29 Hz, DM 93.5; reserves +1.9 and +3.0 deg.
  Crossing at 0.237 Hz with |L| = 7.3 gives 20 log10(7.3) = 17.3 dB; signed minimum -17.31 dB. Correct control reading (conditionally stable loop, gain-reduction margin).
- Bode numbers against margins.txt: fc 1.724 Hz, phase at fc about -133.4 (interpolated; 180-46.9 = 133.1), phase crossing 18.29 Hz at -15.68 dB, 18 bins, DM 75.51 ms.
  DM = PM/(360 fc) with PM in deg and fc in Hz gives seconds; 46.9/(360 x 1.724) = 75.6 ms. Equation (an_dm) is correct.
- Margin definitions (PM, GM sign and units), reading rules 1 and 2 (GATES.md Q13 A text).
- Method: break points and bands (rate 1 to 60 Hz, attitude 0.2 to 20 Hz, outer 0.2 to 8 Hz), Schroeder multisine, 10 bins/decade, NP >= 3 first discarded,
  amplitude test 1 dB / 5 deg, period-exact FFT with least-squares fallback, coherence 0.8 / 0.9, "above about 3 Hz", serial flights, u = c + d.
- Model comparison: rate loop (23.6 vs 22.3 deg, 4.7 vs 4.1 dB, -9.7 vs -8.4, 0.2 to 1.7 dB, +17 deg at 1 Hz to -5 deg at 8 Hz, 1.1 deg); table an_att model and
  measured values and both deltas (measured minus model); "within 0.3 deg"; "1.6 to 4.6 dB"; "about 15 deg" without outer loops; p = 8; one-sample latency;
  pitch identical to roll in the model; yaw not modelled; three-bin check 0.60/0.29/0.14 vs 0.69/0.27/0.16, unkeyed; identity to 1e-9 (the model test checks it at 267, 400, 800 Hz).
- The identity (an_ident) is algebraically consistent with L_att = A N/(1+L_rate): (1+L_rate)(1+L_att) = 1 + L_rate + A N.
- O(s) structure follows t195 (derivation re-done: a = g phi, v = a/s, p = v/s gives N = (Kv+Ki/s)(Kp+s)/s^2 + Kd F with F a 5 Hz first-order low-pass). Combining as L_att O is right for a break at the
  rate setpoint with the outer loop closed (L_att(1+N)).
- Verdict items: 24/24, 9/9 steps with both keys, four evidence limits (match freeze-10 verdict).
- Figure an_margins renders as described: three panels, filled 400 Hz / open 800 Hz, dashed thresholds, "no crossing" labels for D rows.
- Notation: T_s, f_c, tau_a, K_p/K_v defined consistently with ch03 for tau_a and T_s (but see R4 for K_p, K_v).

## Findings

### R1 (MAJOR), line 235 (figure caption)
Problem: caption says "The 250 Hz controller rate was not measured", while line 90 says the lowest rate is about 267 Hz. Internal contradiction; 250 Hz is not a configuration in the evidence.
Source: GATES.md G2 Configurations: "267 Hz (reported; nearest integer divisor of the 800 Hz IMU to the mission's 250 Hz)"; no 267 Hz cell is flown on the final configuration (G2_SCORES.md lists 800 and 400 Hz only).
Fix: "The reported 267 Hz controller rate was not flown on the final configuration." Same change in line 309 of the verdict ("The 267 Hz rate was not measured on the final configuration") and in FIGURES.md.

### R2 (MAJOR), line 127 and 129 (also 120 context)
Problem: the subscript M3a is an internal measurement-point id (development trail).
Source: model_vs_measured.md uses L_M3a(att_p).
Fix: name by function, e.g. L_tq ("loop broken at the torque setpoint"), and rename in eq. (an_ident) and line 129.

### R3 (MAJOR), line 119, equation (an_att)
Problem: A_att = p z^-1 ts z/(z-1) reduces to p ts/(z-1), which drops the one-sample latency. The model integrator is theta[k+1] = theta[k] + T w[k], that is T/(z-1), and the latency z^-1 is added on top.
Source: margins_models.py line 198 `att_p * zi**att_lat * T * zi/(1-zi)` with zi = z^-1, so zi/(1-zi) = 1/(z-1) and A_att = p T z^-1/(z-1) = p T/(z (z-1)). (NOTES_F's "sign" worry is a misreading: the source's z/(1-z) is written in zi = z^-1, there is no sign flip.)
Fix: A_att = p z^-1 * ts/(z-1), with the text "an integrator of the rate (forward Euler) and a delay of one sample". Effect on numbers: none (the tables come from the model code), but the printed equation does not match it.

### R4 (MAJOR), lines 134 to 139, equation (an_outer)
Problem: (a) K_p, K_v are already defined in ch04 as the INDI position and velocity gains (MC_INDI_XY_P 1.2, MC_INDI_XY_VP 2.4); here they are called "the position and velocity gains" without saying that they are the gains of the stock position/velocity controller that ran in the pre-final flights, and K_i, K_d do not exist in ch04. A reader will take the ch04 values. (b) Meaning of each gain is not given (K_i velocity integral, K_d velocity derivative acting on the 5 Hz filtered velocity). (c) The reader is not told the gain values were assumed.
Source: model_vs_measured.md "S93 orchestrator check": flights ran with the stock-structure position controller (MPC_XY_P etc.); defaults assumed (Kp 0.95, Kv 1.8, Ki 0.4, Kd 0.2), "not read from the flown parameter dump".
Fix: add "K_p is the position gain, K_v, K_i, K_d the proportional, integral and derivative velocity gains of the position controller that was active in these runs; the values used in the model are the stock defaults, they were not read back from the flights. They differ from the K_p, K_v of chapter 4 and they are not part of the final configuration." Or rename to K_p^s etc. so that ch04 notation is not reused.

### R5 (MAJOR), line 141
Problem: "The acceleration increment of the INDI stage adds no small-signal path" is stated as fact. It is an assumption in the source.
Source: t195 note: "increment adds no path except mismatch (drag*v term, UNVERIFIED size)"; model_vs_measured.md: "INDI acceleration increment assumed to cancel at 1.3 Hz".
Fix: "The model assumes that the acceleration increment of the INDI stage cancels, and adds no small-signal path; this was not checked." This matters because the 0.3 deg PM agreement depends on it.

### R6 (MAJOR), lines 172, 175, 300 (plateau GM and "no gain margin")
Problem: "plateau gain margin" is used three times but never defined. The reader cannot tell why 12.9 differs from 13.5 and what "the second key's reading of the flat gain region" is. The gate rule (GM reported with the minimum of 1/|L| where the phase is within 10 deg of -180 deg; the pass uses the smaller) is missing from the criteria section. Also, "7 of 8 cells have no gain margin" is only true for the primary scorer: the 400 Hz seed-2 pt1 D cell has 16.3 dB in key 2, and the four pt0 D cells have a plateau GM of about 28 dB in key 2, so "none" in the table row pt0, D hides a reading that the second key gives.
Source: GATES.md G2 "Pass" bullet and Q13 A; G2_SCORES.md columns "plateau GM dB (key2)" (27.99 to 28.03 for pt0 D).
Fix: in section an_criteria add: "Where the phase comes close to -180 deg without crossing (within 10 deg), the gain margin is also read as the smallest 1/|L| there, the plateau gain margin; the gate uses the smaller of the two." In line 175: "...in 7 of 8 cells in the primary scorer (the second key finds 16.3 dB in one of them and about 28 dB in the plateau of the four pt0 cells)". Add a table note for the D, pt0 row.

### R7 (MAJOR), line 302 (verdict)
Problem: "The attitude step test passes in 9 of 9 flights with both keys" cites a test that chapter 5 never introduces (no criterion, no figure, no table); the chapter is about margins and the verdict mixes in a second criterion without definition. The 9 of 9 is also the only place where "both keys" is used for something other than outer cells.
Source: G2_SCORES.md G2-STEP: 3 seeds x roll/pitch/yaw, overshoot <= 5 %, settle <= 450 ms (yaw 1350 ms); worst roll/pitch overshoot 0.65 %, worst settle 347.5 ms.
Fix: either add one sentence in the introduction and a short paragraph in the results ("A second part of the gate is an attitude step per axis, 3 seeds: overshoot at most 5 %, 2 % settling time at most 450 ms (yaw 1350 ms). All nine flights pass; worst overshoot 0.65 %, worst settling 347.5 ms.") or cross-reference the chapter where the step response is shown.

### R8 (MAJOR), lines 39, 40, 152, 159 to 164 (and table caption)
Problem: pt0, pt1 are internal injection-point ids (parameter value names), used as row labels and in prose. The brief forbids internal run names; they are a fragment of the cell names (pt1_ax2_r400_s2). A reader sees "pt0" and "pt1" with a one-line caption definition only.
Source: g2_margins.md (MC_INDI_PINJ_PT 0 / 1).
Fix: use "Stage input" and "Stage output" (or "Velocity/position break" and "Acceleration break", matching the figure rows) as row labels, and drop \texttt{pt0}/\texttt{pt1} from the table, caption and the table-break column (lines 39-40, 152).
Also: figure rows are named "Velocity/position" and "Acceleration"; the table rows use pt0 and pt1. Use the same names in both.

### R9 (MINOR), lines 70 to 73 and 301-302 versus 300
Problem: "key 1 and key 2" first appear on line 70 without naming what differs. Verdict line 300 says "All logs are clean after one re-flight" while three cells are "blocked": in the source "clean" means holes PASS and key agreement (20/24 clean). The word is used in a different sense.
Fix: say "No log has holes beyond the limit after one re-flight" and keep "blocked" separate. Add at line 70: "two scoring programs written independently".

### R10 (MINOR), lines 178 to 182
Problem: "a single gap of 22.5 ms against a limit of 10 ms excess" is muddled: the gap is 22.5 ms, the excess over the expected spacing is 11.25 ms, the limit is 10 ms.
Source: G2_SCORES.md: max gap 22.50 ms, excess 11.25 ms (limit 10 ms).
Fix: "a single gap of 22.5 ms in the position setpoint log, an excess of 11.25 ms over the limit of 10 ms". Also name the logged topic by function (it is already a function name, fine).

### R11 (MINOR), lines 96 to 98
Problem: "It is large in every cell, so this does not change the verdict" cannot be known without the value of the telemetry latency; it is supported only if the latency is below roughly 150 ms (75.5 ms is the smallest DM among rate cells, 229 ms for outer cells). The source says "never binding" without the value either.
Fix: "The latency is a few tens of milliseconds at most in the simulation model (value not recorded in the evidence); even the smallest margin, 75.5 ms for the rate loop, is expected to cover it, but this was not verified." Or record the model value if it is known. Also mention it as an evidence limit in the verdict list (it is only partly in the figure caption).

### R12 (MINOR), line 89
Problem: "worst of two runs, at controller rates of 800 and 400 Hz" is ambiguous: the two runs are two seeds at each rate. Line 147 says "two controller rates and two seeds". Also the freeze-10 evidence applies the limit to each cell (all 24), which is stricter.
Fix: "Each limit applies to the worst of two runs (two seeds), at controller rates of 800 and 400 Hz."

### R13 (MINOR), lines 92 to 94
Problem: "A gain margin of 6 dB tolerates a doubling of the effectiveness" is correct control engineering only with the right quantity: 6.02 dB is a factor 2 in loop gain. In INDI the loop gain scales with the ratio of true to modelled control effectiveness, so a doubling of that ratio (a model that underestimates effectiveness by half) is the case; an overestimate of effectiveness (true half the model) makes the loop gain smaller, a gain-reduction case that the low-frequency crossing of reading rule 2 addresses. Also "PM of 45 deg leaves room for unmodelled lag" is fine but is better said with its equivalent: at the crossover f_c, 45 deg corresponds to an extra delay of 1/(8 f_c).
Fix: "A gain margin of 6 dB means the loop gain may rise by a factor of two before instability, for example if the real control effectiveness is twice the identified value." Optionally add the 1/(8 fc) remark.

### R14 (MINOR), line 54
Problem: "$T_p$" is not defined and "the multiple of $1/T_p$" is ungrammatical.
Fix: "Its frequencies are integer multiples of $1/T_p$, where $T_p$ is the period of the multisine (7.5 to 20 s), with 10 bins per decade."

### R15 (MINOR), lines 251 to 257
Problem: the rate cross-check reports a model PM of 23.6 and GM of 4.7 dB, below the 6 dB and 45 deg limits, with no word that this is the old law without the setpoint lead (the pre-lead configuration), which the reader may take for the final loop. The phrase "when the setpoint lead was added" comes later. Also the next sentence says the lead change was 9.7 vs 8.4 deg, direction (drop) fine.
Fix: "an earlier measurement, taken before the setpoint lead of chapter 3 existed (phase margin 23.6 against 22.3 deg, ...; these are not the final loop)". Add "The final-loop rate margins are in table an_spot only" and the explanation of why the final rate PM is 46.9 and the earlier flights showed about 69 deg (source gives none; say that the spot cell and the earlier pre-final flights are different firmware and the difference is not explained, if this is to be mentioned at all). A reader comparing with chapter 3's earlier numbers will ask.

### R16 (MINOR), lines 262 to 267 and 284 to 289
Problem: (a) "Both gain margins are far above 6 dB" refers to two quantities but the table has three rates; the sentence should say "model and measured gain margins are all above 17 dB". (b) The acceptance rule is "within 10 deg and 3 dB, or the difference is explained"; for 400 and 267 Hz the chapter states the cause is "not shown", and never says whether the cross-check is accepted. Source: accepted as conservative and bounded (measured GM >= 21.8, model GM >= 17.2). (c) The delta sign (measured minus model) is not stated in the table header.
Fix: add "The cross-check is therefore accepted on the grounds that the model is conservative and both gain margins stay above 17 dB." Add to caption "$\Delta$ = measured minus model". Replace "Both" by "All".

### R17 (MINOR), lines 290 to 293
Problem: the three-frequency check with "the stock horizontal gains" does not say which loop break (stage input) or which model produced the prediction; "stock" contradicts line 134's "the position and velocity gains" without a definition, and the stock gains are not those of the final configuration (ch04). A reader cannot judge 0.60 vs 0.69.
Fix: state the break (velocity/position, horizontal), say 15 % to 15 % deviations in |L| (0.69/0.60 = 1.15, 0.27/0.29 = 0.93, 0.16/0.14 = 1.14), that this is a pre-final check with the stock gains of that time, and that it does not validate a model.

### R18 (MINOR), lines 237 to 243
Problem: "The Nichols chart shows the same two points on one curve" and "passes the critical point with a clear gap" give no number for the gap. Figure and ch03 caption are consistent (1.72 Hz, 46.9 deg, 18.3 Hz, 15.7 dB) so only the unquantified claim is weak. Also the phase "-133 deg" is 180 - 46.9 = 133.1 (interpolation of the data gives -133.4); fine, but state it as "about".
Fix: "The curve stays 15.7 dB below and 46.9 deg to the right of the critical point at the two closest passes" or drop the sentence. Also the Bode figure is in ch03: since line 195 introduces the rate cell, a forward reference to the figure number would help the reader at line 197 already.

### R19 (MINOR), line 235 and lines 230-234 (figure explanation)
Problem: the text explains markers and dashed lines but not the panel layout (three panels: phase, gain, delay), the two delay-margin thresholds (2 periods at 800 and at 400 Hz, drawn as two dashed lines, not one), the grouping in rows (rate, attitude, velocity/position, acceleration, each xy and z), and why "Acceleration, z" has a marker at 22 dB (the 22.4 dB cell). The log axis of the delay panel is not mentioned. The rate and attitude rows have one cell each; the reader may think it is a plot of statistics.
Fix: add 3 sentences: "Left to right: phase margin, gain margin, delay margin (log axis). Each row is a loop; the rate and attitude rows hold one cell, the others 8. The two delay thresholds are two control periods at 800 and at 400 Hz."

### R20 (MINOR), line 297
Problem: "(G2)" gate id and "stability gate" appear without a pointer to where gates are defined. Acceptable if the gate scheme is introduced in ch01 (it is, table with C2); add cross-reference. Not development trail by itself. No file names, decision ids, Q or session numbers were found in the text (checked: no `M:`, `D-`, `S1xx`, `Q1x`, `.py`, `.md`, `freeze`).
Fix: "(gate G2, \cref{...})" if a label exists.

### R21 (MINOR), line 111
Problem: the cross-check rule given is the rule in the gate text, but the sentence "or that the difference is explained" lacks the second half of the gate: "a margin that passes only because it disagrees with the model is not a pass". It matters because the attitude GM residue is on the conservative side.
Fix: add that sentence.

## Totals

BLOCKER 0, MAJOR 8 (R1 to R8), MINOR 13 (R9 to R21). Total 21.
Most important: R3 and R1 for correctness (the printed attitude equation drops the one-sample delay of the model; the 250/267 Hz contradiction between figure caption and text), R4 and R5 for honesty of the cross-check (outer-loop gains and cancellation are assumptions, with a notation clash with chapter 4).
