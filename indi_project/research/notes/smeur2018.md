# Smeur, de Croon, Chu (2018): Cascaded Incremental Nonlinear Dynamic Inversion for MAV Disturbance Rejection

**Citation.** E. J. J. Smeur, G. C. H. E. de Croon, Q. Chu, "Cascaded incremental nonlinear dynamic inversion for MAV disturbance rejection", *Control Engineering Practice*, 2018. arXiv:1701.07254 (the local copy is arXiv v2, dated 12 Jan 2022 in its header). Affiliation: Department of Aerospace Engineering, Delft University of Technology. Journal volume and page numbers are not confirmed by the local text and are not given here.

**Local copy.** `indi_project/research/raw/foundations/smeur2018_cascaded.pdf` (PDF) and `indi_project/research/raw/foundations/smeur2018_cascaded.txt` (1130 lines, text extraction with the two-column layout preserved, so columns are side by side and must be read in pairs).

**Page convention.** Page numbers are the arXiv v2 printed page numbers, taken from the footer numbers in the extracted text. They are not the journal pagination. Where a page boundary is ambiguous in the extraction, the page is given as "(p. ~N)".

**Extraction caveat.** Equations are partly garbled by text extraction (sub/superscripts, Greek letters and some fractions are flattened). Equations written as "[reconstructed]" were rebuilt from the surrounding text and figures. Where a reconstruction could be checked numerically against values stated in the paper, the check is noted.

## Summary

1. Scope: the paper extends INDI attitude control (earlier analysis in Smeur et al. 2016a) to the outer, position/linear-acceleration loop, and shows the combination on a Parrot Bebop quadrotor running Paparazzi (Sec. 1, pp. 1-2; Sec. 2, p. 2).
2. Inner loop: angular acceleration and thrust increments are computed from a first-order Taylor expansion with static 4x4 control-effectiveness matrices G1, G2, using measured Ω̇ and T that are filtered by the same second-order filter as the inputs (Eqs. 1-7, pp. 2-3).
3. Attitude outer loop: a quaternion error feeds gains Kη and KΩ, giving an angular-acceleration reference. Bebop actuator model is first-order, A(z) = α/(z − (1 − α)) with α = 0.1 at 512 Hz (Eq. 11, p. 4). Stated gains KΩ = 28.0 and Kη = 21.4 give poles at 0.964 and 0.965 ± 0.0445i (p. 4). Table 2 (p. 10) lists Kη = 28.0 and KΩ = 10.7 instead, which conflicts with these values (see (d)). Measured step response differs from the linear design by at most 6.4 % of the step (Fig. 5, p. 5; 25 repetitions).
4. Experiments (details in (d)): (i) indoor 10 m/s open-jet wind-tunnel in-and-out flights, 7 repetitions per controller: maximum position deviation 0.21 m on entry and 0.20 m on exit for INDI, 1.51 m for PID (Sec. 5.1, Fig. 11, pp. 10-11). The introduction's 21 cm and 151 cm figures (p. 2) match these. (ii) Outdoor takeoff on standard GPS in a 5.1 m/s mean wind (KNMI, not measured on site): average maximum position error 0.24 m for INDI (13 flown, 1 rejected, 12 analysed) versus 0.85 m for PID (12 flights) (Sec. 6, Fig. 14, pp. 12-13). (iii) Linearised versus nonlinear thrust increment, 25 repetitions each: no numbers in the text; the authors state the nonlinear version reduces the maximum vertical-acceleration error (Sec. 7, Figs. 15-16, p. 14).
5. Caveats for a fair INDI-vs-PID benchmark are in (e). Gain values conflict between Sec. 2 and Table 2 (see (d)), and the displayed acceleration filter differs from the controller filter.

## (a) Inner-loop and outer-loop INDI laws

**Inner loop: angular acceleration and thrust (Sec. 2, pp. 2-4).**
- Model: [Ω̇; T] = F(Ω, v) + G(ω, ω̇) (Eq. 1, p. 2). Ω = body rates, ω = propeller rates, T = total thrust. The 4-vector is three angular accelerations plus thrust (p. 2).
- First-order Taylor expansion about the previous sample (Eq. 2, p. 3). The ∂F/∂Ω and ∂F/∂v terms are dropped and treated as disturbance, since no airspeed model or airspeed estimate is used (p. 3). The partials of G are taken as static matrices G1, G2 (4x4, one column per rotor, rows roll/pitch/yaw/thrust; p. 3).
- Incremental form (Eq. 3, p. 3): [Ω̇ − Ω̇0; T − T0] = G1(ω − ω0) + Ts·G2(ω̇ − ω̇0). Ts is factored out of G2 (p. 3).
- Filtered form (Eq. 5, p. 3): same structure with the filtered terms (subscript f). Finite differences ω̇ = (ω − Lω)/Ts, with L the lag operator, give Eq. 6: [Ω̇ − Ω̇f; T − Tf] = (G1 + G2)(ω − ωf) − G2·L(ω − ωf). I checked that Eq. 6 follows from Eq. 5 by substitution.
- Inversion (Eq. 7, p. 3) [reconstructed from extraction]: ω_c = ω_f + (G1 + G2)^(-1)·( [ν_Ω̇ − Ω̇f; Te] + G2·L(ω_c − ω_f) ). ν_Ω̇ is the virtual control (desired angular acceleration). Te = T − Tf is the thrust increment computed in the outer loop (p. 3). The motor command increment is added to the filtered motor feedback (p. 3; Fig. 3, p. 4).
- Attitude outer part (Sec. 2.1, pp. 3-5). Quaternion error q_err = q_ref ⊗ q_s* (Eq. 8). Rate reference Ω_ref = Kη·[q1err q2err q3err]^T (Eq. 9), so Kη is a proportional gain on the vector part. The angular-acceleration reference comes from the rate error through a second gain KΩ (p. 4; block diagram Fig. 4, p. 5). Quaternion kinematics q̇ = ½ q ⊗ [0; Ω] (Eq. 10). For the linear analysis the quaternion integration is removed, which gives the factor 2 in front of Kη (Fig. 4 labels it 2Kη; the text extraction shows "21", read as 2) (p. 4).
- Closed-loop transfer function η_ref → η (Eq. 12, p. 4) [denominator reconstructed]. The stated poles 0.964 and 0.965 ± 0.0445i (KΩ = 28.0, Kη = 21.4) are consistent with the reconstructed denominator: the root sum and product agree with its z² and constant coefficients to the printed precision (my check, not a claim in the paper).
- Stated consequence (p. 4): the P and D gains "are not free to choose without consequences for the stability". Neglecting actuator dynamics can give a stable-looking design that is unstable with slower actuators (the paper's example is α = 0.02, where Eq. 12 is unstable with the same gains).

**Outer loop: linear acceleration (Sec. 3, pp. 5-6).**
- Position dynamics: ξ̈ = g + (1/m)F(ξ̇, w) + (1/m)T_N(η, T) (Eq. 14, p. 6). Thrust in NED: T_N(η, T) = M^NB(η)·[0, 0, T]^T (Eq. 15, p. 6).
- Linearisation (Eq. 16-17, p. 6). A first-order Taylor expansion is taken in ξ̇, w, φ, θ, ψ and T. The aerodynamic partials ∂F/∂ξ̇ and ∂F/∂w are set to zero ("the best guess"), and the aerodynamic forces enter through the measured ξ̈0. The ψ-derivative term is dropped on the assumption that ψ changes slowly. Result: ξ̈ = ξ̈0 + (1/m)·G(η0, T0)(u − u0), with u = [φ θ T]^T (Eq. 17). The matrix G(η, T) is Eq. 18 (partly garbled; the layout was not checked entry by entry).
- Incremental law (Eq. 19, p. 6): u_c = u_f + m·G^(-1)(η0, T0)·(ν_ξ̈ − ξ̈f), with u_e = u_c − u_f. Here ν_ξ̈ is the desired acceleration (virtual control), and ξ̈0 is obtained by rotating the body-frame specific force to NED and adding gravity (p. 6).
- Outer-loop structure (Fig. 6, p. 7): roll and pitch increments are added to the filtered measured roll and pitch. The thrust increment Te goes directly to the inner loop.
- Position PD (Sec. 4.1, p. 7; Fig. 7). ν_ξ̈ comes from a PD on position and velocity with gains Kξ and Kξ̇, manually tuned for fast response with little overshoot. The explicit equation is not in the extracted text, so the form is read from the block diagram only. The paper states the PD gains depend mainly on the position-estimate update rate and the inner-loop speed (p. 7).
- Nonlinear alternative (Sec. 4.4, pp. 8-9). Eq. 22-23 subtract the dynamics one step earlier and assume gravity and aerodynamic changes are small over one step: ξ̈ − ξ̈0 = (1/m)(T_N(η, T) − T_N(η0, T0)). Eq. 24 gives T_N(η, T) = m(ν_ξ̈ − ξ̈0) + T_N(η0, T0). Eq. 25-27 invert Eq. 15: T = ||T_N||, φc = arcsin((sinψ·TNx − cosψ·TNy)/T), θc = arcsin((cosψ·TNx + sinψ·TNy)/(T·cosφc)). I checked algebraically that Eq. 26-27 invert Eq. 15 exactly. Whether this nonlinear version is used on the vehicle or only compared is for Sec. 5 (not yet read at this point).

## (b) Filtering

- Filter (Eq. 4, p. 3): second-order H(s) = ωn²/(s² + 2ζωn·s + ωn²), taken from Bacon et al. (2001). The text says it "also introduces a delay" (p. 3). The experiment uses ωn = 50 rad/s and ζ = 0.55 (Sec. 4.5, p. 9; Table 2, p. 10). Sec. 4.5 says the attitude-loop disturbance response is 1 − A(z)H(z)z^-1, so a higher cutoff rejects disturbances faster but passes more noise. Both loops share one filter, so the trade-off is set for both at once (p. 9).
- Signals filtered: motor-rate feedback ω (Fig. 3, p. 4); angular acceleration Ω̇ from gyro finite differences, which the text says is "very noisy" (p. 3); thrust feedback T (via motor rate, p. 3); accelerometer-derived ξ̈0 (p. 6); roll and pitch φ, θ (Fig. 6, p. 7).
- Synchronisation: every Taylor term with index 0 is filtered by the same filter and tagged with f, so they share one delay (p. 3, p. 6). The increments are added to filtered measurements (p. 3, p. 6). The outer and inner loops use Eq. 4 with the same parameters (p. 6), because the thrust increment can be passed from outer to inner only when both filters are equal (p. 6).
- Bias estimate (Sec. 4.4, pp. 8-9): the difference between GPS-derived acceleration (rotated into IMU axes) and IMU acceleration is filtered by a second-order filter with natural frequency 0.25 rad/s, to estimate the slowly varying accelerometer bias. The text notes that the gyro-rate derivative removes gyro bias, but the accelerometer bias is not removed that way (p. 9).

## (c) Actuator model and control effectiveness

- Actuator model: first-order A(z) = α/(z − (1 − α)), with α = 0.1 at 512 Hz for the Bebop (Eq. 11, p. 4). It is used in the analysis and gain design, not as an estimator in the control law as far as read.
- Actuator state: the control law uses measured motor feedback. The increment is added to the filtered motor rate ω (Fig. 3, p. 4). Thrust is not measured. It is computed from a quadratic fit of thrust versus propeller rotational speed (Sec. 4.3, p. 8; Fig. 8). The thrust data come from a static test with the quadrotor mounted upside down on a scale (p. 8).
- Rejected alternative: the thrust estimate from accelerometer Z-specific force is said to "work well while hovering" but to fail when other aerodynamic forces appear in body Z, such as at high-speed steady flight with high bank angle (p. 8).
- Identification of G1, G2 (Sec. 2.2, p. 5): a single test flight with logged inputs, gyro and accelerometer data, solved by least squares on Eq. 13 [reconstructed]: [Ω̈f; Ṫf] = [G1, Ts·G2]·[ω̇f; ω̈f], with derivatives by finite difference. The paper says this avoids needing inertia and actuator-force knowledge and "eliminat[es] chances for modeling errors" (p. 5).
- Online adaptation (Sec. 4.2, pp. 7-8): LMS update of G (Eq. 20-21). The rows are extended with the thrust row, so thrust effectiveness also adapts. The paper notes this matters if vehicle mass changes, for example after dropping a payload (p. 7).
- Table 1 (p. 7), thrust-axis effectiveness in 10^-3 m/s²/rpm, per motor M1-M4. Reading the garbled layout: each "Adaptation from" row starts with an initial value (−0.35 or −1.13), followed by the converged values for M1-M4 after 30 s. Values are about −0.77, −0.73, −0.58, −0.63 (start −0.35) and about −0.76, −0.73, −0.59, −0.65 (start −1.13). The offline value is about −0.76, −0.72, −0.57, −0.63. Standard deviations are in the table. Five flights started at each initial value (10 flights in total, p. 7). Table values are read from extraction and should be checked against the PDF.
- Unit ambiguity: Table 1 and p. 7 use "rpm" (average RPM of 126, 126, 125, 123 for M1-M4 over a 2-min flight), while the Fig. 8 axis is labelled "Propeller rotational speed (Hz)" with values 40-160 (p. 8). Flag for the benchmark when comparing units.
- Numeric attitude-axis values of G1 and G2 are not given in the text. Only the thrust row is tabulated (Table 1). The full (4x4) identified matrices are therefore unverified here.


## (d) Experiments

**Vehicle and software.** Parrot Bebop quadrotor running Paparazzi, with the INDI attitude and outer loops implemented in Paparazzi (pp. 2, 10). Control loop, accelerometer and gyro run at 512 Hz (p. 10). The mass and size of the vehicle were not found in the sections read.

**Attitude step check (Sec. 2.1, Fig. 5, p. 5).** Measured step responses over 25 repetitions (mean and standard deviation) are compared with the linear design model of Eq. 12. Maximum deviation is 6.4 % of the step, at 0.14 s. This is a model-versus-flight check of the inner loop, not a comparison with another controller.

**Baseline.** The PID controller uses the same inner INDI attitude loop. Its outer loop has P, I and D terms on position and velocity, mapped to roll, pitch and thrust through the matrix R (Eq. 29, Fig. 9, p. 11). It was tuned by hand for "the fastest response possible to a 5m step input, without oscillation", and energy efficiency was not considered (p. 10).

**Gains as printed.**
- INDI (Table 2, p. 10): ωn = 50 rad/s, ζ = 0.55, KΩ = 10.7 (rad/s²)/(rad/s), Kη = 28.0, Kξ = 0.7 (m/s)/m, Kξ̇ = 1.5 (m/s²)/(m/s).
- PID (Table 3, p. 10): P = 0.65 (m/s)/m, I = 0.11 rad/(m/s)/s, D = 0.2 rad/(m/s).
- The authors give a "crude" mapping: dividing Kξ̇ by 9.81 gives 0.15 rad/(m/s), close to the PID D gain of 0.2. They say the gains are "not exactly the same" (p. 10).
- Conflict: Sec. 2 gives KΩ = 28.0 and Kη = 21.4 (p. 4), while Table 2 gives Kη = 28.0 and KΩ = 10.7. The two sets cannot both be right for the same design. The paper does not say which set applies to the flights.

**E1. Indoor wind tunnel (Sec. 5, pp. 9-11).**
- Setup: TU Delft Open Jet Facility, 2.85 m × 2.85 m outlet, up to 30 m/s. Set to 10 m/s. The quadrotor alternates every 14 s between a waypoint in the exhaust centre and one 2 m outside it. Bebop maximum speed is 13 m/s per the manufacturer (p. 9).
- The disturbance is a simulated gust created by flying in and out of the flow. The previous fan experiment (Smeur et al. 2016b) reached only 4.0 m/s, 1 m in front of the fan, with an inhomogeneous flow (p. 9).
- Position: OptiTrack at up to 120 Hz, but sent to the drone at 4 Hz to imitate GPS (p. 10).
- Repetitions: seven per controller (Fig. 11 caption, p. 11).
- Results (Sec. 5.1, Fig. 11, pp. 10-11): INDI shows a position error of 0.21 m on entry (2.0 s) and 0.20 m on exit (16.6 s), recovered within about 3 s. The PID maximum error is 1.51 m. The PID shows less variation between flights in steady flow. The authors attribute the extra INDI variance to the noisier accelerometer feedback (p. 11).
- Figure 10 shows INDI acceleration filtered with ωn = 20 rad/s and ζ = 0.7. That is a display filter, not the controller filter (ωn = 50 rad/s, ζ = 0.55).
- The conclusion's "more than 7 times lower" (p. 14) is consistent with 1.51 / 0.21 ≈ 7.2, my arithmetic.

**E2. Outdoor takeoff with standard GPS (Sec. 6, pp. 11-13).**
- Setup: first-version Bebop with an external u-blox NEO-M8N GPS over USB, because the built-in GPS of that version was low quality (p. 12). Mean wind 5.1 m/s, from KNMI, not measured on site (p. 12).
- Design: 12 PID flights, then 13 INDI flights, run in sequence without breaks. The authors assume the wind was the same for both blocks, but note that the wind fluctuated between flights (p. 12). One INDI flight was rejected because the state estimator had not converged before takeoff (p. 12). The position reference was reset before each flight (p. 12).
- Results (Fig. 13, Fig. 14, pp. 12-13): average maximum horizontal position error is 0.24 m for INDI versus 0.85 m for PID. Averaged over time, the two errors are similar after some time. Some INDI runs show large errors (Fig. 13). The authors suspect GPS errors, because the accelerometer and GPS velocity disagree in those runs (p. 13).

**E3. Linearised versus nonlinear thrust increment (Sec. 7, pp. 13-14).**
- Setup: indoor arena with position tracking. The quadrotor hovers. The reference is a predefined acceleration step of (0, 4, 0) m/s² for 0.5 s, then (0, −4, 0) m/s² for 0.5 s. G1 and G2 are identified beforehand with the adaptive algorithm. Each case is repeated 25 times (p. 13).
- Results (Fig. 15, linearised; Fig. 16, nonlinear; mean and one standard deviation of NED z-acceleration): the figures are the only source. No numbers are given in the text. Qualitatively, the linearised case shows a slight upward acceleration, then a large downward dip when the bank reverses, which the authors attribute to thrust being reduced (pp. 13-14). The nonlinear case shows a larger early upward acceleration, which the authors attribute to actuator dynamics being faster than rotational dynamics. Its average over repetitions is closer to zero, but a residual unintended acceleration remains (p. 14).
- The authors say the nonlinear version "reduces the maximum error in vertical acceleration tracking for an aggressive maneuver", but that more research is needed to show significant benefits (Sec. 8, p. 14).

## (e) Limitations stated by the authors, and benchmark relevance

**Stated by the authors.**
1. Aerodynamic drag partials (∂F/∂ξ̇, ∂F/∂w) are set to zero, and the inner-loop airspeed and rate partials are treated as disturbances (pp. 3, 6).
2. The ψ-dependence of the thrust vector is neglected because ψ is assumed to change slowly. The authors suggest a different Euler order (XYZ) as a future fix (pp. 6, 15).
3. G1 and G2 are static, and the RPM-thrust nonlinearity is not used in the inner loop (pp. 3, 8, 14-15).
4. The linearisation is accurate only for small increments. The nonlinear alternative was tested in one maneuver only, and more experiments are needed (pp. 8, 14).
5. Actuator saturation can destabilise the loop. The authors' pseudo-inverse allocation then gives a suboptimal realisation of the objective. They point to a prioritised allocation as work in progress (p. 15).
6. The outer loop is sensitive to accelerometer bias, which causes a steady position offset. The authors estimate the bias from GPS-derived acceleration (pp. 8-9). A Kalman filter is mentioned as an alternative.
7. Filter cutoff trades disturbance-rejection speed against noise. A higher cutoff rejects gusts faster but passes more noise. The authors judge the INDI loop noisier than the PID loop in steady flow (pp. 9, 11).
8. In outdoor tests, GPS and state-estimator errors caused some large INDI errors, and the authors say a better estimator is beyond the scope of the paper (p. 13).
9. The authors state that the P and D attitude gains are not free to choose without consequences for stability, and that actuator dynamics matter for that (pp. 4-5).

**Relevant for a fair INDI-vs-PID benchmark (my assessment, not all stated by the authors).**
- The paper's own comparison is labelled "crude" (p. 10). The two outer loops are not gain-matched, and INDI has no integral term. The authors say the integral term is what matters for disturbance rejection (p. 10), so the comparison is effectively "INDI with an acceleration-based integral replacement" against "PID with I = 0.11". The tuning effort for each controller is not documented beyond "manually tuned" (pp. 7, 10).
- Sensor rates: both controllers received position at 4 Hz in E1. INDI also uses the 512 Hz accelerometer, so the comparison measures the combined effect of that extra feedback and the controller structure. The paper does not separate the two.
- Statistics: E1 has 7 repetitions per controller. E2 has 12 PID and 12 INDI flights, run in separate blocks, not interleaved. E3 has 25 repetitions per case. No statistical test is reported.
- Wind: E2 relies on an external mean wind figure, not on-site measurement. E1 is a steady jet, not a gust profile.
- Metric: E1 reports "maximum position deviation", averaged over repetitions. E2 reports "average maximum position error". Use the same definition in any new benchmark.
- Filters: display filter (ωn = 20, ζ = 0.7) differs from the controller filter (ωn = 50, ζ = 0.55), so Fig. 10 does not show the controller's own signal.
- Units: Table 1 and the RPM text use rpm, while Fig. 8 is labelled in Hz (p. 8). Check the units before reusing the values.
- Gains: the conflict between Sec. 2 and Table 2 (see (d)) must be resolved before the values are used as a reference set.
- Platform: all results are on a Bebop running Paparazzi, not PX4. Gains and filter parameters are not transferable without re-identification.
