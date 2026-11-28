# NOTES_F (chapter 5, analysis)

## Numbers not traced to a source (derived or written from reasoning)
- Phase at the roll rate crossover, -133 deg: arithmetic 180 - 46.9.
- "1.25 ms control period at 800 Hz": arithmetic from 800 Hz.
- "PM 49.1 is 4.1 deg above limit": arithmetic.
- Table 5.x (outer) ranges per break/axis: computed by script from the primary table in G2_SCORES.md (pt1_ax2_r400_s2 replaced by the re-fly values GM 13.9, PM 56.9, DM 485). Range ends for DM of pt1_ax2 (461 to 485) use the re-fly.
- "A gain margin of 6 dB tolerates a doubling of effectiveness" and the one-line reasons for the criteria: engineering explanation, not from a source.
- Eq. (A_att) written with discrete integrator ts z/(z-1); g2 notes write "ts z/(1-z)" (sign convention not traced). T_cl numerator N: source gives (K + lead) Pn.
- Eq. outer factor O(s): symbols Kp, Kv, Ki, Kd follow the t195 text; their values (MPC_XY_P 0.95, VEL_P/I/D 1.8/0.4/0.2) are not given in the chapter on purpose.
- Rate-loop model: described in words only; no L_indi equation was found in the sources read.

## Source disagreements
- Controller rate: task and figure notes say 250 Hz ("The 250 Hz controller rate was not measured", FIGURES.md caption); GATES/g2_margins.md say 267 Hz reported (266.7). Chapter says 267 in text, keeps the caption as given.
- z outer cells without -180 crossing: 02_outer_loop_design.md section 8 says 4 of 8; G2_SCORES.md primary table gives 7 of 8 (GM 22.4 only in pt1_ax3_r800_s2). Chapter uses 7 of 8 (gate scores).
- pt1_ax2_r400_s2: original row (PM 59.6, GM 13.8, DM 542) vs re-fly (56.9, 13.9, 485); chapter uses the re-fly as the GATES verdict does.
- pt1_ax1_r800_s1 key2 DM etc. not used. Rate roll: pre-freeze cells PM 69 deg (g2_margins.md) vs final spot 46.9 deg; the cause is not explained in the sources (chapter only reports the final cell).
- Model-vs-measured tables (Tab. an_att, rate cross-check) come from pre-final binaries (g2_margins.md, model_vs_measured.md); labelled as such.
- g2_margins.md says GM "nan" for z outer cells (no crossing) and xy GM 18-19 dB (pre-final); final xy GM is 13.5-14.6. Final scores used.
- Figure g2_bode_rate is already placed in ch03; ch05 refers to it (fig:bode_rate) and does not repeat it.
