# Acquatella, van Ekeren, Chu (2017): PI(D) tuning via INDI

**Citation:** P. Acquatella B., W. van Ekeren, Q. P. Chu, "PI(D) tuning for Flight Control Systems via Incremental Nonlinear Dynamic Inversion", IFAC 2017. arXiv:1701.08981v3 (5 Apr 2017). URL: https://arxiv.org/abs/1701.08981

Local text: `research/raw/foundations/arxiv_1701.08981.txt`. Numbers in brackets are the paper's equation numbers, "Sec." the paper's section headings. "[my check]" marks a derivation done for this note, not stated in the paper. Garbled or inconsistent text is listed in section 8.

## 1. Summary

- INDI applied to the rate loop is shown to be equivalent to time-delay control (TDC): the INDI law [18] and the TDC law [22] are the same expression (Sec. 3.3).
- Sampled and with first-order error dynamics, the TDC/INDI law is an incremental PI with K = (ḡ·t_s)^-1 and T_I = k_P^-1 [23-29]. Second-order error dynamics give an incremental PID [30].
- The only free tuning variable is the effectiveness gain ḡ; the desired error poles k_P (and k_D) set the integral (and derivative) times [8-10, 29, 30].
- The law is written without the airframe model f and without the effector blending G, which the paper calls "model-free" [16-18, Remark 1].
- Equivalence rests on approximations ε_INDI ≈ 0 [12], ε_TDC ≈ 0 [20], fast actuators [5], and a first-order Taylor expansion (Sec. 3.2).
- Only evidence: one simulated pitch-rate loop on a launcher-type longitudinal model (Sec. 4, Fig. 2). INDI and the derived PI gave the same response under nominal (matched) conditions. No mismatch case, no separately tuned PID, no saturation study.

## 2. Plant and assumptions (Sec. 2)

- Euler rotational dynamics [1]: I ω̇ + ω × I ω = M_B.
- Control-affine form [4]: ω̇ = f(ω) + G(ω)δ, with f = I^-1(M_a − ω×Iω) and G = I^-1(M_c)_δ (text garbled, see 8).
- Actuator [5]: G_a(s) = K_a/(τ_a s + 1). Actuator dynamics are left out of the design; the paper assumes 1/τ_a is higher than the closed-loop bandwidth (text after [5]).
- Rates have relative degree one (Sec. 3.1, text after [10]).

## 3. The INDI law as stated in the paper

**NDI baseline (Sec. 3.1).** Virtual input ν = ω̇_des [6-7]:
- Inversion [6]: δ = G^-1(ν − f). Single-integrator form [7]: ẏ = ν, with y = ω.
- Outer loop [8]: ν = ẏ_d + k_P·e, e = y_d − y. Error dynamics [9-10]: ė + k_P·e = 0.
- Needs exact f and G ("sensitive to model uncertainties", text after [10]).

**INDI (Sec. 3.2).** First-order expansion about the λ-delayed state [11a, 13]:
- Definitions [11a]: ω_0 = ω(t−λ), δ_0 = δ(t−λ), ω̇_0 = f(ω_0) + G(ω_0)δ_0 = ω̇(t−λ). δ_0 is taken from the actuator output (text after [14]).
- Approximation [12]: ε_INDI = f(ω(t−λ)) − f(ω(t)) ≈ 0, valid for small λ.
- Incremental model [13]: Δω̇ ≈ G_0·Δδ.
- Control [14]: δ = δ_0 + G_0^-1(ν − ω̇_0).
- Final form [15]: δ(t) = δ(t−λ) + G_0^-1[ν − ω̇(t−λ)].

**Effectiveness-free variant (Sec. 3.2, Chang & Jung 2009).** Split ω̇ = H + ḡ·δ [16], with H = f + (G − ḡ)δ and ḡ = k_G·I_n or diag(k_G1..k_Gn) [text after 16]:
- Control [17]: δ = ḡ^-1(ν − H).
- Incremental [18]: δ(t) = δ(t−λ) + ḡ^-1[ν − ω̇(t−λ)].
- Remark 2: the self-scheduling from G_0 in [15] is lost, so ḡ should be a scheduling variable.

**TDC (Sec. 3.3).** Control [19]: δ = ḡ^-1(ν − H̄). Time-delay estimate [20-21]: ε_TDC = H(t−λ) − H(t) ≈ 0, hence H̄ = H(t−λ) = ω̇(t−λ) − ḡ·δ(t−λ). Substituting gives [22], stated to be the same as the INDI law [18].

**Sampled form (Sec. 3.4).** The smallest λ is the sample period t_s. Causal form [23]: δ(k) = δ(k−1) + ḡ^-1[ν(k−1) − ω̇(k−1)].

## 4. Derivation of the PI(D) equivalence (Sec. 3.3-3.4)

**Paper's steps.**
1. Replace ν by [8] in [23], giving [24]: δ(k) = δ(k−1) + ḡ^-1[ė(k−1) + k_P·e(k−1)]. [my check: ν − ω̇ = (ẏ_d − ω̇) + k_P·e = ė + k_P·e, using ė = ẏ_d − ω̇ from e = y_d − y.]
2. Angular acceleration is not measured, so ė is replaced by the backward difference [25]: ė(k) = [e(k) − e(k−1)]/t_s. Remark 3: this difference is the counterpart of the acceleration ẋ_20 used in INDI.
3. Standard PI [26-27]; its incremental form [28]: δ(k) = δ(k−1) + K·t_s·ė(k−1) + T_I^-1·e(k−1).
4. Matching [24] to [28] gives [29]: K = (ḡ·t_s)^-1, T_I = k_P^-1.
5. Second-order desired dynamics ë + k_D·ė + k_P·e = 0 give the incremental PID [30]: K = k_D·(ḡ·t_s)^-1, T_I = k_D·k_P^-1, T_D = k_D^-1 (printed as "T_D = k_D^-1", see 8).
6. Example mapping [43-44] uses the same K and T_I.

**[my check] Constants.** I redid the matching for the printed PI forms:
- Integral part of [27] differenced: T_I^-1·t_s·e(k−1). Proportional part: K·t_s·ė(k−1). Matching to [24] gives K = (ḡ·t_s)^-1 and T_I = k_P^-1, which is exactly [29]. This holds for the form K(e + T_I^-1∫e).
- The parallel form written in [26] and [28] (integral coefficient T_I^-1 with no K and no t_s) does not give [29]; it gives an integral gain of K·k_P. So [26]/[28] and [29] are inconsistent as printed (see 8).
- Second order: with K = k_D/(ḡ·t_s), the derivative term K·t_s·T_D·ë matches ḡ^-1·ë only if T_D = k_D^-1, and the integral term needs T_I = k_D/k_P. This agrees with [30].

**Conditions under which the equivalence holds** (as the paper states them, collected by me):
- C1. Small delay, λ = t_s (Sec. 3.4). ε_INDI ≈ 0 [12]: f does not change over one sample.
- C2. ε_TDC ≈ 0 [20]: H(t−λ) ≈ H(t). The unmodelled part H, which includes (G − ḡ)δ, changes little over one sample.
- C3. First-order Taylor; O(Δω², Δδ²) neglected (Sec. 3.2, after [13]).
- C4. Actuator dynamics negligible: 1/τ_a faster than closed-loop bandwidth (after [5]). INDI uses measured δ_0 (Sec. 3.2).
- C5. Acceleration replaced by backward difference of e [25], or ω̇ measured [23]. The PI form needs no acceleration sensor; the INDI form needs ω̇(k−1).
- C6. ḡ constant over one step, and it is the only parameter (Sec. 3.4, Remark 4). K and T_I are then functions of ḡ, t_s, k_P, k_D only.
- C7. Decoupled, diagonal axes (eq. [7] decoupling; diagonal K, T_I, ḡ).
- C8. Hurwitz desired error dynamics (see 8 on the sign of k_P).

**What "equivalent" means here.** The equivalence is an algebraic identity between two control laws written in terms of past signals [22]/[18] and [28]. It does not establish that the two closed loops behave identically for a real, mismatched plant. The paper's only statement on closed-loop behaviour is the nominal simulation (Sec. 4). Stability for discrete TDC is deferred to Chang & Jung (2009) (Sec. 3.4).

## 5. Where the paper says INDI and PI(D) differ

- **Effectiveness coupling.** The PI proportional gain K = (ḡ·t_s)^-1 [29] is not free: it depends on the effectiveness estimate and on the sample time. The paper says PID scheduling "shall be done at K via ḡ" (end of Sec. 3.4).
- **Model dependence.** NDI needs f and G [6]. INDI needs G_0 [14-15] (or ḡ [18]) and measured ω̇ and δ. TDC cancels f through H̄ [19-21]. The PI form needs neither f, G, nor an acceleration sensor [24-28].
- **Self-scheduling.** INDI's G_0 schedules the gain automatically [15]. With constant ḡ this property is lost (Remark 2). The paper proposes scheduling ḡ online (Remark 4, Sec. 5).
- **Measured vs estimated acceleration.** INDI uses ω̇(t−λ) [11a, 21, 23]. The PI form replaces it by a finite difference of the error [25]; the paper does not discuss its noise sensitivity. Sec. 4 assumes "pitch acceleration is available for measurement" (text before [36]).
- **Actuator state.** INDI recursion uses measured δ(t−λ) [15, 18]. The incremental PI [28] recursion is written on the controller's own past output; the paper does not say which signal is used in the PI implementation (see 8).
- **Trim.** PI [26] has a trim term δ_DC from initial conditions; the incremental forms [18, 28] have none.
- **Robustness.** Sec. 1 and Remark 1 call the law robust and model-free. Sec. 3.2 notes that typical INDI laws still depend on G_0, and [16-18] move that dependence into ḡ.
- **Not discussed in the paper:** saturation, anti-windup, rate limits, sensor filtering, discretization error for ω̇ at large t_s.

## 6. Examples and results

- **Fig. 1 (Sec. 3.1):** four-loop structure (position, flight path/airspeed, attitude, rate). The rate loop is the subject of the paper.
- **Plant (Sec. 4, [31a-b], [32a-b]):** second-order longitudinal launcher model at about 6000 m, state x_1 = α, x_2 = q. Coefficients given: b_z(M) = 1.6238M − 6.7240, b_m(M) = 12.0393M − 48.2246. Valid for −10° ≤ α ≤ 10° and 1.8 ≤ M ≤ 2.6. Mach number M is a measured parameter. Aerodynamic functions are "assumed accurately known".
- **Actuator:** K_a = 1, τ_a = 1e−2 s (after [32b]).
- **Design:** rate error z_2 = x_2 − x_2ref [33-34]; desired dynamics ż_2 + k_P2·z_2 = 0 with k_P2 = 50 rad/s [35]; INDI law u = u_0 + ḡ^-1(ν − ẋ_20) [38, 40], ḡ = k_G·ĝ_2 with k_G = 1 [text after 36].
- **Noise:** zero-mean Gaussian, σ = 1e−3 rad/s on the rate measurement (Sec. 4).
- **Mapped PI gains:** K = 100·ĝ_2^-1, T_I = 0.02 s [text after 36]. T_I = 1/50 matches [44]. Paper: "both controllers showing identical closed-loop response as expected".
- **Fig. 2 (Sec. 4):** smooth rate doublets at Mach 2, 0-20 s. Panels: q with q_REF, q_INDI, q_PI and q_INDI − q_PI; α with α_INDI; δ with δ_INDI and δ_INDI − δ_PI. The text says the responses are identical; the difference traces are the only quantitative evidence.
- **[my inference]** K = (ḡ·t_s)^-1 with ḡ = ĝ_2 and K = 100/ĝ_2 imply t_s = 0.01 s (100 Hz). The paper does not state t_s.
- **[my check]** Actuator bandwidth 1/τ_a = 100 rad/s against k_P2 = 50 rad/s. The separation is a factor 2, which is weak against the C4 requirement.
- **Not in the paper:** effectiveness mismatch (ḡ ≠ G), disturbances, saturation, hardware, a separately tuned PID baseline. The PI in Fig. 2 is derived from the INDI, not tuned on its own.

## 7. Implications for comparing INDI against PX4's PID rate controller (my interpretation)

Not verified against PX4 source for this note.

- **Key fact.** Under C1-C8 with ḡ equal to the true effectiveness, INDI rate control is the incremental PI(D) [29, 30]. With a fixed ḡ, the INDI law is itself a fixed-gain PI. Any advantage of INDI over a PID must come from (a) scheduling ḡ, (b) the model-free cancellation of f through H̄ [19-21], or (c) measured actuator-state feedback δ(t−λ) [15].
- **What a fair PID must include to match INDI (under the paper's assumptions):**
  - Same sample time t_s, and P gain K = 1/(ḡ·t_s) with ḡ the same effectiveness estimate INDI uses, rather than a constant K [29].
  - Same integral mapping T_I = 1/k_P, so the integral gain is K/T_I = k_P/(ḡ·t_s). If the PID is written in parallel form, the integral coefficient must be set to this value, not to 1/k_P [26-28, my check].
  - For a D term, K = k_D/(ḡ·t_s) and T_D = 1/k_D [30]. The P gain is then tied to k_D, not to k_P.
  - Same incremental (velocity) structure and the same actuator feedback path, or the difference should be stated.
  - Same filter on the rate and difference path. [25] divides by t_s, so rate noise is amplified (my inference; the paper does not quantify it). Sec. 4 tests noise at sigma = 1e-3 rad/s.
  - Same saturation and anti-windup handling. The paper says nothing here, so any comparison on this point is outside the paper's evidence.
- **[my derivation] Effectiveness mismatch.** Let the true effectiveness be G and the law use ḡ. Under C1-C2, Δω̇ = G·Δδ and Δδ = ḡ^-1(ν − ω̇(t−λ)), so the acceleration error obeys e_k = (1 − G/ḡ)·e_{k−1}. The loop is stable for 0 < G/ḡ < 2, and G/ḡ = 1 is deadbeat. This gives a testable prediction: a fixed-gain PID tuned at ḡ behaves like INDI at fixed ḡ, with effective gain scaled by G/ḡ. An INDI that updates ḡ would keep G/ḡ near 1. The paper gives no closed-loop result for ḡ ≠ G, so this is my derivation, not the paper's.
- **What INDI does that a fixed-gain PID cannot, per the paper:**
  - One scalar per axis (ḡ) carries the scheduling, instead of three gains [Remark 4, end of Sec. 3.4].
  - No aerodynamic model in the law. H̄ [21] estimates the unmodelled part from the past, which is the source of robustness when ε_TDC ≈ 0 (C2). This is a claim about the paper's law, not a measured result.
  - The incremental recursion uses measured δ(t−λ) [15], so actuator-state feedback is built in.
- **Caveat.** With constant ḡ, the INDI-PI pair in Fig. 2 gives no advantage over a PID with the same K and T_I. A comparison that shows a benefit for INDI needs a mismatch or a scheduling test, which the paper does not provide.

## 8. Unverified / unclear

1. Author list: the local text lists "van Ekeren" as second author, not "van Kampen" as in the task brief. The IFAC 2017 venue is not printed in the text; only the arXiv header (v3, 5 Apr 2017) is.
2. [2]: "ω̇ = I^-1 M_B − ω × I ω" is garbled. Read as I^-1(M_B − ω × Iω), consistent with f in [4].
3. [4] and text after it: f and G definitions are garbled. Read as f = I^-1(M_a − ω×Iω), G = I^-1(M_c)_δ.
4. Sec. 3.1, text after [9]: "Hurwitz, i.e., k_Pi < 0". With s + k_Pi, Hurwitz needs k_Pi > 0; [10] and k_P2 = 50 rad/s [35] confirm positive. Treat "< 0" as a sign error.
5. [16] text: ḡ_1 = k_G·I_n and ḡ_2 = diag(k_G1..k_Gn). The subscript labels and the scalar/diagonal distinction are unclear. The paper uses a scalar in Sec. 4.
6. [26]-[28] vs [29]: the parallel form printed in [26] and [28] (integral term with no K and no t_s) does not reproduce [29]. [29] is consistent with the K(e + T_I^-1∫e) form. [43] has the same issue.
7. [30]: T_D printed as "k_D^-1" (split across lines). Read as k_D^-1, which agrees with my check.
8. [30]/derivative term: the ë term and its discretization are not written out. The printed grouping "K·t_s·T_D·ë(k−1) + ė(k−1)" is ambiguous; read as K·t_s·(ė + T_D·ë).
9. [24]: the step ν − ω̇ = ė + k_P·e uses ė = ẏ_d − ω̇ from e = y_d − y, which the paper does not state.
10. [12], [20]: the approximations ε_INDI and ε_TDC are assumed, with no bound on λ or on the variation of f and H.
11. Stability of discrete TDC/INDI is deferred to Chang & Jung (2009). Not checked here.
12. Sec. 4: the simulation does not say how ẋ_20 was obtained (measured noise-free, or differenced from the noisy rate). This matters for the "identical response" claim with σ = 1e−3 rad/s noise.
13. Sec. 4: the sample time t_s is never stated (inferred 0.01 s, see 6).
14. Sec. 4: the input is called u in [32]-[44] but δ in Sec. 3. Read u = δ.
15. Fig. 2: image only in the text extraction. The size of the q_INDI − q_PI and δ_INDI − δ_PI traces is not verified.
16. Sec. 4: "ḡ = k_G·ĝ_2" uses an estimate ĝ_2, but the aerodynamic model is "assumed accurately known", so the example never tests a mismatch.
17. [17]-[18] vs [21]: H_0 is defined as ω̇_0 − ḡ·δ_0 in the text, and H̄ as ω̇(t−λ) − ḡ·δ(t−λ) in [21]. These agree, but the reuse of the H symbol for two quantities should be noted.
18. Sec. 1 and Sec. 3.3 call the law "model-free" and "robust". The paper does not quantify robustness; the only support is the nominal simulation in Sec. 4.
