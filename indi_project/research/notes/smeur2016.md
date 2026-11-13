# Smeur, Chu, de Croon (2016): Adaptive INDI for Attitude Control of MAVs

## 1. Citation

Smeur, E. J. J., Chu, Q., de Croon, G. C. H. E., "Adaptive Incremental Nonlinear Dynamic Inversion for Attitude Control of Micro Air Vehicles", *Journal of Guidance, Control, and Dynamics*, 39(3), 2016.
DOI: 10.2514/1.G001490

Local text used: `indi_project/research/raw/foundations/inaoep_14032018.txt` (plain-text extraction, not the PDF).

## 2. Summary

- INDI measures angular acceleration instead of modelling it; only the control-effectiveness matrices remain as model (Abstract; Sec. I, p.1-2).
- Paper's three claimed contributions: (1) delay-consistent angular acceleration from filtered gyro, (2) adaptive INDI that estimates effectiveness online, (3) propeller momentum included (Abstract; Sec. I).
- Quadrotor model with rotor gyroscopic/momentum term: Eqs. (1)-(8); linearised INDI law Eq. (19), simplified Eq. (21).
- Key trick: the same second-order filter H(s) (Eq. 15; omega_n = 50 rad/s, zeta = 0.55) is applied to the gyro-derived acceleration and to the actuator signal, so inputs and outputs are synchronous (Sec. III, Eq. 16).
- Closed-loop argument (Sec. III.C, Eqs. 22-27): disturbance rejection holds when actuator and filter dynamics are stable.
- Outer loop: PD on attitude/rate error commands angular acceleration (Sec. III.D, Fig. 5). Adaptive part: Sec. IV. Hardware: Parrot Bebop running Paparazzi (Sec. I, V, VI).

## 3. Control law

**Model (Sec. II).** Vehicle Euler equation, Eq. (1): $I_v\dot\Omega = -\Omega\times I_v\Omega + M$. Rotor moment, Eqs. (2)-(4): gyroscopic term $\Omega\times I_r\omega_i$ plus $\dot\omega_{iz}$ term; assumes $\omega_{ix},\omega_{iy}\ll\omega_{iz}$ and neglects $\dot\omega_{ix},\dot\omega_{iy}$ (text after Eq. 3). Rotor moment for all four rotors, Eq. (5). Full vehicle equation, Eq. (6):
$I_v\dot\Omega = -\Omega\times I_v\Omega + M_c(\omega) + M_a(\Omega,v) - M_r(\omega,\dot\omega,\Omega)$.
Control moment (thrust/torque mixing), Eq. (7), with $\omega_i^2$ as the actuator input:
$M_c = B\,[\omega_1^2,\omega_2^2,\omega_3^2,\omega_4^2]^T$, $B=\begin{bmatrix}-bk_1 & bk_1 & bk_1 & -bk_1\\ lk_1 & lk_1 & -lk_1 & -lk_1\\ k_2 & -k_2 & k_2 & -k_2\end{bmatrix}$.
Here $k_1$ = rotor force constant, $k_2$ = rotor moment constant, $b$ = half-width, $l$ = half-length (Nomenclature; Fig. 1).

**Angular acceleration (Eq. 8).** Solving Eq. (6):
$\dot\Omega = F(\Omega,v) + \tfrac12 G_1\omega^2 - T_s G_2\dot\omega - C_\Omega G_3\omega$, with $F(\Omega,v)=I_v^{-1}(M_a-\Omega\times I_v\Omega)$ (text after Eq. 8). Eq. (8) is the non-linear model; $\omega^2$ is element-wise.
- $G_1 = 2I_v^{-1}B$, Eq. (9). Multiplies the rotor-speed-squared thrust/torque.
- $G_2 = I_v^{-1}[\,0;0;\,I_{rzz}(1,-1,1,-1)\,]$ (Eq. 10), i.e. only the yaw row is non-zero. This is the rotor spin-up / reaction-torque term; its $T_s$ placement is garbled (see Sec. 10).
- $G_3$, Eq. (11): gyroscopic coupling of rotor spin with $\Omega_x,\Omega_y$ (rows 1-2 non-zero, row 3 zero).
- $C_\Omega$, Eq. (12): 3x3 matrix in $\Omega_x,\Omega_y$ (layout unclear).
- Eq. (8) is linearised by Taylor expansion (Eq. 13-14). Assumption of time-scale separation (text after Eq. 13): partials w.r.t. $\Omega$ and $v$ neglected, valid only if actuators are fast relative to aerodynamic and precession moments.

**Filtered linearisation (Eqs. 14-18).** Linearised about the filtered state $(\cdot)_f$:
$\dot\Omega \approx \dot\Omega_f + G_1\,\mathrm{diag}(\omega_f)(\omega-\omega_f) - T_sG_2(\dot\omega-\dot\omega_f) - C_{\Omega f}G_3(\omega-\omega_f)$ (Eq. 16; sign of the $G_2$ term reconstructed).
With $\dot\omega \approx (\omega - z^{-1}\omega)/T_s$ (Eq. 17), Eq. (18):
$\dot\Omega = \dot\Omega_f + [G_1\mathrm{diag}(\omega_f) + G_2 - C_{\Omega f}G_3](\omega-\omega_f) - G_2z^{-1}(\omega-\omega_f)$.
The $z^{-1}$ term is the one-sample memory of the actuator; the paper writes the system as $\dot x = f(x)+g(x;u,\dot u)$ (Sec. II, text before Sec. III), i.e. the input enters through its derivative too.

**INDI law (Eq. 19).** Virtual control $\nu$ = desired $\dot\Omega$. Command $\omega_c$, with $\pm$ signs as extracted:
$\omega_c = \omega_f + [G_1\mathrm{diag}(\omega_f)+G_2-C_{\Omega f}G_3]^{\dagger}\big(\nu - \dot\Omega_f \pm G_2z^{-1}(\omega_c-\omega_f)\big)$.
$\dagger$ = Moore-Penrose pseudoinverse (control allocation; text after Eq. 19; Fig. 2). Increment $\tilde\omega = \omega_c-\omega_f$ makes it incremental.

**Simplified law (Eq. 21).** Dropping $G_3$ (about 0.2 % LS error increase) and treating the rotor as linear in $\omega$ instead of quadratic (about 0.9 % increase), Sec. III.A:
$\omega_c = \omega_f + (G_1+G_2)^{\dagger}(\nu - \dot\Omega_f \pm G_2z^{-1}\tilde\omega)$, with $\tilde\omega = \omega_c-\omega_f$.
Sign of the $z^{-1}$ term is reconstructed from Eq. (22), $TF_{\dot\Omega_{err}\to\tilde\omega} = (G_1+G_2-G_2z^{-1})^{\dagger}$.

**Role of the previous actuator state.** $z^{-1}\tilde\omega$ (i.e. $G_2$ coupling to the previous command increment) carries the rotor-acceleration/reaction term into the law; $\omega_f$ is the filtered actuator state. Fig. 2 shows the scheme: $\nu$ in, $\dot\Omega$ out, gyro fed back through the second-order filter $H_z$ and subtracted from $\nu$ to give $\dot\Omega_{err}$; $A_z$ = actuator dynamics (first-order, Sec. III.B).

**Outer loop (Sec. III.D, Fig. 5).** PD on attitude error and rate error gives $\nu$ (gains $K_\eta$, $K_\Omega$); the paper says the controller design depends only on actuator speed $A_z$. Attitude kinematic inversion is replaced by simple angle feedback for small angles.

## 4. Angular acceleration estimation and filtering

**Filter (Sec. III.B, Eq. 15).** Gyro rate is filtered, then differentiated. Second-order low-pass $H(s)=\omega_n^2/(s^2+2\zeta\omega_n s+\omega_n^2)$. Source of the filter: [9] Bacon, Ostroff and Joshi (2001) per the reference list; the intro attributes the second-order filter to Bacon and Ostroff (Sec. I). Values for the control loop: $\omega_n=50$ rad/s (about 8 Hz), $\zeta=0.55$, "satisfactory results" (Sec. III.B, text after Eq. 15). Order 2. Butterworth or other low-pass filters are said to be possible (Sec. III.B). No discrete-time implementation of $H_z$ is given in the text read.

**Same filter on the actuator signal (Sec. III.B, Eq. 16; Sec. III.C).** Every term evaluated at the operating point $(\cdot)_0$ in the Taylor expansion is re-evaluated at $(\cdot)_f$, so $\omega$ is filtered too. The paper says this makes $\dot\Omega_f$, $\omega_f$ and the other terms synchronous (Sec. III.B, text after Eq. 16). Stated consequence (Sec. III.C, text after Eq. 26): applying $H_z$ to the input as well means "a lot of terms cancel, and all that remains is the actuator dynamics." Ablation: an INDI variant using $\omega_0$ instead of $\omega_f$ in the increment is expected not to fly well (Sec. V.A design text, extraction lines 485-498; observed result in Sec. VI.A, Fig. 11).

**Actuator state.** Preferred: actuator feedback (rotor speed) available (Fig. 2). Otherwise $\omega_0$ is estimated with a model of the actuator dynamics $\hat A_z$ (Fig. 4, Sec. III.B). Actuator model: first-order dynamics $A_z$ (Sec. III.B, text after Eq. 19), same $A_z$ for all motors (Sec. III.C). Paper says the actuator is in most cases first- or second-order (Sec. III.C). Time-constant value: not found in the text read (Sec. 10).

**Delay assumptions.** Discrete derivative $\dot\omega\approx(\omega-z^{-1}\omega)/T_s$, Eq. (17): one-sample difference. Controller and gyro loop at 512 Hz (Sec. V intro). Delay is compensated by the filtered linearisation (Eqs. 16-18), not by prediction. Predictive filtering [8] is rejected because it needs extra modelling and cannot predict disturbances (Sec. I).

**Filter for the adaptive estimator (Sec. IV, text after Eq. 28).** Same second-order form, $\omega_n=25$ rad/s, $\zeta=0.55$, used on $\Delta\dot\Omega_f$ and $\Delta\omega_f$. Reason: differentiation amplifies high frequencies. The estimation filter "can be different from the filtering for the actual control" (Sec. IV, text after Eq. 29).

## 5. Adaptive effectiveness

**Problem (Sec. IV intro).** $G_1,G_2$ depend on inertia, airspeed, battery voltage and actuator failure (Sec. IV intro). Without an estimate the vehicle may crash before adaptation converges (Sec. IV, extraction lines 518-531).

**Estimator (Eqs. 28-29).** Least mean squares (LMS) adaptive filter [15]. Eq. (28) is garbled in the extraction (Sec. 10). Best reading: $G_k = G_{k-1} - \mu_1\,e_k\,x_k^{T} - \mu_2 G_{k-1}$, with regressor $x_k$ built from $\mathrm{diag}(\omega_f)\Delta\omega_f$ and $-\Delta\omega_f$ (the same stack as Eq. 20), and error $e_k = \Delta\dot\Omega_f - G_{k-1}x_k$ (Sec. IV text). Eq. (29): the adapted matrix is $G=[G_1\ G_2]$, the effectiveness including both $G_1$ and $G_2$ (Sec. IV text).
- Inputs: $\Delta\omega_f$ and $\Delta\dot\Omega_f$, both filtered (Sec. IV, Eq. 28).
- $\mu_1$: diagonal, one entry per input. $\mu_2$: diagonal, one entry per axis, because the axes have different signal-to-noise (Sec. IV, extraction lines 476-510).
- Learning rate: larger $\mu$ gives faster convergence, too large loses stability. Theoretical limit depends on the autocorrelation matrix of the filter input [15]; in practice stability is lost before that limit, so tuning is needed (Sec. IV, extraction lines 518-531). No numeric $\mu$ values read yet.
- Excitation: no change in input means no change in $G$; more excitation gives faster adaptation (Sec. IV, extraction lines 476-510). LMS preferred to finite-horizon RLS, which "forgets" data outside the horizon.
- Initial value: an approximate $G$ is provided before takeoff; the system then tunes itself. The paper says this is the only prior knowledge needed (Sec. IV, extraction lines 518-531).

**What it converges to.** Physical $G_1,G_2$ of the current configuration: in the bumper experiment, the matrices are expected to "converge to their original state" after bumper removal (Sec. V.C text). Evidence is experimental only; no analytical convergence result is in the text read.

## 6. Saturation, allocation, yaw, practical details

- **Saturation.** No actuator saturation, rate limit or anti-windup handling is described in the text read. The increment $\tilde\omega$ is unbounded in the extracted equations (Eqs. 19-21).
- **Allocation.** Control allocation is the Moore-Penrose pseudoinverse $\dagger$ of $G_1\mathrm{diag}(\omega_f)+G_2-C_{\Omega f}G_3$ (Eq. 19) or of $G_1+G_2$ (Eq. 21) (Sec. III.A-B). The paper notes that with $G_2=0$ the pseudoinverse gain becomes very large (Sec. VI.D text, after Eq. 21 discussion in Sec. V.D).
- **Thrust / 4th DOF.** Vertical acceleration is not inverted by INDI. Pilot sets average thrust and attitude over Wi-Fi; a separate controller scales the average motor input to the pilot's command after the INDI increment (Sec. III.E, Altitude Control; Sec. V intro).
- **Arming / engagement.** INDI is engaged when the pilot's thrust command exceeds idle. The vehicle then stays on the floor until lift is produced; adaptation diverges briefly during takeoff/landing from floor contact (Sec. VI.C text). Arming logic: not described.
- **Yaw and rotor spin-up.** $G_2$ (Eq. 10) carries rotor spin-up torque; the paper states it is "very significant" (Sec. VI.D, Fig. 24). Propeller angular momentum is included (Sec. I, contribution 3). Yaw is controlled through the same increment, with no separate yaw law.
- **Outer loop.** PD on attitude and rate error with gains $K_\eta$, $K_\Omega$ (Sec. III.D, Fig. 5). Gains and numeric values not found in the text read.
- **Initialisation.** Approximate $G_1,G_2$ are required before takeoff (Sec. IV text, extraction lines 518-523). Filter and adaptation constants are given as $\omega_n$, $\zeta$, $\mu_1$, $\mu_2$ without numeric $\mu$ values.
- **Compute.** Control loop at 512 Hz, all computation on the vehicle, pilot commands over Wi-Fi (Sec. V intro).

## 7. Experimental setup and results

**Vehicle and setup (Sec. V intro; Fig. 1, 6, 7).** Parrot Bebop quadrotor, 396.2 g, bumpers 12 g each (Sec. V intro). Paparazzi autopilot, 512 Hz sensor and control loops. Pilot sets attitude reference and average thrust; INDI and adaptation run onboard. Four experiments (Sec. V intro): performance, disturbance rejection, adaptation, yaw.

**Performance test (Sec. V.A).** Roll doublet, amplitude 30 deg, half-period 0.25 s; roll only. Compared with a manually tuned PID; INDI run without adaptation (Fig. 8-10).
- Fig. 8: roll angular acceleration vs reference and vs reference filtered by actuator model; actual tracks the expected $\dot p_{refA}$ (Eq. 26), with lag. Onboard filtered estimate is "significantly delayed" (Sec. VI.A text).
- Fig. 9: INDI roll reaches reference in 0.2 s, very small overshoot.
- Fig. 10: PID similar rise time and overshoot; integral action degrades dynamics; paper says INDI "marginally improves" responsiveness (Sec. VI.A text after Fig. 10).
- Fig. 11: INDI without filter-delay compensation oscillates severely; doublet not flown for safety (Sec. VI.A). Paper concludes delay compensation is "crucial".

**Disturbance rejection (Sec. V.B, VI.B; Fig. 6, 12-15).** 42.5 g added to a nose container about 11 cm ahead of CG, giving a persistent pitch-moment step. Weight placed by hand, so the input is a step plus a delta pulse (Sec. VI.B text).
- Fig. 12-13: INDI reference re-acquired about 0.1 s after losing track; pitch returns to zero with no steady-state error, back at zero after 0.3 s.
- Fig. 14: motor-speed difference front vs rear changes by an average 578 rpm between [12.6, 13.0] s and [13.4, 13.8] s (Sec. VI.B; formula garbled).
- Fig. 15: PID takes about 1.5 s to return to zero pitch, "approximately five times longer" (Sec. VI.B).

**Adaptation (Sec. V.C, VI.C; Fig. 16-23).** Bumpers add mass far from CG and change $G_1,G_2$. Flights: [8, 54] s and [66, 125] s, landed and bumpers removed in between.
- Fig. 16: bumpers on, $G$ from no-bumper model: higher inertia, oscillation, reducible by lowering $K_\eta,K_\Omega$.
- Fig. 17: bumpers off, $G$ from bumper model: effectiveness higher than modelled, fast oscillation not removable by gains (Sec. VI.C text).
- Fig. 18-21: online evolution of rows of $G_1$ (roll, pitch, yaw) and third row of $G_2$. Large change in yaw row between flights (Fig. 20); roll row changes (Fig. 18). Converged values "stable with little noise".
- Fig. 22-23: with adaptation, doublet performance matches nominal "regardless of whether the bumpers are equipped", interpreted as robustness (Sec. VI.C).
- Paper notes actuators differ from each other (Fig. 20 text), contrary to equal-actuator assumption.

**Yaw (Sec. V.D, VI.D; Fig. 24-27).** Yaw doublet 5 deg amplitude, 1 s period (0.5 s each sign). Compared with manually tuned PID for fast rise and low overshoot.
- Fig. 24: change in yaw angular acceleration vs model prediction (Eq. 21): "a close match". Prediction without $G_2$ is far off: spin-up torque "very significant".
- Zero-$G_2$ flight: strong oscillation, takeoff not possible (Sec. VI.D). Flight without $G_2$ possible only with inflated yaw effectiveness; "severe performance penalty" (Fig. 25).
- Fig. 26 vs 27: with $G_2$, INDI yaw has "faster rise time and less overshoot" than PID (Sec. VI.D text, after Fig. 26).

**Comparison scope.** Only a manually tuned PID is used. No other controller, no NDI, no quantitative metrics (RMS, settling time tables). Number of repetitions and flights per test not stated. No tables found in the text.

## 8. Claimed limitations and assumptions

- **Time-scale separation.** Partials w.r.t. $\Omega$ and $v$ are neglected; holds only if actuators are fast relative to aerodynamic and precession moments (Sec. III.A, text after Eq. 13).
- **Taylor expansion.** Higher-order terms neglected (Sec. III.A, text before Eq. 13).
- **Rotor gyroscopics.** Rotors flat in z ($I_{rxz}=I_{ryz}=0$); $\omega_{ix},\omega_{iy}\ll\omega_{iz}$ and $\dot\omega_{ix},\dot\omega_{iy}$ negligible (Sec. II text after Eq. 3).
- **Simplifications.** $G_3$ dropped and rotor treated as linear: LS error rises about 0.2 % and 0.9 % on one "typical dataset" (Sec. III.A). Only one dataset described.
- **Actuators.** First-order dynamics assumed; all motors share $A_z$ (Sec. III.B-C). Paper says Sec. VI shows they do not, which the text treats as adaptive benefit.
- **Effectiveness.** Coarse initial $G$ required before takeoff; LMS stability depends on tuning (Sec. IV text).
- **Kinematics.** Attitude kinematics inversion replaced by angle feedback, valid for small angles (Sec. III.D).
- **Outer loop.** PD; INDI inner loop response "simply the actuator dynamics" (Sec. V.A text). Knowledge of actuator dynamics needed only for high-performance outer loop (Sec. VII).
- **Experimental scope.** One airframe (Bebop), roll doublet, pitch step, yaw doublet; pitch and roll not separately tested (Sec. V.A text: "no fundamental difference").
- **Not claimed.** Convergence proof, robustness margins, saturation behaviour, behaviour under strong wind (wind not tested; step weight used instead).

## 9. Implications for a PX4 implementation (interpretation, not the paper's claim)

Interpretation by the note author, not the paper's statement.
- Filter matching: any INDI increment in PX4 must apply the same $H_z$ to the actuator signal used in $\omega_f$ (Eq. 16-18). Without it the paper's own ablation oscillates (Fig. 11). The PX4 rate-loop low-pass filters (gyro, D-term) would need to be mirrored in the INDI path.
- Actuator feedback: PX4 does not necessarily have rotor-speed feedback on all targets. If absent, the paper's $\hat A_z$ model (Fig. 4) must be used, with a time constant that the text does not give (Sec. 10).
- Yaw: $G_2$ (rotor spin-up) matters; without it the paper's experiments show failure or a penalty. Needs rotor inertia $I_{rzz}$ and the motor configuration in the parameter set.
- Allocation: the paper's pseudoinverse on a 3x4 $G$ is not the same as PX4's matrix-mixer. Saturation and desaturation are unaddressed in the paper, so PX4's control-allocation saturation path needs its own design.
- Adaptation: LMS on $\Delta\omega_f$ and $\Delta\dot\Omega_f$ would need guards for low excitation and for ground contact (Sec. VI.C). Adaptation on the ground was not tested.
- Baseline: the INDI vs PID evidence is qualitative (one doublet per axis, one step). A PX4 comparison should use fixed metrics and repetitions.
- Hardware transfer: Bebop with Paparazzi, 512 Hz. PX4 loop rates and gyro sampling differ; $T_s$, $\omega_n$ and $\zeta$ must be rechecked.

## 10. Unverified / unclear

1. Eq. (2)/(3): rotor momentum equation partly garbled; exact form of $M_{ri}$ and sign of $\Omega\times I_r\omega_i$ taken from the pattern.
2. Eq. (5): matrix layout legible but signs of some entries assumed from the pattern.
3. Eq. (9): $G_1 = 2I_v^{-1}B$ read from "2I_v^-1" with the matrix; consistent with the "1/2 G_1 omega^2" in Eq. (8). Not stated explicitly.
4. Eq. (10): position of $T_s$ in $G_2$ unclear (inside or outside); Eq. (8) writes $T_s G_2\dot\omega$.
5. Eq. (8), (16), (18): sign of the $G_2$ term partly lost in extraction ("" glyph).
6. Eq. (12): layout of $C_\Omega$ (entries of $\Omega_x$, $\Omega_y$) unclear.
7. Eq. (19), (21): sign of the $z^{-1}$ term not legible; $+$ used, reconstructed from Eq. (22).
8. Eq. (20): regressor stack and signs partly legible.
9. Eqs. (22)-(27): transfer-function algebra garbled; only the stated conclusions (disturbance rejection, $A_zH_zz^{-1}\to 1$) are recorded.
10. Eq. (28): LMS update garbled; $\mu_2$ leakage-term reading is a guess.
11. Eq. (29): $G=[G_1\ G_2]$ read, but exact stacking not verified.
12. Section numbering: subsection headers (IV.A/B, V.A-D, VI.A-D) are partly lost; mapping inferred from reading order and cross-references. Paragraph citations use extraction line numbers in those spots.
13. Actuator time constant: not found in the text read. Figures may hold it.
14. No numeric values for $k_1,k_2,b,l,I_v,I_r$, $K_\eta,K_\Omega$, $\mu_1,\mu_2$ in the text read.
15. Fig. 14 formula garbled ("$\omega_1+\omega_2-\omega_3-\omega_4$ over 4" read from pattern).
16. Figure contents (Fig. 8-27) are not in text; only the authors' text descriptions are recorded.
17. Page numbers are not reliable from extraction; citations use section, equation and figure numbers.
18. Quoted claims (e.g. "0.2 %", "578 rpm") not checked against the figures.
