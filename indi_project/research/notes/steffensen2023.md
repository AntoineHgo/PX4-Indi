# Steffensen, Steinert, Smeur (2023): Nonlinear Dynamic Inversion with Actuator Dynamics: An Incremental Control Perspective

**Citation.** R. Steffensen, A. Steinert, E. J. J. Smeur, "Nonlinear Dynamic Inversion with Actuator Dynamics: an Incremental Control Perspective", *Journal of Guidance, Control, and Dynamics* (JGCD), 2023, as given in the brief. The PDF carries only the arXiv stamp `arXiv:2201.09805v2 [eess.SY] 25 Nov 2022`. The journal volume, pages and DOI are **not verified** from the PDF. Affiliations as printed: Technical University of Munich; Delft University of Technology.

**Local copy.** `indi_project/research/raw/robustness/steffensen_arxiv.pdf` (16 pages). Text extracted to `indi_project/research/raw/robustness/steffensen_arxiv.txt` with `pdftotext -layout`.

**Page convention.** Page numbers are the arXiv v2 printed page numbers, taken from the footer digit at the bottom of each page in the extracted text. They may differ from the JGCD pagination. Section, equation, figure and reference numbers are the paper's own. Lines cited as "l." refer to line numbers in `steffensen_arxiv.txt`.

**Extraction caveat.** `pdftotext` flattens sub/superscripts, matrix inverses and Greek letters. Multi-line equations are marked "[reconstructed]" below (Eqs. 11-16, 24-27, 31-32, 47-48). Eqs. 1-10, 17-23 and 28-30 are readable in the text, but their exact placement of inverses and bars still needs a page-image check before quoting. Eqs. 33-46 (roll example) are readable.

## Summary

1. The paper derives a sensor-based NDI law for a control-affine system with first-order linear actuators. It differentiates the output one more time than its relative degree, so the actuator dynamics are inverted too (Eqs. 2-6, pp. 3-4). The resulting NDI law (Eq. 9, p. 4; Eq. 16, p. 5) uses the measured state derivative x-dot, not a model for it.
2. Traditional INDI is shown to be a limit of this NDI law. With equal actuator bandwidths omega and Omega_y = omega*I, the INDI law (Eq. 23, p. 6) equals the NDI law with the first term dropped (Eqs. 24-26, p. 7). The paper claims INDI approximates the NDI control signal arbitrarily well as omega grows (Eq. 26, p. 7; p. 14 l. 917-919). It does **not** claim the INDI closed-loop error dynamics converge to the designed ones: the Appendix (pp. 13-14, Eq. 48) says INDI "does not produce the correct error dynamics" even in the limit.
3. The advantages claimed for NDI when the actuators are slow are (i) compensation of state-derivative terms, (ii) well-defined error dynamics, and (iii) exact tracking of a reference model under nominal conditions (abstract, p. 1). The derivation supports (ii) and (iii) through Eq. 10 (p. 4). The only numerical support is a single SISO fixed-wing roll-rate example with no sensor noise and no parameter uncertainty (Sec. V.A, p. 9; Figs. 2-7, pp. 10-12).
4. The NDI law needs the actuator bandwidth omega (Eqs. 16, 31, 36 and 43); the INDI law (Eq. 21/23) does not. The paper treats the actuator state u as available (Eqs. 1-2, p. 3; "state information was available without noise", p. 9). It proposes no estimator for an unmeasured actuator state, and does not say whether the u_0 term in INDI is the measured actuator state or the previous command (Eq. 18, p. 6).
5. Validation is simulation only, on a single SISO roll-rate example of a fixed-wing aircraft. The paper has no multirotor, no flight test and no table. Results are in Figs. 2-7 only, and no numerical error values are given in the text. The paper itself says the actuator bandwidth "might be uncertain" and that actuators may not be first-order (Discussion, p. 13 l. 837-839).

## (a) Main claim: NDI with actuator dynamics and its relation to INDI

**Setting (Eqs. 1-3, p. 3).** System x-dot = f(x,u), y = h(x), with u the actuator state (Eq. 1, p. 3). First-order actuators: u-dot = Omega (u_c - u), Omega a constant diagonal matrix of actuator bandwidths (Eq. 2, p. 3). Relative degree r with respect to u: y^(r) = F(x,u) (Eq. 3, p. 3). The paper's stated assumption is that the relative degree is r for all outputs (p. 3, l. 162-163).

**Key step (Eqs. 4-6, pp. 3-4).**
- y^(r+1) = F_x x-dot + F_u u-dot (Eq. 4, p. 3), with F_x = dF/dx and F_u = dF/du (p. 3).
- Substitute Eq. 2: y^(r+1) = F_x x-dot + F_u Omega (u_c - u) (Eq. 5, p. 4).
- The paper keeps x-dot unexpanded "to allow it to be possibly determined by measurements" (p. 4, l. 182-183).
- Set y^(r+1) = nu (virtual control). If F_u Omega has full row rank, u_c = (F_u Omega)^dagger (nu - F_x x-dot) + u (Eq. 6, p. 4), where ^dagger is any right inverse (p. 4).

**Error dynamics (Eqs. 7-8, p. 4).** e_y = y_ref - y. Generic form: e_y^(r+1) + sum_{i=0}^{r} k_i e_y^(i) = 0 (Eq. 7, p. 4). Pseudo control nu = y_ref^(r+1) + sum_{i=0}^{r} k_i e_y^(i) (Eq. 8, p. 4).

**NDI law with error controller (Eq. 9, p. 4).** u_c = (F_u Omega)^dagger [ y_ref^(r+1) + sum_i k_i e_y^(i) - F_x x-dot ] + u (Eq. 9, p. 4, text-readable). The paper calls this "an NDI control law with linear error controller, where the actuator dynamics were additionally included in the system dynamics and inverted" (p. 4, l. 218-219).

**Exact error dynamics (Eq. 10, p. 4).** Substituting Eq. 9 into Eq. 5 gives y^(r+1) = nu, using (F_u Omega)(F_u Omega)^dagger = I (p. 4, l. 220). The error dynamics are then the designed ones, Eq. 7 (p. 4, l. 231-232).

**Split error dynamics (Sec. II.A, p. 5).** The paper rewrites the design as a product of a system part and an actuator part, to make the "desired inner-loop bandwidth" Omega_y explicit.
- Laplace form (Eq. 11, p. 5) [reconstructed]: E_y(s) [ s^r I + sum_{i=0}^{r-1} K_i s^i ] [ s I + Omega_y ] = 0. The system part has gains K_i; the actuator part has Omega_y (p. 5, l. 265-277).
- Time-domain forms: Eq. 12, Eq. 13 [reconstructed], Eq. 14 [reconstructed] (p. 5, l. 282-316).
- Pseudo control with split gains (Eq. 15, p. 5) [reconstructed]: nu = y_ref^(r+1) + sum_{i=1}^{r} K_{i-1} e^(i) + Omega_y e^(r) + sum_{i=0}^{r-1} K_i e^(i).
- Final control law (Eq. 16, p. 5) [reconstructed]: u_c = (F_u Omega)^dagger [ y_ref^(r+1) + sum K_{i-1} e^(i) + Omega_y e^(r) + sum K_i e^(i) - F_x x-dot ] + u.
- The paper notes the system can be made arbitrarily fast through Omega_y, but practical choice should be limited to the actuator design bandwidth (p. 6, l. 343-347).

**Comparison with Bhardwaj et al. [23] (p. 4, l. 233-243).** The state-dependent term F_x x-dot is supplied by a physical reference model in [23]. The paper argues the feed-forward is only correct if the plant tracks the reference model and the zero-dynamics states match. Under disturbances the error dynamics are excited by F_x(x-dot - x-dot_ref) (Eq. 10 context, p. 4). The paper's law uses measured x-dot and so keeps the designed error dynamics. A possible drawback: reduced stability margins from the extra feedback, "but this requires further investigation" (p. 4, l. 240-242).

**Classical INDI (Sec. III, pp. 6-7).**
- Taylor expansion of F about (x_0, u_0) with x_0 = x(t - dt), u_0 = u(t - dt) (Eqs. 17-18, p. 6; text-readable). The paper states that "the classic INDI derivation contains some inaccuracies" (p. 6, l. 357-358).
- Linearised relation nu = y_0^(r) + F_x (x - x_0) + F_u (u_c - u_0) + O(dx, du) (Eq. 19, p. 6), solved for u_c (Eq. 20, p. 6).
- The term F_x (x - x_0) is usually neglected (Eq. 21, p. 6; the paper cites [24, 25]).
- With the desired error dynamics of Eq. 12 and the nu of Eq. 22 (p. 6), INDI reads u_c = F_u^dagger [ y_ref^(r) + sum K_i e^(i) - y_0^(r) ] + u_0 = F_u^dagger e^(r) + sum K_i e^(i) + u_0 (Eq. 23, p. 6, text-readable).
- The paper notes Wang et al. [16] keep F_x(x - x_0) with Delta x = x-dot(t - dt) dt (p. 6, l. 385). Because the actuator does not reach u_c within one sample, the term is "not exactly canceled" and the stability properties "are unclear" (p. 6, l. 385-388). The same concern appears in the intro (p. 2, l. 91-95).

**Equal-bandwidth comparison (pp. 7-8).** Assumptions (p. 7, l. 410-411): (1) Omega = omega I, omega > 0; (2) Omega_y = omega I.
- Identity (Eq. 24, p. 7, text-readable): (F_u Omega)^dagger Omega_y = F_u^dagger.
- Substituting, the NDI law becomes (Eq. 25, p. 7) [reconstructed]: u_c = (1/omega) { F_u^dagger [ y_ref^(r+1) + ... - F_x x-dot ] } + F_u^dagger e^(r) + ... + u.
- Limit omega -> inf (Eq. 26, p. 7) [reconstructed]: u_c = F_u^dagger e^(r) + sum K_i e^(i) + u, which is the INDI law of Eq. 23 (p. 7, l. 428-429).
- The paper says "the first term in Eq. (25)" is the one INDI neglects, and that the mismatch "vanishes for sufficiently large actuator bandwidth" (p. 7, l. 448-452).
- The paper's wording: "for a fixed time, the INDI law approximates the true NDI law arbitrarily well" by choice of omega (p. 7, l. 459-461).
- The paper's claim that the INDI law "does not hold in the limit" (p. 7, l. 459) is clarified in the Appendix (see below).

**Input scaling (Sec. III, p. 7, l. 462-489).** With Omega_y = Lambda omega, Lambda diagonal, Eq. 27 gives the INDI law with a scaling gain (Eq. 27, p. 7) [reconstructed]: u_c = F_u^dagger Lambda e^(r) + ... + u. Cordeiro et al. [19] observed that Lambda elements below 1 reduce the closed-loop bandwidth (p. 7, l. 486). The paper identifies Lambda = 1 as the case where desired innermost bandwidth equals actuator bandwidth (p. 7, l. 487-489).

**Actuator-including INDI (Sec. IV, p. 8).**
- Smeur et al. [15] showed that when INDI (Eq. 21) is applied with actuator dynamics, y^(r) follows nu with the actuator dynamics, provided F_x x-dot is neglected and all actuators have equal bandwidth (p. 8, l. 494-496).
- Combining Eq. 28, y^(r+1) = F_u u-dot = F_u omega (u_c - u) (p. 8), with INDI (Eq. 21) gives Eq. 29 (p. 8): **y^(r+1) = omega (nu - y^(r))**. The paper reads this as "y^(r) follows nu with the dynamics of the actuator" (p. 8, l. 502-503). For a rate loop, this is the angular acceleration following nu through a first-order lag of bandwidth omega.
- Virtual control Eq. 30 (p. 8) and the resulting law Eq. 31 (p. 8) [reconstructed]: u_c = F_u^dagger (1/omega) [ y_ref^(r+1) + sum K_{i-1} e^(i) + omega e^(r) + sum K_i e^(i) ] + u_0. The paper says this equals Eq. 16 with Omega = omega I, Omega_y = omega I, and F_x x-dot neglected (p. 8, l. 519). It "requires all actuators to have the same bandwidth, otherwise Eq. (29) does not hold" (p. 8, l. 519-520).
- Raab et al. [22] remove the equal-bandwidth restriction (Eq. 32, p. 8) [reconstructed]; it also equals Eq. 16 with F_x x-dot neglected, and it "offers the option to specify a desired Omega_y" (p. 8, l. 521-533).
- Note: Eq. 31 is written with u_0 and Eq. 32 with u, as extracted. The distinction should be checked against the page image.

**Roll-rate example (Sec. V, pp. 8-9).**
- Roll dynamics p-dot = L_p p + L_u u (Eq. 33, p. 8), with L_p < 0 "usually large" (p. 8, l. 543) and L_u < 0. First-order aileron actuator u-dot = omega (u_c - u) (Eq. 34, p. 8). Output y = p, relative degree r = 1 (p. 8, l. 548-549).
- Control relation p-ddot = L_p p-dot + L_u omega (u_c - u) (Eq. 35, p. 8).
- NDI control law (Eq. 36, p. 8; Eq. 43-44, p. 9): u_c = (1/(L_u omega)) [ p-ddot_d - L_p p-dot ] + u, with p-ddot_d = p-ddot_ref + k_1 e-dot + k_0 e, k_1 = omega_d - L_{p,d}, k_0 = -L_{p,d} omega_d (Eqs. 41-44, p. 9).
- Reference model p-dot_ref = -L_{p,d} delta - p_ref; delta-dot = omega_d (p_c - delta) (Eq. 37, p. 9). Desired error dynamics (Eq. 39-40, p. 9): e-ddot + omega_d e-dot - L_{p,d} e-dot + omega_d e = 0.
- Classical INDI for the same example (Eq. 45, p. 9): u_c = (1/L_u) (e-dot - L_{p,d} e) + u, with reference dynamics p-dot_ref = -L_{p,d} (p_c - p_ref) (Eq. 46, p. 9). Note that Eq. 45 has no omega, consistent with Eq. 23.
- Note the INDI reference dynamics (Eq. 46) differ from the NDI reference (Eq. 37): the comparison is not like-for-like in the reference model. The paper's Fig. 2 compares tracking against each law's own reference model (p. 10).

**Simulation settings (Sec. V.A, p. 9, l. 619-625).** No sensor noise, no parameter uncertainty. L_u = 0.25 (deg/s^2)/deg, L_p = -6.6 (deg/s^2)/(deg/s), L_{p,d} = 2 L_p = -13.2 (deg/s^2)/(deg/s), omega = 20 rad/s. Three laws compared: NDI (Eq. 43), INDI (Eq. 45), and INDI with actuators (Eq. 43 without L_p p-dot) (p. 9, l. 626-630).

## (b) Treatment of actuator dynamics

- **Model.** The actuator is a first-order lag with constant bandwidth, u-dot = Omega (u_c - u) (Eq. 2, p. 3). The paper does not give a time constant as such; the bandwidth omega = 1/tau is the parameter used (Eq. 34, p. 8; omega = 20 rad/s, p. 9). "Time constant" is therefore 1/omega by definition, not a separate quantity in the paper.
- **Bandwidth in the law.** The NDI law depends on omega (Eqs. 16, 31, 36, 43). INDI does not (Eqs. 21, 23, 45).
- **Actuator state.** The actuator state u is a state of the system and is used directly in the control law: "+ u" in Eq. 6, Eq. 9, Eq. 16, and "+ u_0" in Eqs. 21 and 23 (pp. 4-7). The paper does not discuss how u is obtained; the simulation assumes it is available without noise (p. 9, l. 619-620).
- **No estimator.** The paper proposes no model-based estimate of u, no observer and no RPM or position feedback. Our case (onboard first-order motor model, no RPM feedback) is therefore not covered by this paper.
- **Ambiguity in u_0.** Eq. 18 defines u_0 = u(t - dt), where u is the actuator state (Eq. 1). Eq. 20-23 treat u as the control signal and u_0 as the previous control. It is not clear whether the paper intends the previous actuator state or the previous command. This matters for our design, because "previous command" and "previous actuator state" differ by the actuator lag (p. 6, l. 385-388 suggests the paper is aware the command is not reached in one sample).
- **Effective bandwidth.** The paper says the NDI law "requires information about the actuator bandwidth, which might also be uncertain" and that "in case the actuators might not be first-order ... an effective bandwidth of the actuator can be used" (Discussion, p. 13, l. 837-839). No identification procedure is given.
- **Inference (not the paper's claim).** For our motor model, this means a bandwidth error affects the NDI law directly (the 1/omega gain in Eq. 36 and the omega e^(r) term in Eq. 31). The INDI law (Eq. 23) does not use omega, so its bandwidth dependence enters only through the closed-loop lag in Eq. 29. A model-based u estimate that is off in the transient would enter INDI through u_0 (Eq. 23) and be fed back as an increment error. The paper does not analyse this.

## (c) Filtering and synchronisation

- **Derivative filtering.** "In some cases, filtering of these noisy derivative signals may be required. Filtering leads to delay, which will lead to deterioration of the controller performance" (Discussion, p. 13, l. 829-830).
- **Filter synchronisation.** "For an INDI controller, this problem can be circumvented with filter synchronization of output and input filters [15], but that particular method cannot be applied to the feedback of x-dot in the proposed controller, as there is no signal to synchronize with" (p. 13, l. 830-832). The synchronisation method is not described in this paper. [15] is cited for it.
- **Suggested alternative.** "A complementary filter could be used, where the high frequencies are coming from a model, and the low frequencies from the filtered measurement [26, 27]" (p. 13, l. 832-833). Not analysed here.
- **Stability warning.** "The feedback of the state derivatives could influence the stability and robustness in the case of model uncertainty and measurement errors. How this compares to classical INDI has to be compared on a case to case basis" (p. 13, l. 834-836).
- **Inference (not the paper's claim).** In Eq. 29, the paper's own analysis shows the angular acceleration lag is first-order with bandwidth omega when F_x x-dot is neglected. Any extra filter on the angular acceleration measurement adds to that lag and changes the effective omega. The paper does not analyse this combined lag.

## (d) Experiments

- **Vehicle.** Simulated fixed-wing aircraft, roll rate only (SISO), Sec. V (p. 8). The Discussion and Conclusion (pp. 13) do not describe any further experiment.
- **Setup.** No sensor noise, no parameter uncertainty (p. 9, l. 619-621). Step command p_c = 5 deg/s (Fig. 2) and initial perturbation p(0) = 5 deg/s with p_c = 0 (Figs. 3, 5, 6, 7) (p. 10, l. 673-679; p. 11, l. 744-747).
- **Comparisons.** NDI (Eq. 43), classical INDI (Eq. 45), INDI with actuators (Eq. 43 without L_p p-dot) (p. 9, l. 626-630). The paper does not compare against PID or any other controller.
- **Figure results.** (Figure captions and axis labels are text-readable; the plotted curves are not.)
  - Fig. 2 (p. 10): NDI follows its reference model for the step; INDI does not follow its own reference model (p. 10, l. 673-675).
  - Fig. 3 (p. 10): NDI error dynamics match the designed dynamics exactly; INDI does not (p. 10, l. 676-681).
  - Fig. 4 (p. 11): INDI with actuators still does not track the NDI response, because the L_p p-dot term is dropped (p. 10-11, l. 682-685).
  - Fig. 5 (p. 11): with a 5 deg/s initial plant perturbation and zero reference state, NDI error dynamics match, and INDI with actuators do not (p. 11, l. 744-750).
  - Figs. 6-7 (p. 12): bandwidth sweep with omega = 5, 10, 20, 50 rad/s (legend). Fig. 6: INDI error approaches the INDI design dynamics as omega grows. Fig. 7: the NDI design error approaches the INDI design error as omega grows (p. 12, l. 756-763, 808-814).
- **Numbers.** No table. The paper gives no numeric error values for Figs. 2-7 in the text. Axis values (e.g., roll-rate error from 0 to -5 deg/s in Fig. 3) are read from the plots and are not quoted here.
- **Not present.** Multirotor, flight test, noise, parameter uncertainty, comparison with PID.

## (e) Implications for a PX4 rate-loop INDI (inference by the note author, not the paper's claims)

1. **Which law we are implementing.** The paper's INDI (Eq. 23, p. 6) is the form with F_u^dagger, the error terms, and u_0, with no actuator bandwidth. The classical PX4 INDI rate loop is in this family. The paper's "NDI with actuators" (Eq. 31, p. 8) is the variant that needs omega.
2. **The inner lag.** Eq. 29 (p. 8) says that with INDI and equal bandwidths, angular acceleration follows nu as a first-order lag with bandwidth omega. In our rate loop, omega would be the motor (effective) bandwidth. This gives a design point, but this is a single-axis, equal-bandwidth result and the paper does not verify it on a multirotor.
3. **Equal bandwidth.** The paper's Eq. 29 holds for equal bandwidths only (p. 8, l. 519-520). Raab et al. [22] (Eq. 32, p. 8) handle unequal bandwidths, but the paper does not compare them. Four similar motors would roughly satisfy the equal-bandwidth assumption; this is not verified.
4. **Actuator state.** The paper assumes u is known. If PX4 uses a model-based motor state estimate in place of a measured actuator state (no RPM feedback), that estimate enters the increment through u_0 (Eq. 23). The paper does not analyse estimate error. Verify with a sim test before relying on it.
5. **Filtering.** The paper suggests filter synchronisation for INDI (p. 13), and says it does not transfer to the x-dot feedback of its NDI law. For our INDI, this does not directly apply, because our feedback is the angular acceleration that the paper treats as y^(r), not x-dot. The paper gives no filter-synchronisation method in this text, so it cannot guide our implementation.
6. **Input scaling.** Lambda (Eq. 27, p. 7) is a tuning knob that reduces closed-loop bandwidth for Lambda < 1, per Cordeiro et al. [19] (p. 7, l. 486). This paper does not test it.
7. **Mismatch between control allocation and B.** The footnote (p. 4, l. 244-247) warns that when the control allocation matrix differs from the system input matrix, uncontrolled states may depend on the allocation. Relevant to our rate loop with multirotor mixing; the paper gives no analysis.
8. **Required signals.** NDI requires x-dot (Discussion, p. 13, l. 823-828). INDI needs only up to y^(r), which the paper says is the same requirement as INDI (p. 13, l. 823-824). For a rate loop, y^(r) is the angular acceleration.
9. **What the paper does not show for us.** No multirotor model, no F_x, no gyroscopic terms, no sensor noise, no RPM feedback. Any claim that the NDI-with-actuators law improves our hover yaw or roll-rate tracking is outside this paper.

## (f) Open questions and items to verify against the PDF page images

1. **Version.** The PDF is arXiv:2201.09805v2 (25 Nov 2022). The journal version (JGCD 2023, per the brief) is not in the file. Check the journal details and whether the content matches before citing the journal.
2. **Garbled equations.** Check the page images for Eqs. 11-16 (pp. 5), 17-23 (p. 6), 24-27 (p. 7), 31-32 (p. 8), 47-48 (p. 14).
3. **u_0 ambiguity.** Eq. 18 defines u_0 = u(t - dt) with u the actuator state (Eq. 1), but Eqs. 20-23 use u as the control signal. Determine from the page image and the derivation whether the paper means the previous actuator state or the previous command.
4. **Eq. 31 vs. Eq. 32.** Check whether the trailing term is u_0 or u in each.
5. **Appendix claim.** Sec. III (p. 7, l. 459) says "the INDI law does not hold in the limit". The Appendix (p. 14, l. 917-919) says INDI "only approximates the true NDI control signal u_c arbitrarily well". Read the Appendix Eq. 48 on the page image before quoting either sentence.
6. **Reference [16] is a different paper.** Steffensen's ref. [16] is Wang, Van Kampen, Chu, De Breuker, "Flexible Aircraft Gust Load Alleviation with Incremental Nonlinear Dynamic Inversion", JGCD 42(7), 2019 (p. 15, l. 981-983). Our local `research/notes/wang2019.md` is a different paper (Wang, van Kampen, Chu, Lu, "Stability Analysis for INDI Control", JGCD 42(5), 2019). Do not conflate them.
7. **Reference [15].** Smeur, Chu, de Croon (JGCD 2016) is cited for the INDI-with-actuators result (Sec. IV) and for the filter-synchronisation method (Discussion). The content of [15] is not in this PDF; any claim about it needs its own note.
8. **Figures.** Numeric values of error and response in Figs. 2-7 are not in the text. Read them from the page images if a number is needed; do not quote plotted values without a source reading.
9. **Sec. III equivalence statement.** The text says INDI approximates NDI "under the condition that the actuators are fast with equal bandwidth" (p. 4, l. 242-243; p. 3, contribution 3). Check the exact wording of the abstract in the journal version.
10. **Tuning parameter units.** The example uses deg-based units (L_p, L_u, L_{p,d} in (deg/s^2)/deg etc., p. 9). Convert before reusing numbers for PX4 (rad/s).
11. **Contribution page.** The contribution list (p. 3, l. 129-139), including "the traditional INDI law approximates the derived exact NDI control law" (p. 3, l. 136-137), is on p. 3. Verify on the page image before citing.
