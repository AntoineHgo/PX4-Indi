# Chapter 2 marker check (session 24)

Report checked: `indi_project/report/02_state_of_the_art.md`. Report not edited.
Sources: notes in `indi_project/research/notes/`, bibliography `research/sources.md`, text extractions under `research/raw/` (pdftotext output and forum JSON), code under `research/raw/paparazzi/`. No downloads. Paths below are relative to `indi_project/`.

Summary: 8 markers found. CONFIRMED 6 (lines 11, 33, 51, 63, 83, 88). NOT FOUND 1 (line 17). NOT A CLAIM 1 (line 3, convention text). CORRECTED 0.

Caveat: "raw" means pdftotext output, not page images. Equation and table checks are against that extraction.

---
## Line 3 - `[TO VERIFY]` (not a claim)

- Marker text: `` `[TO VERIFY]` ``
- Claim: none. The sentence describes the marking convention ("equations that the notes flag as reconstructed are avoided or marked `[TO VERIFY]`"). It is a literal marker string, not a marker on a statement.
- Verdict: NOT A CLAIM (outside the three verdict labels; flagged for you).
- Evidence: n/a.
- Proposed replacement: keep the sentence, but reword the literal so the marker count stays at 7 real markers, for example "...are marked with a to-verify tag." Your call.

---

## Line 11 - `[TO VERIFY against PDF]`

- Marker text: `[TO VERIFY against PDF]`
- Claim: the note finds the printed parallel-form constants of acquatella2017 inconsistent, so only the structure is used.
- Verdict: CONFIRMED.
- Evidence:
  - `research/raw/foundations/arxiv_1701.08981.txt` Eq. (26), line 277: "δ(t) = K e(t) + T_I^-1 ∫e(σ)dσ + δ_DC" (no K on the integral term).
  - Same file, Eq. (27), line 288: "δ(k) = K e(k − 1) + T_I^-1 Σ t_s e(i) + δ_DC".
  - Same file, Eq. (29), line 241: "K = (ḡ · t_s)^-1, T_I = k_P^-1".
  - Consequence: with K = 1/(ḡ t_s) and T_I = 1/k_P, the printed integral coefficient is 1/T_I = k_P, not K·k_P. So the printed forms do not reproduce Eq. (29). Matches `notes/acquatella2017.md` line 58.
- Proposed replacement: "The printed parallel-form constants are inconsistent: the integral term in Eqs. (26)-(28) has no K factor, which does not reproduce Eq. (29), so only the structure is used [acquatella2017, Eqs. 26-29]."

---

## Line 17 - `[TO VERIFY against PDF]`

- Marker text: `[TO VERIFY against PDF]`
- Claim: the rotor-momentum equations of smeur2016 are partly garbled in the extraction.
- Verdict: NOT FOUND.
- Evidence:
  - No text extraction of smeur2016 exists under `research/raw/`. A filename search for smeur2016 and the DOI suffix G001490 returned only `notes/smeur2016.md`. The raw-tree title search also found nothing.
  - The only support is the note itself: `notes/smeur2016.md` line 144 ("Eq. (2)/(3): rotor momentum equation partly garbled") and line 152 (Eqs. 22-27 garbled). I did not verify those against any extraction.
- Proposed replacement: "The rotor-momentum equations could not be checked against a clean text extraction here, so chapter 3 carries the model [smeur2016, Eqs. 2-3]."

---

## Line 33 - `[TO VERIFY against PDF]` (Table 1 of smeur2018)

- Marker text: `[TO VERIFY against PDF]`
- Claim: converged thrust-axis effectiveness from two initial values agreed with the offline value.
- Verdict: CONFIRMED. Wording caveat: the paper says "converged" for the average of five flights per start value.
- Evidence:
  - `research/raw/foundations/smeur2018_cascaded.txt` Table 1, lines 445-460: "Adaptation from -0.35: -0.77 -0.73 -0.58 -0.63"; "Adaptation from -1.13: -0.76 -0.73 -0.59 -0.65"; "Offline: -0.76 -0.72 -0.57 -0.63" (units 10^-3 m/s²/rpm).
  - Same file, lines 469-476: "after 30 seconds the control effectiveness of each motor on average has converged very close to the value calculated offline".
  - Largest gap to offline across both start values is 0.02 (M3 and M4 from -1.13).
- Proposed replacement: "In Table 1, the thrust-axis effectiveness after 30 s of adaptation, from each of two initial values, lies within 0.02 x 10^-3 m/s²/rpm of the offline value for every motor [smeur2018, Sec. 4.2, Table 1]."

---

## Line 51 - `[TO VERIFY against PDF]` (gains in smeur2018)

- Marker text: `[TO VERIFY against PDF]`
- Claim: the gains printed in Sec. 2 and Table 2 conflict.
- Verdict: CONFIRMED.
- Evidence:
  - `research/raw/foundations/smeur2018_cascaded.txt` line 248 (Sec. 2): "With K_Ω = 28.0 and K_η = 21.4".
  - Same file, Table 2, lines 672-673: "K_Ω 10.7 (rad/s²)/(rad/s)" and "K_η 28.0".
  - Matches `notes/smeur2018.md` lines 66-70.
- Proposed replacement: "The gains printed in Sec. 2 (K_Ω = 28.0, K_η = 21.4) and in Table 2 (K_Ω = 10.7, K_η = 28.0) conflict, so they cannot both describe the flown design [smeur2018, Sec. 2, Table 2]."

---

## Line 63 - `[TO VERIFY against PDF]` (wang2019 Monte Carlo)

- Marker text: `[TO VERIFY against PDF]`
- Claim: NDI had the other model term exact, and the 31 failures are removed from NDI statistics.
- Verdict: CONFIRMED.
- Evidence:
  - `research/raw/robustness/wang_pure.txt` lines 1007-1008: "both controllers overestimate the control effectiveness matrix by 30%. On the other hand, the perfect model α̂ = α is used by NDI" (extraction shows "α^ α").
  - Same file, lines 1376-1377: "...the box plots in Fig. 13, in which the 31 failure cases under NDI control have been discarded. The interquartile range (IQR) values..."
  - Matches `notes/wang2019.md` lines 83 and 92.
- Proposed replacement: "NDI was given the exact α̂ = α, and the 31 NDI failure cases were discarded before the box plots and IQR values [wang2019, Sec. IV.D]."

---

## Line 83 - `[TO VERIFY by test]` (impl_paparazzi adaptation)

- Marker text: `[TO VERIFY by test]`
- Claim: the adaptation input scaling is consistent only for one value of its constant, and the airframes use another.
- Verdict: CONFIRMED by static code reading. The test is still outstanding: nothing was run.
- Evidence:
  - `research/raw/paparazzi/sw/airborne/firmwares/rotorcraft/stabilization/stabilization_indi.c` lines 1032-1033: du and ddu are scaled by `STABILIZATION_INDI_ADAPTIVE_MU` (and MU/PERIODIC_FREQUENCY); the measured `ddx_estimation` (around line 1035) is not scaled.
  - Lines 1041-1050: prediction `ddx_error += g1_est * du_estimation`; line 994: `g1_est -= du_estimation * mu * ddx_error`.
  - `stabilization_indi.h` line 31: `#define INDI_G_SCALING 1000.0`; `stabilization_indi.c` line 1098: `g1g2 = g1 / INDI_G_SCALING`. Together, the prediction matches the measurement only if mu = 1/1000 = 1e-3.
  - Code default: `stabilization_indi.c` line 87: `STABILIZATION_INDI_ADAPTIVE_MU 0.001f`.
  - Airframes: `conf/airframes/ENAC/quadrotor/bebop2_fish.xml` line 177 `ADAPTIVE_MU 0.0001`; also `robobee.xml` 170, `djIR.xml` 163, `anton_map.xml` 169, `hexa_tilted_motors.xml` 169.
  - Caveat: the note's `INDI_EST_SCALE 0.001` (note line 107) is defined in `stabilization_indi_simple.c` line 107, not in the full controller. The sentence above relies only on the full controller.
- Proposed replacement: "By reading the code, the adaptation scales its input by ADAPTIVE_MU but not its measured output, so the prediction matches only when ADAPTIVE_MU = 1/INDI_G_SCALING = 1e-3, the code default; the example airframes set 1e-4 [impl_paparazzi, Sec. B5]. This is a static reading and has not been tested in simulation or flight."

---

## Line 88 - `[TO VERIFY against the thread]`

- Marker text: `[TO VERIFY against the thread]`
- Claim: one PX4 forum poster's vehicle took off and shook, with 8 Hz on motor speed against 20 Hz on rates and G2 ignored, and quotes "If same, the vehicle can not take off".
- Verdict: CONFIRMED. The thread is available locally as JSON, so the marker can be resolved.
- Evidence: `research/raw/px4_eco/forum_36293.json`
  - Offset ~17375: "cutoff frequency is 8hz(motor rpm) and 20hz(rates). If same, the vehicle can not take off." Author field "lviron", created_at 2024-03-05.
  - Offset ~18876: "Additionally, I ignore the G2 matrix." Dated 2024-03-05. I did not confirm that this post has the same author.
  - "took off but shakes" (2024-03-05) is in `notes/impl_px4_prior.md` line 61. Not checked against the JSON.
  - The quote is the poster's own remark about the cutoff mismatch. Its meaning is not established.
- Proposed replacement: "One poster's vehicle took off and shook, with 8 Hz on motor speed against 20 Hz on rates and G2 ignored [impl_px4_prior, Sec. 4B; forum thread 36293, posts of 2024-03-05]. The poster wrote "If same, the vehicle can not take off" about the two cutoffs; the cause of the shaking is not established."

---

## Open items

- Line 17 (smeur2016): no local text of the paper. The garbling claim rests on the note alone.
- Line 83: the test named in the marker is still outstanding. Remove the marker only if the report says the check is static.
- Line 3: literal `[TO VERIFY]` in convention text; reword to avoid counting it as a marker.
- Line 88: the author of the "ignore G2" post is not confirmed.
