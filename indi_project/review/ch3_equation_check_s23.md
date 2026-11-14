# Chapter 3 equation check against source PDFs (session 23)

Scope: the `[TO VERIFY against PDF]` markers in `report/03_theory.md` (line 5 skipped, it is the explanatory sentence).
Source PDFs: `research/raw/foundations/inaoep_14032018.pdf` (Smeur, Chu, de Croon 2016, JGCD 39(3); title page confirms; the note `research/notes/smeur2016.md` cites the local `.txt` of this file), `research/raw/foundations/arxiv_1701.08981.pdf` (Acquatella et al. 2017), `research/raw/robustness/wang_pure.pdf` (Wang et al. 2019).
Page numbers below are PDF page indices as rendered by the Read tool.

## line 15

Paper key: smeur2016. Equations: Eqs. (2)-(5) (rotor angular-momentum model), with Eq. (6) for the full vehicle equation.

Report (sentence carrying the marker): "where $\varpi_i$ is the speed of rotor $i$, $M_c$ the control moment produced by the rotors, $M_a$ the aerodynamic moment (drag, gusts, any offset of the centre of mass) and $M_r$ the moment due to rotor angular momentum. The note on smeur2016 flags the exact form of the rotor-momentum equations (Eqs. 2-5) as partly garbled in the extraction, so only the structure is used here `[TO VERIFY against PDF]`."

PDF (pages 2 of inaoep_14032018.pdf):
- Eq. (2): $I_{r_i}\dot\omega_i + \Omega\times I_{r}\omega_i = M_{r_i}$, with $I_{r_{xz}}=I_{r_{yz}}=0$ (rotors flat in z).
- Eq. (4): $M_{r_i} = \begin{bmatrix} I_{r_{zz}}\Omega_y\omega_{i_z} \\ -I_{r_{zz}}\Omega_x\omega_{i_z} \\ I_{r_{zz}}\dot\omega_{i_z}\end{bmatrix}$ (read clearly).
- Eq. (5): $M_r = \sum_i (-1)^{i+1} M_{r_i}$ written as $M_r = \begin{bmatrix}0&0&0&0\\0&0&0&0\\I_{r_{zz}}&-I_{r_{zz}}&I_{r_{zz}}&-I_{r_{zz}}\end{bmatrix}\dot\omega + \begin{bmatrix}I_{r_{zz}}\Omega_y&-I_{r_{zz}}\Omega_y&I_{r_{zz}}\Omega_y&-I_{r_{zz}}\Omega_y\\-I_{r_{zz}}\Omega_x&I_{r_{zz}}\Omega_x&-I_{r_{zz}}\Omega_x&I_{r_{zz}}\Omega_x\\0&0&0&0\end{bmatrix}\omega$, with $\omega=[\omega_1,\dots,\omega_4]^T$ (rotor speeds, not squared).
- Eq. (6): $I_v\dot\Omega + \Omega\times I_v\Omega = M_c(\omega) + M_a(\Omega,v) - M_r(\omega,\dot\omega,\Omega)$. In Eq. (6) it enters as $-M_r(\omega,\dot\omega,\Omega)$.
- Eqs. (2) and (3) are only partly legible at page-image resolution; I did not transcribe them term by term.

Verdict: MATCH (structure only, as the report says). $M_r$ depends on the rotor speeds, their rates and $\Omega$, and in the paper it is the yaw-axis gyroscopic/spin-up term plus $\Omega_{x,y}$ cross terms. Eqs. (4)-(5) are legible and their signs agree with the note's reconstruction, so the note's "signs assumed" caveat is now resolved for Eq. (5). The report still avoids the exact coefficients, which is consistent with the sentence.

## line 17

Paper key: smeur2016, Eq. (7).

Report: "Each rotor produces a thrust $k_1\varpi_i^2$ and a reaction (drag) torque $k_2\varpi_i^2$ about its axis ... [smeur2016, Eq. 7: $M_c = B\,[\varpi_1^2,\dots,\varpi_4^2]^T$ with $B$ built from $bk_1$, $lk_1$ and $k_2$; the signs of some entries were assumed from the pattern in the note `[TO VERIFY against PDF]`]."

PDF (page 3 of inaoep_14032018.pdf, Eq. 7):
$M_c = \begin{bmatrix} bk_1(-\omega_1^2+\omega_2^2+\omega_3^2-\omega_4^2) \\ lk_1(\omega_1^2+\omega_2^2-\omega_3^2-\omega_4^2) \\ k_2(\omega_1^2-\omega_2^2+\omega_3^2-\omega_4^2)\end{bmatrix} = \begin{bmatrix}-bk_1 & bk_1 & bk_1 & -bk_1\\ lk_1 & lk_1 & -lk_1 & -lk_1\\ k_2 & -k_2 & k_2 & -k_2\end{bmatrix}\omega^2$

Verdict: MATCH. The report's $B$ (row 1 $[-bk_1, bk_1, bk_1, -bk_1]$, row 2 $[lk_1, lk_1, -lk_1, -lk_1]$, row 3 $[k_2, -k_2, k_2, -k_2]$) is identical to the PDF's, including all signs. The "signs assumed" caveat is resolved.

## line 25

Paper key: smeur2016, Eq. (9) (and Eq. (8) for the $\tfrac12 G_1\omega^2$ term).

Report: "Smeur et al. take the rotor speed squared as input and obtain $G_1 = 2 I_v^{-1} B$ [smeur2016, Eq. 9; read from the extraction, "not stated explicitly" in the note `[TO VERIFY against PDF]`]."

PDF (page 3, Eq. 9): $G_1 = 2I_v^{-1}\begin{bmatrix}-bk_1&bk_1&bk_1&-bk_1\\lk_1&lk_1&-lk_1&-lk_1\\k_2&-k_2&k_2&-k_2\end{bmatrix}$, i.e. $G_1 = 2I_v^{-1}B$ with the $B$ of Eq. (7). Eq. (8) is $\dot\Omega = F(\Omega,v) + \tfrac12 G_1\omega^2 - T_sG_2\dot\omega - C(\Omega)G_3\omega$, so the factor 2 is the one the report states.

Verdict: MATCH. The equation is explicit in the PDF, so the note's "not stated explicitly" is superseded. The report's $G_1 = 2I_v^{-1}B$ is correct.

## line 27

Paper key: smeur2016, Eq. (10) (and the $T_s$ factor in Eq. (8)).

Report: "Smeur et al. write the corresponding effectiveness $G_2 = I_v^{-1}[0;0;I_{rzz}(1,-1,1,-1)]$, non-zero only in the yaw row [smeur2016, Eq. 10; the placement of $T_s$ in this expression is unclear in the extraction `[TO VERIFY against PDF]`]."

PDF (page 3, Eq. 10): $G_2 = I_v^{-1}T_s^{-1}\begin{bmatrix}0&0&0&0\\0&0&0&0\\I_{r_{zz}}&-I_{r_{zz}}&I_{r_{zz}}&-I_{r_{zz}}\end{bmatrix}$.
Eq. (8) (page 3): $\dot\Omega = F(\Omega,v) + \tfrac12G_1\omega^2 - T_sG_2\dot\omega - C(\Omega)G_3\omega$, with "the sample time $T_s$ is introduced to ease future calculations".
Eq. (14) and (16) keep the same product $T_sG_2(\dot\omega-\dot\omega_0)$.

Verdict: MISMATCH. The PDF puts $T_s^{-1}$ inside $G_2$ (Eq. 10), so the paper's $G_2$ is $I_v^{-1}T_s^{-1}[\dots]$, not $I_v^{-1}[\dots]$. The $T_s$ in Eq. (8) cancels it, so the physical term in Eq. (8) is $-I_v^{-1}[0;0;I_{r_{zz}}(1,-1,1,-1)]\dot\omega$. The report's expression is therefore the paper's product $T_sG_2$, not $G_2$. The report's "$G_2 = I_v^{-1}[\dots]$" should either carry the $T_s^{-1}$ (to match Eq. 10) or be written as $T_sG_2 = I_v^{-1}[\dots]$ with the paper's Eq. (8) convention. The $[0;0;I_{r_{zz}}(1,-1,1,-1)]$ entries and the yaw-row-only structure match. Sign: Eq. (8) carries a minus sign on the $G_2\dot\omega$ term, which the report does not state here.

## line 31

Paper key: acquatella2017 (`research/raw/foundations/arxiv_1701.08981.pdf`), Eq. (4), with the definitions it uses (Eq. 3 and text after Eq. 4). Page 2.

Report: "$\dot\omega = f(\omega, v) + G(\omega)\,u$ [acquatella2017, Eq. 4; the definitions of $f$ and $G$ are garbled in the extraction and were read as $f = I^{-1}(M_a - \omega\times I\omega)$, $G = I^{-1}(M_c)_u$ `[TO VERIFY against PDF]`]."

PDF (page 2):
- Eq. (4): $\dot\omega = f(\omega) + G(\omega)\delta$, with $f(\omega) = I^{-1}(M_a - \omega\times I\omega)$ and $G(\omega) = I^{-1}(M_c)_\delta$.
- Eq. (3): $M_B = M_a + M_c = M_a + (M_c)_\delta\,\delta$, with $M_a = [L_a, M_a, N_a]^T$, $M_c = [L_c, M_c, N_c]^T$, $\delta = [\delta_a,\delta_e,\delta_r]^T$ (aileron, elevator, rudder). $\omega = [p,q,r]^T$, $I$ the inertia matrix with $I_{xz}$ terms (Eq. 1-2).

Verdict: MATCH, with notation differences only. (i) The paper's input is $\delta$ (control-surface deflections), the report's $u$. (ii) The paper writes $f$ as a function of $\omega$ alone; $M_a$ carries the aerodynamic dependence on the airspeed/state implicitly, so the report's $f(\omega, v)$ is a reasonable extension but not the paper's argument list. The bracketed definitions of $f$ and $G$ in the report are exactly those printed in the PDF. The note's "garbled" caveat is resolved.

## line 68

Paper key: acquatella2017, Eqs. (26)-(30). Pages 4 (PI and PID forms; Eqs. 26-30 are on this page).

Report: "Acquatella et al. show that with $G_1$ replaced by a fixed $\bar g$, the law is algebraically an incremental PI(D) with $K=(\bar g\,t_s)^{-1}$ and $T_I = k_P^{-1}$ [acquatella2017, Eqs. 29-30; the printed parallel-form equations 26 and 28 are inconsistent with 29, see the note `[TO VERIFY against PDF]`]."

PDF (page 4):
- Eq. (26): $\delta(t) = K e(t) + T_I^{-1}\int_0^t e(\sigma)\,d\sigma + \delta_{DC}$.
- Eq. (27): discrete parallel PI, $\delta(k) = K\big(e(k-1) + T_I^{-1}\sum_{i=0}^{k-1} t_s e(i)\big) + \delta_{DC}$.
- Eq. (28): incremental PI, $\delta(k) = \delta(k-1) + K\,t_s\big(\dot e(k-1) + T_I^{-1} e(k-1)\big)$ (the bracket is what I read at page-image resolution; the text extraction drops it).
- Eq. (29): $K = (\bar g\cdot t_s)^{-1}$, $T_I = k_P^{-1}$ (first-order error dynamics $\dot e + k_P e = 0$, Eq. 10).
- Eq. (30): for second-order error dynamics $\ddot e + k_D\dot e + k_Pe = 0$: $K = k_D(\bar g\,t_s)^{-1}$, $T_I = k_D k_P^{-1}$, $T_D = k_D^{-1}$.
- Eq. (24) (page 4, incremental TDC form): $\delta(k) = \delta(k-1) + \bar g^{-1}[\dot e(k-1) + k_P e(k-1)]$.

Verdict: MATCH for the first-order case. Eq. (29) gives exactly $K=(\bar g t_s)^{-1}$ and $T_I = k_P^{-1}$, as the report says. The report's citation "Eqs. 29-30" should be "Eq. 29" for these two values: Eq. (30) (second-order / PID error dynamics) gives different $K$ and $T_I$ scaled by $k_D$, so including it without that qualifier is misleading. On the note's claim that Eqs. 26 and 28 are inconsistent with 29: as read on this page, Eq. (28) with the bracket reduces to Eq. (24) once Eq. (29) is substituted ($Kt_s = \bar g^{-1}$, $T_I^{-1}=k_P$). I could not confirm an inconsistency from the page image; the note's concern may come from the text extraction dropping the bracket. Recommend the report drop that clause or re-check Eq. (28) at higher zoom.

## line 51

Paper key: wang2019 (`research/raw/robustness/wang_pure.pdf`), Eqs. (10)-(13), with Eq. (11) for $\delta$ and Eq. (12) for the incremental law. Pages 4 (Eqs. 10-13) and 5 (Theorem 1 and the Remark on p. 1119).

Report: "They keep the dropped terms as a perturbation $\delta(z;\Delta t)$ of the closed loop, $y^\rho = \nu + \delta(z;\Delta t)$ [wang2019, Eq. 13, reconstructed in the note `[TO VERIFY against PDF]`]."

PDF (page 4):
- Eq. (10): $y^{(\rho)} = y_0^{(\rho)} + B(x_0)\Delta u + \delta(z,\Delta t)$, with Eq. (11): $\delta(z,\Delta t) = \Big[\frac{\partial[\alpha(x)+B(x)u]}{\partial x}\Big|_0\Delta x + \mathcal O(\Delta x^2)\Big]_{x=T^{-1}(z)}$.
- Eq. (12): $\Delta u = \mathcal B^{-1}(x_0)(\nu - y_0^{(\rho)})$.
- Eq. (13): $\dot\eta = f_0(\eta,\xi)$, $\dot\xi = A_c\xi + B_c[\nu + \delta(z,\Delta t)]$, $y = C_c\xi$.
- Text after Eq. (13): "which is consistent with Eq. (9), except for the perturbation term $\delta(z,\Delta t)$."
- Remark after Eq. (13) on p. 1119 (page 5 of PDF) and Theorem 1 on p. 1119: the closed loop is ultimately bounded for $\|\delta(z,\Delta t)\|_2\le\bar\delta_z$, with $\|\delta\|\to 0$ as $\Delta t\to 0$ (Eq. 28).

Verdict: MATCH, with a presentation caveat. The printed Eq. (13) has the perturbation inside the input channel as $\dot\xi = A_c\xi + B_c[\nu+\delta(z,\Delta t)]$, and $y^{(\rho)} = \nu + \delta(z,\Delta t)$ follows from Eq. (10) with Eq. (12) substituted. The report's shorthand is therefore correct, but it is not printed in the paper in that exact form, so it should cite "Eqs. (10)-(13)" (or say "from Eqs. 10 and 12") rather than "Eq. 13" alone. The $\delta$ definition in Eq. (11) (Jacobian times $\Delta x$, evaluated at $x=T^{-1}(z)$) is the point of the "dropped terms" statement, and it matches the report's usage. The quote "is not mathematically rigorous and is especially deficient for unstable nonlinear plants" is on p. 1119 as the report says.

## line 144

Paper key: smeur2016 (`research/raw/foundations/inaoep_14032018.pdf`), Eqs. (22)-(27) and the text of Sec. III.C (pages 4-5).

Report (the marker sentence): "...the first-order response of section 5.2.2. In general the loop transfer function is $L = KA/s$ ... The disturbance enters through $1 - AH$. Both $A$ and $H$ are unity at DC ... This is the quantitative version of the qualitative claim of Smeur et al. that "disturbance rejection holds when actuator and filter dynamics are stable" [smeur2016, Sec. III.C; the transfer-function algebra of Eqs. 22-27 is garbled in the extraction and was not used `[TO VERIFY against PDF]`]."

PDF:
- Eq. (22) (page 4): $\tilde\omega = (G_1+G_2)^+\dot\Omega_{err} + (G_1+G_2)^+G_2z^{-1}\tilde\omega$, which gives $TF_{\dot\Omega_{err}\to\tilde\omega}(z) = (G_1+G_2-G_2z^{-1})^{+}$. The superscript is a pseudoinverse "+", not "-1" as the note's reconstruction says.
- Eq. (24) (page 5): $TF_{\omega\to\dot\Omega}(z) = G_1 + \tfrac{z-1}{z}G_2 = G_1+G_2-G_2z^{-1}$.
- Eq. (25): open loop $TF_{\dot\Omega_{err}\to\dot\Omega}(z) = (G_1+G_2-G_2z^{-1})\,I\,(1-A(z)H(z)z^{-1})^{-1}A(z)$ (as read).
- Eq. (26): $TF_{\nu\to\dot\Omega}(z) = I\,A(z)$. The text says the closed loop from $\nu$ to the angular acceleration "is, in fact, the actuator dynamics $A(z)$".
- Eq. (27): $TF_{d\to\dot\Omega}(z) = I\,(1 - A(z)H(z)z^{-1})$, with $A(z)H(z)z^{-1}$ (the one-sample delay is in the term).
- Text after Eq. (27) (page 5): "disturbances in the angular acceleration are rejected as long as the actuator dynamics and the designed filter are stable."
- The paper defines $H(z)=IH(z)$ and $A(z)=IA(z)$ (page 5), with all actuators sharing the same dynamics.

Verdict: MISMATCH, on three points.
1. Quotation. The report puts "disturbance rejection holds when actuator and filter dynamics are stable" in quotation marks attributed to Smeur et al. This is a paraphrase, not the paper's wording. The verbatim sentence is "disturbances in the angular acceleration are rejected as long as the actuator dynamics and the designed filter are stable" (Sec. III.C, after Eq. 27). Either quote that verbatim or drop the quotation marks.
2. Disturbance term. The paper's disturbance transfer function is $I(1-A(z)H(z)z^{-1})$, with the $z^{-1}$. The report's "$1-AH$" drops the delay. This is acceptable only if the report states it is a continuous-time shorthand (it does use $L = KA/s$, so the shorthand is consistent), but the text should say so.
3. "Not used". The report says Eqs. 22-27 "was not used", but its $1-AH$ statement is taken from Eq. (27), so Eq. (27) is used. The sentence should say Eq. (27) was used and Eqs. (22)-(25) were not.

CANNOT CHECK (not in the paper): the report's $\omega/\omega_{sp}=K/(s+K)$ with $A=H=1$ and the loop $L=KA/s$ are the report's own continuous-time reduction. The paper gives no $K/(s+K)$ result, and its Eq. (26) concludes that the $\nu\to\dot\Omega$ closed loop is $A(z)$ only, which is a different transfer function. The statement "both $A$ and $H$ are unity at DC, so a constant disturbance has no steady-state effect" is consistent with Eq. (27) at $z=1$, but the paper does not state it.

Other note items checked on the way: Eqs. (24)-(27) match the note's reconstruction; the Eq. (22) superscript is the only correction.

## Summary of markers

| line | paper, eq | verdict |
|---|---|---|
| 15 | smeur2016, Eqs. 2-5 (structure) | MATCH (structure only) |
| 17 | smeur2016, Eq. 7 | MATCH |
| 25 | smeur2016, Eq. 9 | MATCH |
| 27 | smeur2016, Eq. 10 (and Eq. 8) | MISMATCH: paper's $G_2 = I_v^{-1}T_s^{-1}[\dots]$; report omits $T_s^{-1}$ |
| 31 | acquatella2017, Eq. 4 | MATCH (notation: $\delta$ for $u$, $f(\omega)$) |
| 51 | wang2019, Eqs. 10-13 | MATCH (shorthand; cite Eqs. 10-13, not 13 alone) |
| 68 | acquatella2017, Eqs. 29-30 | MATCH for Eq. 29; Eq. 30 changes $K$, $T_I$ for second-order case; note's "inconsistency" not seen |
| 144 | smeur2016, Eqs. 22-27, Sec. III.C | MISMATCH: quote is a paraphrase; $1-AH$ omits $z^{-1}$; Eq. 27 was used |
