# 3. Theoretical background

This chapter states the model and the control law on which the rest of the report rests. It uses the notation of section 5.2.1, so that chapter 5 can refer back to it: $\omega$ and $\omega_{sp}$ are the measured and desired body rates, $\nu$ the virtual control (desired angular acceleration), $a_f$ the filtered measured angular acceleration, $\tau$ a normalised torque (dimensionless, 1 = the allocator's reference maximum for that axis), $\tau_f$ the filtered modelled torque, $H$ the filter chain, $G_1$ and $G_2$ the control effectiveness and the yaw spin-up term, $K$ the rate-tracking bandwidth, $T_a$ the actuator time constant (`MC_INDI_ACT_TC`) and $T_s$ the cycle time. All quantities are per body axis. Where a symbol is needed that chapter 5 does not define, it is introduced here.

Equations taken from the literature were read from text extractions of the papers, not from page images. Where an equation used below is marked as reconstructed in the reading notes, the marker `[TO VERIFY against PDF]` is kept. Statements that the notes do not support are marked `[UNSOURCED]`.

## 3.1 Rigid-body rotational dynamics of a multirotor

For a rigid vehicle with inertia tensor $I_v$ and body rate $\Omega$, the Euler equation is $I_v\dot\Omega = -\Omega\times I_v\Omega + M$ [smeur2016, Eq. 1; acquatella2017, Eq. 1]. In this chapter $\Omega$ is written $\omega$ when it is the measured rate, as in chapter 5. The moment $M$ has three parts [smeur2016, Eq. 6]:

$$
I_v\dot\omega = -\omega\times I_v\omega + M_c(\varpi) + M_a(\omega, v) - M_r(\varpi,\dot\varpi,\omega),
$$

where $\varpi_i$ is the speed of rotor $i$, $M_c$ the control moment produced by the rotors, $M_a$ the aerodynamic moment (drag, gusts, any offset of the centre of mass) and $M_r$ the moment due to rotor angular momentum. The note on smeur2016 flags the exact form of the rotor-momentum equations (Eqs. 2-5) as partly garbled in the extraction, so only the structure is used here `[TO VERIFY against PDF]`.

**Control moment.** Each rotor produces a thrust $k_1\varpi_i^2$ and a reaction (drag) torque $k_2\varpi_i^2$ about its axis, with the sign of the latter alternating with the spin direction. For an X-quad with half-width $b$ and half-length $l$, roll and pitch moments come from differences of thrust times a lever arm, and the yaw moment from the signed sum of the drag torques [smeur2016, Eq. 7: $M_c = B\,[\varpi_1^2,\dots,\varpi_4^2]^T$ with $B$ built from $bk_1$, $lk_1$ and $k_2$; the signs of some entries were assumed from the pattern in the note `[TO VERIFY against PDF]`]. Tal and Karaman write the same relation as $(\mu;T) = G_1\varpi^{\circ 2} + G_2\dot\varpi$ [tal2021, Eq. 5].

**Control effectiveness $G_1$.** Dividing by the inertia gives the angular acceleration the actuators can produce per unit of actuator input:

$$
\dot\omega = F(\omega, v) + G_1\,u_{act} + G_2\,\dot u_{act} + \dots,\qquad F = I_v^{-1}\big(M_a - \omega\times I_v\omega\big).
$$

Smeur et al. take the rotor speed squared as input and obtain $G_1 = 2 I_v^{-1} B$ [smeur2016, Eq. 9; read from the extraction, "not stated explicitly" in the note `[TO VERIFY against PDF]`]. In this project the input is a normalised torque, so $G_1$ is a diagonal matrix with units rad/s$^2$ per unit torque: $G_1 \approx I_v^{-1} M_{max}$ per axis, with $M_{max}$ the physical torque corresponding to $\tau = 1$ [UNSOURCED: this normalisation is a project convention, section 5.2.6]. Because $I_v$ is nearly diagonal for a symmetric airframe, the three axes decouple in $G_1$. Two further properties matter later. First, $G_1$ is operating-point dependent: with $\varpi_i$ linear in the command, thrust is quadratic in it, so $\partial T_i/\partial\varpi_i$ grows with rotor speed. Smeur et al. keep the factor $\mathrm{diag}(\varpi_f)$ in the full law and show that treating the rotor as linear raised a least-squares error by about 0.9 % on one dataset [smeur2016, Sec. III.A]. Second, $G_1$ depends on inertia, battery voltage and airspeed, which is the motivation for adaptive estimation [smeur2016, Sec. IV; blaha2024, Sec. II-B].

**Yaw spin-up term $G_2$.** Yaw torque is rotor drag torque. To change it the rotors must be accelerated, and their inertia $I_{rzz}$ produces a reaction torque on the airframe proportional to the rotor acceleration. Smeur et al. write the corresponding effectiveness $G_2 = I_v^{-1}[0;0;I_{rzz}(1,-1,1,-1)]$, non-zero only in the yaw row [smeur2016, Eq. 10; the placement of $T_s$ in this expression is unclear in the extraction `[TO VERIFY against PDF]`]. They report that its effect is "very significant" in yaw: the measured yaw-acceleration change matched the prediction with $G_2$ and was far off without it, and flights without $G_2$ oscillated or needed inflated yaw effectiveness [smeur2016, Sec. VI.D]. In chapter 5 the term enters as $G_2\,\dot\tau$ with units rad/s$^2$ per unit torque rate, where $\dot\tau$ is evaluated as a finite difference over $T_s$ (section 5.2.5). The sign convention is that of section 5.2.5. Gyroscopic coupling of the spinning rotors with the roll and pitch rates, the $G_3$ term of Smeur et al., was dropped by them at a cost of about 0.2 % in the same least-squares fit [smeur2016, Sec. III.A], and is not modelled here.

## 3.2 Nonlinear dynamic inversion

Write the rate dynamics in control-affine form, $\dot\omega = f(\omega, v) + G(\omega)\,u$ [acquatella2017, Eq. 4; the definitions of $f$ and $G$ are garbled in the extraction and were read as $f = I^{-1}(M_a - \omega\times I\omega)$, $G = I^{-1}(M_c)_u$ `[TO VERIFY against PDF]`]. Nonlinear dynamic inversion chooses the input that cancels the model and imposes a desired acceleration $\nu$:

$$
u = G^{-1}(\omega)\,\big(\nu - f(\omega, v)\big)\quad\Rightarrow\quad \dot\omega = \nu .
$$

The virtual control $\nu$ is then the output of a linear outer law, for example $\nu = K(\omega_{sp}-\omega)$, which gives the first-order error dynamics $\dot e = -Ke$ for a constant setpoint [acquatella2017, Eqs. 6-10].

The strength of the method is that the closed loop is linear and has designed dynamics. Its weakness is where the model enters. The inversion is exact only if $f$ and $G$ are exact. The inertia, the gyroscopic term, drag, rotor effects and any external moment must all be known, and an error in any of them appears directly as an acceleration error. Acquatella et al. describe the law as "sensitive to model uncertainties" [acquatella2017, Sec. 3.1]. For a multirotor this is a practical problem. $M_a$ depends on airspeed and attitude, and its partial derivatives are rarely available. A payload or a battery shift changes $I_v$ and the centre of mass in a way that no fixed model captures.

## 3.3 The incremental form

**Taylor expansion about the current state.** Incremental NDI avoids evaluating $f$. Let $(\omega_0, u_0, \dot\omega_0)$ be a recent measurement, with $\dot\omega_0 = f(\omega_0,v_0)+G(\omega_0)u_0$. A first-order expansion of the dynamics about it gives

$$
\dot\omega \;\approx\; \dot\omega_0 + \frac{\partial f}{\partial\omega}\Big|_0(\omega-\omega_0) + \frac{\partial f}{\partial v}\Big|_0(v-v_0) + G(\omega_0)\,(u-u_0).
$$

**Time-scale separation.** The method assumes that over one controller step the state moves little, so that the first two correction terms can be dropped, while the input moves fast: the actuator increment $G\,\Delta u$ dominates. Smeur et al. state this condition as validity "only if actuators are fast relative to aerodynamic and precession moments" and neglect the partials with respect to $\omega$ and $v$ [smeur2016, Sec. III.A, text after Eq. 13]. Acquatella et al. express it as $\epsilon_{INDI} = f(\omega(t-\lambda))-f(\omega(t))\approx 0$ for small delay $\lambda$ [acquatella2017, Eq. 12], together with fast actuators, $1/\tau_a$ above the closed-loop bandwidth. Smeur et al. 2018 drop the same partials and treat the aerodynamic effect as disturbance because no airspeed model is available [smeur2018, Sec. 2, p. 3].

Wang et al. object that this argument "is not mathematically rigorous and is especially deficient for unstable nonlinear plants" [wang2019, Sec. III.A, p. 1119]. They keep the dropped terms as a perturbation $\delta(z;\Delta t)$ of the closed loop, $y^\rho = \nu + \delta(z;\Delta t)$ [wang2019, Eq. 13, reconstructed in the note `[TO VERIFY against PDF]`], and prove ultimate boundedness with a bound that shrinks with the sampling interval [wang2019, Theorem 1, p. 1119]. Their proofs assume ideal actuators; actuator dynamics and limits appear only in simulation [wang2019, p. 1119, p. 1124]. For this report the practical content is the same under both views: the incremental form is accurate when the sampling period is short compared with the dynamics that were dropped.

**Resulting law.** Dropping those terms and requiring $\dot\omega = \nu$ gives the increment

$$
\Delta u = u-u_0 = G_1^{-1}\,(\nu - \dot\omega_0),\qquad u = u_0 + G_1^{-1}(\nu - \dot\omega_0),
$$

which is the form of [acquatella2017, Eqs. 14-15] and, with the reconstruction caveats of the note, [smeur2016, Eq. 19 and Eq. 21]. This is the law of section 5.2.2 with $\dot\omega_0 \to a_f$ and $u_0 \to \tau_f$.

**From model dependence to sensor dependence.** The vector $f(\omega,v)$ does not appear in the law. Everything that moves the vehicle and that is not an actuator effect (gyroscopic terms, drag, gusts, a centre-of-mass offset) is contained in the measured $\dot\omega_0$. Smeur et al. state the consequence: only the control-effectiveness matrices remain as a model [smeur2016, Abstract; Sec. I]. They verified this with a step moment from an added weight, which the controller removed with no steady-state error, against a PID that took about five times longer [smeur2016, Sec. VI.B]. That is one airframe and one disturbance, and is cited here only to show that the mechanism was demonstrated, not that it is general.

The dependence on the model is replaced by a dependence on two signals:

1. a measured angular acceleration $\dot\omega_0$, which in a flight controller comes from differentiating the gyro and is therefore noisy and delayed (section 3.4);
2. the actuator state $u_0$ that corresponds to that measurement. This is not the last command but what the actuators actually produced. Smeur et al. use rotor-speed feedback when it exists and an actuator model otherwise [smeur2016, Sec. III.B, Fig. 4]; Tal and Karaman close a motor-speed loop with optical encoders [tal2021, Sec. I, Sec. III-E]; Blaha et al. use rotor-speed telemetry, or an emulated first-order lag when the thrust coefficient is unknown [blaha2024, Sec. II-A.a, Sec. II-B.c]. Steffensen et al. treat the actuator state as measured and propose no estimator [steffensen2023, Eqs. 1-2, p. 3].

The effectiveness $G_1$ stays in the law as a gain. Acquatella et al. show that with $G_1$ replaced by a fixed $\bar g$, the law is algebraically an incremental PI(D) with $K=(\bar g\,t_s)^{-1}$ and $T_I = k_P^{-1}$ [acquatella2017, Eqs. 29-30; the printed parallel-form equations 26 and 28 are inconsistent with 29, see the note `[TO VERIFY against PDF]`]. Their equivalence is an identity between two control laws, not a statement about a mismatched plant [acquatella2017, note section 4].

## 3.4 Angular acceleration estimation and filter synchronisation

**Estimation.** Angular acceleration is not measured directly. It is obtained by filtering the gyro and differencing: $\dot\omega_f \approx (\omega_f - z^{-1}\omega_f)/T_s$ [smeur2016, Eq. 17]. Smeur et al. use a second-order low-pass $H(s)=\omega_n^2/(s^2+2\zeta\omega_n s+\omega_n^2)$ with $\omega_n = 50$ rad/s and $\zeta = 0.55$ [smeur2016, Eq. 15 and text]. Tal and Karaman use a second-order Butterworth at 30 Hz [tal2021, Sec. V-A]; Blaha et al. use one at 15 Hz [blaha2024, Sec. II-A.a]. The filter is needed because differentiation amplifies noise, and it adds delay. In this project the chain is the one of section 5.2.4, built from `IMU_GYRO_CUTOFF` and `IMU_DGYRO_CUTOFF`.

**Why the actuator state must pass through the same filter.** The Taylor expansion of section 3.3 is valid when the acceleration and the actuator state it is paired with refer to the same instant. After filtering, the measured acceleration is $a_f = H\dot\omega$, a delayed and smoothed copy. If $u_0$ is the unfiltered actuator state, the increment compares an old acceleration with a fresh input. Smeur et al. therefore re-evaluate every operating-point term of the expansion at its filtered value, $(\cdot)_f$, which makes the terms synchronous [smeur2016, Sec. III.B, Eq. 16]. Tal and Karaman require "identical LPFs ... to ensure that equal phase lag is incurred by acceleration and thrust measurements" [tal2021, Sec. III-B, p. 6], and Blaha et al. use one filter on $\nu_0$, $u_0$ and $\dot\Omega_0$ "so Eq. (1) stays valid" [blaha2024, Sec. II-A.a].

The effect is visible in a one-axis calculation. Let the actuator be $A(s)$ with a perfect model, the plant $\dot\omega = G_1 A u + d$, and the law $u = \tau_0 + G_1^{-1}(Ke - a_f)$ with $a_f = H\dot\omega$. If the model state is filtered, $\tau_0 = HAu$, then $u(1-HA) = G_1^{-1}(Ke - HG_1Au - Hd)$ and, since $HAu$ appears on both sides,

$$
u = G_1^{-1}\,(Ke - Hd). \qquad\text{(synchronised)}
$$

If the model state is not filtered, $\tau_0 = Au$, the same algebra gives

$$
u\,\big(1 - A(1-H)\big) = G_1^{-1}\,(Ke - Hd). \qquad\text{(not synchronised)}
$$

The extra factor $A(1-H)$ is the synchronisation error. For $\omega T_H \ll 1$, with $T_H$ the group delay of $H$, $1 - H \approx j\omega T_H$ grows linearly with frequency, so the unsynchronised loop carries a frequency-dependent distortion of the effective gain and an extra phase lag equivalent to a pure delay $T_H$. The filter delay then adds to the loop delay that limits the bandwidth. This is my derivation for a first-order picture; the experimental counterpart is that Smeur et al. observed severe oscillation when the filter-delay compensation was removed and did not fly the doublet for safety [smeur2016, Sec. VI.A, Fig. 11]. Steffensen et al. also note the cost of filtering derivative signals, "filtering leads to delay, which will lead to deterioration of the controller performance", and cite filter synchronisation as the INDI remedy [steffensen2023, Discussion, p. 13].

Synchronisation is also imperfect in practice. Wang et al. state that "synchronization errors still exist in practice" even with a shared filter [wang2019, p. 1123]. The remaining sources in this project are listed in section 5.2.4: the sensor filters run at the gyro rate and the controller copy at the controller rate, the backward difference adds half a raw sample, and notch filters are not replicated.

## 3.5 Actuator dynamics and delay

**First-order model.** The motor-propeller chain is modelled as a first-order lag in torque, $\dot\tau_{act} = (\tau_{cmd}-\tau_{act})/T_a$, so $A(s) = 1/(T_a s+1)$. This is the model of Smeur et al. [smeur2016, Sec. III.B; same $A_z$ for all motors, Sec. III.C], of Steffensen et al. ($\dot u = \Omega(u_c-u)$ [steffensen2023, Eq. 2]) and of Tal and Karaman ($\dot\varpi = \tau_m^{-1}(\varpi_c-\varpi)$ with $\tau_m = 20$ ms in simulation [tal2021, Eq. 32, Sec. IV-A]). Smeur et al. note that the motors of their vehicle differ from each other, contrary to the equal-actuator assumption [smeur2016, Sec. VI.C text on Fig. 20]. Real ESC and motor responses are also not symmetric in rising and falling commands [UNSOURCED; the asymmetry is mentioned only in the session-16 review, which reports separate up and down constants in the Gazebo model].

**Discretisation.** With the command held constant over one cycle (zero-order hold), the exact solution of the lag over $T_s$ is $\tau_{act}(t+T_s) = e^{-T_s/T_a}\tau_{act}(t) + (1-e^{-T_s/T_a})\tau_{cmd}$, so

$$
\tau_{act}[k] = \tau_{act}[k-1] + \alpha_a\big(\tau_{cmd}[k-1]-\tau_{act}[k-1]\big),\qquad \alpha_a = 1 - e^{-T_s/T_a}.
$$

The input is the command of the previous cycle, which is the right alignment because the gyro sample at $t_k$ reflects what was commanded one cycle earlier. Smeur et al. 2018 give the discrete actuator as $A(z)=\alpha/(z-(1-\alpha))$ with $\alpha=0.1$ at 512 Hz [smeur2018, Eq. 11, p. 4]. Read as the same ZOH form, this corresponds to $T_a = -T_s/\ln(1-\alpha) = (1/512)/0.1054 \approx 18.5$ ms (arithmetic done here, not stated in the paper).

**Pipeline delay.** Beyond the lag there is transport delay: sensor sampling and batching, the half-sample added by the backward difference, publication between modules, and the ESC protocol period. A pure delay $e^{-sT_d}$ multiplies $A(s)$. Smeur et al. compensate delay only through the filtered linearisation, not by prediction, and reject predictive filtering because it needs extra modelling [smeur2016, Sec. I, Sec. III.B]. In the project law an integer delay of $d$ samples can be inserted on $\tau_{act}$ before $H$ (section 5.2.2), which can represent whole cycles only.

**Inner-loop consequence.** With synchronised signals and an exact model, angular acceleration follows $\nu$ through the actuator: $\dot\omega = A\,\nu$ (section 3.6). Steffensen et al. state the same for INDI with equal bandwidths, $y^{(r+1)} = \omega_{act}(\nu - y^{(r)})$, "$y^{(r)}$ follows $\nu$ with the dynamics of the actuator" [steffensen2023, Eq. 29, p. 8], and Smeur et al. that the inner loop response is "simply the actuator dynamics" [smeur2016, Sec. V.A]. The actuator therefore bounds the achievable bandwidth: $K$ must lie below $1/T_a$ for the time-scale separation of section 3.3 to hold. Acquatella et al.'s simulation, with $1/\tau_a = 100$ rad/s and $k_{P} = 50$ rad/s, has a separation of only a factor 2, which their note flags as weak [acquatella2017, note section 6].

## 3.6 Closed-loop behaviour

This section derives the closed loop for one axis in the Laplace domain, first with an exact actuator model and then with a mismatched one. The symbol $u$ is the normalised torque command $\tau_{cmd}$ of section 5.2.2, without saturation. Time constants of the model and of the real actuator are written $T_e$ and $T_t$ (the session-16 review uses $\tau_e,\tau_t$). The model is $A_{est}=1/(T_es+1)$ and the plant $A_{true}=1/(T_ts+1)$.

### 3.6.1 Setup

The plant, with $d$ an unmodelled disturbance acceleration, and the law of section 5.2.2 are

$$
\dot\omega = G\,A_{true}\,u + d,\qquad a_f = H\dot\omega,\qquad \tau_f = H A_{est}\,u,\qquad u = \tau_f + G_1^{-1}\,(Ke - a_f),
$$

with $e = \omega_{sp}-\omega$ and $G$ the true effectiveness (equal to $G_1$ for now). The sensor-side and model-side filters are the same $H$, which is the synchronisation condition of section 3.4.

### 3.6.2 Exact actuator model

Take $A_{est}=A_{true}=A$. Substituting,

$$
u = HAu + G_1^{-1}\big(Ke - HG_1Au - Hd\big)\;\Rightarrow\; u = \frac{K}{G_1}\,e - \frac{1}{G_1}H d .
$$

The command is a proportional law on the rate error, $u = (K/G_1)e$, plus a cancellation of the filtered disturbance. The feedback is taken "around the actuator state": the increment is added to $\tau_f$, not to the previous command.

Two views of the same loop are useful. Writing $\Delta = G_1^{-1}(Ke - a_f)$ for the increment, $u = HA_{est}u + \Delta$ gives

$$
u = \frac{1}{1 - HA_{est}}\,\Delta .
$$

At low frequency $HA_{est}\to 1$, so $1/(1-HA_{est})$ has a pole at the origin: the map from the increment to the command is an integrator. The integral action sits in this structure, not in a separate integrator. The session-16 review reaches the same statement [review_s16, section 1]. Substituting $u$ into the plant gives the acceleration and the rate:

$$
\dot\omega = A K e + (1 - AH)\,d,\qquad \omega = \frac{K A\,\omega_{sp} + (1-AH)\,d}{s + K A}.
$$

With $A = 1$ and $H = 1$ this is $\omega/\omega_{sp} = K/(s+K)$, the first-order response of section 5.2.2. In general the loop transfer function is $L = KA/s$, so the rate loop is an integrator and a first-order lag with gain $K$ and no model of $f$ or $d$. The disturbance enters through $1 - AH$. Both $A$ and $H$ are unity at DC, so a constant disturbance has no steady-state effect on $\omega$ (final value theorem with $1-AH\to 0$), and no integrator is needed. Above the bandwidth of $AH$, $1-AH\to 1$ and the disturbance passes unattenuated: rejection is a high-pass-complement shape set by the actuator and the filters. This is the quantitative version of the qualitative claim of Smeur et al. that "disturbance rejection holds when actuator and filter dynamics are stable" [smeur2016, Sec. III.C; the transfer-function algebra of Eqs. 22-27 is garbled in the extraction and was not used `[TO VERIFY against PDF]`].

**Effectiveness error.** If $G = gG_1$, the same algebra gives $u\,[1 + (g-1)HA] = G_1^{-1}(Ke - Hd)$. At DC the acceleration is $Ke$ regardless of $g$; at frequencies where $HA\to 0$ the loop gain is multiplied by $g$. A discrete analysis in the note on Acquatella et al., made there and not in the paper, gives an acceleration-error recursion $e_k = (1 - G/\bar g)e_{k-1}$, stable for $0<G/\bar g<2$ [acquatella2017, note section 7]. An error in $G_1$ therefore changes the bandwidth, not the DC behaviour.

### 3.6.3 Actuator-model mismatch

Now $A_{est}\neq A_{true}$. The same substitution gives

$$
u = HA_{est}u + G_1^{-1}\big(Ke - HG_1A_{true}u - Hd\big)\;\Rightarrow\;
u\,\big(1 - H(A_{est}-A_{true})\big) = G_1^{-1}(Ke - Hd),
$$

that is

$$
u = \frac{K}{G_1}\,\frac{e}{1 - H\,\Delta A},\qquad \Delta A = A_{est}-A_{true}.
$$

This agrees with the session-16 review [review_s16, section 5], which wrote it without the disturbance term. The difference of two first-order lags is

$$
\Delta A = \frac{1}{T_es+1}-\frac{1}{T_ts+1} = \frac{(T_t-T_e)\,s}{(T_es+1)(T_ts+1)},
$$

a band-pass with a zero at the origin and two poles, as in the review. Its magnitude is $|\Delta A(j\omega)| = (T_t-T_e)\,\omega\,/\sqrt{(1+T_e^2\omega^2)(1+T_t^2\omega^2)}$. Maximising over $\omega$ is the same as minimising $\big(1+T_e^2\omega^2\big)\big(1+T_t^2\omega^2\big)/\omega^2 = \omega^{-2} + T_e^2 + T_t^2 + T_e^2T_t^2\omega^2$, whose minimum is at $\omega^{*2} = 1/(T_eT_t)$, where it equals $(T_e+T_t)^2$. Hence

$$
f^* = \frac{1}{2\pi\sqrt{T_eT_t}},\qquad |\Delta A|_{max} = \frac{|T_t-T_e|}{T_t+T_e}.
$$

The review's expression for the peak is truncated in the text; the closed form above is my result, and its numeric value for 20/40 ms matches the review's 0.33. At $\omega^*$ the two pole phases sum to $-90^\circ$, which cancels the $+90^\circ$ of the zero, so $\Delta A(j\omega^*)$ is real, with the sign of $T_t - T_e$.

**Numbers for $T_e = 20$ ms, $T_t = 40$ ms.**

- $\sqrt{T_eT_t} = \sqrt{0.020\times0.040} = \sqrt{8\times10^{-4}} = 0.02828$ s, so $\omega^* = 35.36$ rad/s and $f^* = 35.36/(2\pi) = 5.63$ Hz.
- $|\Delta A|_{max} = (0.040-0.020)/(0.040+0.020) = 0.333$, positive (plant slower than model).
- With $H\approx1$ at $f^*$ (the 30 Hz filters lie well above 5.6 Hz), the factor $1/(1-H\Delta A) = 1/(1-0.333) = 1.50$, a 50 % rise of the controller gain in the band around 5.6 Hz.
- With the phase lag of $H$ at $f^*$ taken as $26^\circ$ (the value given in the review, not recomputed here): $1-0.333\,e^{-j26^\circ} = 0.700 + j0.146$, magnitude $0.716$, factor $1.40$.
- At the nominal crossover of $L = KA_{true}/s$ for $K = 20$ rad/s and $T_t = 40$ ms, $\omega_c$ solves $\omega\sqrt{1+(0.04\,\omega)^2} = 20$, so $\omega_c \approx 16.6$ rad/s (2.6 Hz; the review gives about 3 Hz). There $|\Delta A| = 0.262$ at $+38^\circ$, and with $H=1$ the factor is $1.23$.

**Which side is dangerous.** Take $\Delta A(j\omega^*)>0$ when $T_t>T_e$: the denominator $1-H\Delta A$ falls below 1 and the gain rises. This is the case of a plant slower than the model, or, equivalently, a model faster than the plant (`MC_INDI_ACT_TC` too small). If $T_t<T_e$ the sign reverses: for $T_e = 40$ ms and $T_t = 20$ ms, $|1+0.333\,H|\approx 1.33$ (1.31 with the $26^\circ$ lag) and the gain falls by a factor of about 0.75. The loop is sluggish but not boosted, so over-estimating `MC_INDI_ACT_TC` is the safe side. The review reaches the same conclusion, noting that a model 1.5 to 3 times slower than the plant gives $\Delta A<0$, and that a model much faster than the plant moves $f^*$ to a frequency where $|L|$ is already small [review_s16, section 5]. I find no disagreement with the review in sign or in algebra.

**What the boost does and does not do.** Two limits should be kept apart. First, the map $e \to u$ is itself stable for any pair of lags: $|\Delta A|\le |T_t-T_e|/(T_t+T_e)<1$ and $|H|\le 1$ for the low-pass chain (and for an added delay), so $|H\Delta A|<1$ and the small-gain theorem rules out right-half-plane zeros of $1-H\Delta A$ (my derivation). The limit does not hold once a model-plant delay mismatch is added, because then $|\Delta A|$ can approach 2. Second, the outer loop sees $L = KA_{true}/[s(1-H\Delta A)]$ times the delays of section 3.5. The boost multiplies the loop gain in the 3 to 8 Hz band, which is close to the crossover, where the phase margin is already reduced by the real actuator lag, the lag of $H$ and the pipeline delay. The review attributes a roll limit cycle at 5 to 7 Hz to this mechanism [review_s16, section 5, marked there as suspected, not reproduced]. This report treats it as a hypothesis for chapters 7 to 9 to test, not as a result.

## 3.7 Saturation and allocation in torque space

The derivation above is linear. Three nonlinearities act in the implementation (section 5.2.2): a clamp on the increment, $\Delta\tau = \mathrm{sat}_{\Delta_{max}}(G_1^{-1}(\nu-a_f))$; a clamp on the output, $\tau_{cmd} = \mathrm{sat}_1(\tau_f+\Delta\tau)$; and the allocator, which maps the three torques and the thrust to four motor commands and may not reach all of them. The papers do little here. Smeur et al. describe no saturation handling [smeur2016, Sec. VI notes], Acquatella et al. do not discuss it [acquatella2017, note section 5], Smeur et al. 2018 state that saturation can destabilise the loop and point to prioritised allocation as work in progress [smeur2018, p. 15], and Tal and Karaman reallocate yaw torque first, then reduce thrust, then clip [tal2021, Sec. III-E]. Blaha et al. use an active-set solution when bounds must hold [blaha2024, Sec. II-A].

Torque space has one useful property. The law adds the increment to $\tau_f$, the filtered modelled achieved torque, not to the last command. If the model state is driven by the torque the allocator actually produced, $\tau_{alloc}$, then a command beyond the achievable range does not accumulate in the state, and the loop does not wind up in the sense of an integrator, because the integration of section 3.6.2 acts on achieved torque. This follows from the structure of the law (my reasoning) and holds only as far as the allocator's feedback of achieved torque is current. Chapter 5 gives the clamps, the allocator feedback path and its staleness limit (section 5.3.5; the session-16 review records a case where the feedback is stale on part of the cycles).

## 3.8 Assumptions tested in later chapters

The derivations above rest on the following assumptions. Each is checked later in the report, in the simulation setup (chapter 6), the tuning (chapter 7), the benchmark (chapter 8) or the discussion (chapter 9).

1. **Time-scale separation.** Actuator and sampling dynamics are fast compared with the neglected terms (section 3.3). The proof of [wang2019] gives boundedness with a sampling-dependent perturbation, but no numeric bound for a multirotor.
2. **Known and constant $G_1$.** A single hover-point value per axis is used (section 3.1, section 5.2.6). An error scales the high-frequency loop gain (section 3.6.2). Model-mismatch scenarios test it.
3. **First-order, symmetric actuator with known $T_a$.** Errors in $T_a$ add the band-pass of section 3.6.3, and the direction of the error matters.
4. **Synchronised filters.** The actuator model passes through the same $H$ as the gyro derivative (section 3.4). Residual errors are the rate difference, half a sample of delay and notch filters.
5. **Pipeline delay representable in whole cycles.** The delay parameter covers integer samples only (section 3.5).
6. **Decoupled axes.** $G_1$ is diagonal and gyroscopic coupling ($G_3$) is ignored [smeur2016, Sec. III.A].
7. **Yaw spin-up.** For yaw, $G_2$ is either identified or taken as zero (section 5.2.5). Smeur et al. found it very significant on their vehicle [smeur2016, Sec. VI.D]; this project's default of zero is an assumption to be tested.
8. **Achieved torque is observable.** Saturation handling assumes the allocator reports what it produced (section 3.7).
9. **No advantage without a differing mechanism.** With fixed $G_1$ the law is an incremental PID [acquatella2017, Eqs. 29-30], so any benefit over a tuned PID must come from the achieved-torque feedback, the measured-acceleration disturbance rejection, or saturation handling (section 5.2.3).
