# Fixes for the chapter 5 section review (chapters/05_analysis.tex)

| Id | Status | What / why |
|---|---|---|
| R1 | FIXED | Figure caption and verdict: "reported 267 Hz rate was not flown on the final configuration" (GATES.md G2 Configurations). |
| R2 | FIXED | L_M3a renamed L_tq ("loop broken at the torque setpoint") in eq. (an_ident) and text. |
| R3 | FIXED | A_att = p z^-1 ts/(z-1); text says forward-Euler integrator plus one-sample delay (margins_models.py, att_p*zi**lat*T*zi/(1-zi)). |
| R4 | FIXED | K_p, K_v, K_i, K_d defined; stated as stock-controller gains, assumed defaults not read back, different from ch04 K_p, K_v. |
| R5 | FIXED | Cancellation of the INDI acceleration increment stated as a model assumption, not checked, and the 0.3 deg agreement depends on it. |
| R6 | FIXED | Plateau GM defined in the criteria section (gate uses the smaller reading); "7 of 8" qualified as primary scorer with the 16.3 dB and ~28 dB second-key readings; note in the D, velocity/position row (G2_SCORES.md). |
| R7 | FIXED | Attitude step test introduced in the verdict item with criteria and worst values (G2_SCORES.md G2-STEP). "Both keys" dropped. |
| R8 | FIXED | pt0/pt1 removed everywhere; rows now "Velocity/position" and "Acceleration", as in the figure; caption explains the two breaks. |
| R9 | FIXED | "two estimators written independently"; "No log has holes beyond the limit after one re-flight". |
| R10 | FIXED | Gap 22.5 ms, excess 11.25 ms, limit 10 ms. |
| R11 | FIXED | Latency stated as not recorded, expected a few tens of ms, unverified; added as fifth evidence limit. |
| R12 | FIXED | "worst of two runs (two seeds)". |
| R13 | FIXED | GM wording as loop-gain factor of two; 1/(8 fc) remark added. |
| R14 | FIXED | T_p defined (7.5 to 20 s). |
| R15 | FIXED | Rate cross-check labelled as earlier, not final loop; pointer to the spot table. The 46.9 vs ~69 deg difference is not mentioned (source gives no explanation, so it is not raised). |
| R16 | FIXED | "All above 17 dB", acceptance sentence added, caption states delta = measured minus model. |
| R17 | FIXED | Break named (velocity/position, horizontal), stock gains of that time, ratios 1.15/0.93/1.14, not a model validation. |
| R18 | FIXED | Gap quantified (46.9 deg, 15.7 dB), "about -133", forward reference to the Bode figure. |
| R19 | FIXED | Panel order, rows, one-cell rows, two delay thresholds and log axis explained in the text. The 22.4 dB marker is explained in the table text already; not added again. |
| R20 | FIXED | Verdict points to the criteria table (tab:criteria) with G2. |
| R21 | FIXED | Sentence "a margin that passes only because it disagrees with the model is not a pass" added. |

Counts: 21 FIXED, 0 REJECTED.

## Outside ch05
- The figure script/FIGURES.md caption for g2_margins (the 250 Hz wording): the caption text is set in ch05 and fixed there, but the FIGURES.md text should match.
- ch02: "4 of 8" vertical cells without gain margin should read 7 of 8 (primary scorer).
