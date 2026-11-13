# Blaha, Smeur, Remes 2024: Control of Unknown Quadrotors from a Single Throw

Status: complete (whole paper read from the local text; section refs use the paper's own labels).

## 1. Citation and URL

- T.M. Blaha, E.J.J. Smeur, B.D.W. Remes, "Control of Unknown Quadrotors from a Single Throw", IROS 2024 (submitted version, arXiv v3, 30 Aug 2024).
- https://arxiv.org/abs/2406.11723
- Code: github.com/tudelft/indiflightSupport (branch iros_imav_2024); data DOI 10.4121/0530be90-cc6c-4029-9774-670657882906 (p.1 footnotes). Not downloaded.

## 2. Summary

- Recovers a quadrotor from a throw with no prior control parameters, using RLS to identify effectiveness and a per-motor model in 450 ms (Abstract; Sec. II-B).
- Excitation: two steps plus a decreasing ramp per motor, aborted on a gyro-margin rule (Sec. II-B.d, Fig. 3).
- Inner loop is actuator-space INDI on angular rate and specific force; attitude and NDI position loops sit on top (Sec. II-A, Eqs. 6-9).
- Runs at 2 kHz on an STM32H743 in a Betaflight fork, 3-inch quad (Sec. II-C). 57 live launches, all stabilised (Sec. III-A).
- Simulation: 1000 craft, RMS parameter error mostly below 10% (Table II). Live fits differ from bench values by 10-35% (Table I). No PID baseline is given.

## 3. INDI formulation

- Incremental model, Eq. (1): Δν = B1 ΔT + B2 Δω̇. ν = [f_x f_y f_z ṗ q̇ ṙ]^T, ΔT is the 4-vector of rotor thrust increments, B1 and B2 are control-effectiveness matrices (Sec. II-A, after Eq. 1).
- Normalised command u = T_s/T_max (Sec. II-A, after Eq. 1).
- Linearised, Eq. (7): ν − ν0 + B2 ω̇0 ≈ B1 k ω_max² + (B2 ω_max² / (2 ω0 τ)) Δu. The ω̇ approximation only matters for yaw (Sec. II-A, Eqs. 4-5 and text).
- Solver: Eq. (7) solved by pseudo-inverse, or active-set if bounds on u must hold (Sec. II-A, after Eq. 7, ref. [8]). This is actuator-space INDI, not torque-space mixing. The torque-space PID path is described as the conventional alternative (Sec. II-A.a).
- Rate loop: last three entries of ν_r = D∘(Ω_r − Ω) (Sec. II-A.b). Gains set by pole placement with damping ζ_D = 0.8 (Sec. II-A.d).
- Attitude: Ω_r = 2 arccos(q_eB)_w (n̂∘A), Eq. (8). Gains ζ_A = 0.7, ζ_V = 0.7, ζ_P = 0.9 (Sec. II-A.b-d).
- Position: a_I = R_IB f_B + G_I, Eq. (9). PID generates a_I,r from position and velocity estimates (Sec. II-A.c).
- Filtering: ν0, u0 and Ω̇0 are low-passed with a 2nd-order Butterworth at 15 Hz. All signals share one filter so Eq. (1) stays valid (Sec. II-A.a).

## 4. Actuator model and actuator-state source

- ESC map, Eq. (2): u = [κδ + (1−κ)√δ]², κ ≥ 0 unknown (Sec. II intro; bracket reconstructed from text, see Sec. 10).
- Rotor dynamics: first-order lag τω̇ = ω_s − ω, with thrust T = kω² (Sec. II intro, Eq. 3).
- Idle offset: ω_s = ω_max(κδ + (1−κ)√δ) + ω_idle, Eq. (14). ω_max is not modelled as battery- or airflow-dependent; it is estimated online (Sec. II-B.b).
- Reparametrised model, Eq. (15): ω = aδ + b√δ + ω_idle − τω̇, with ω_max = a+b and κ = a/(a+b) (Sec. II-B.b).
- Measured signals: rotor speed ω and its derivative ω̇ (differentiated), body rate Ω, specific force f (Sec. II-B.c; Sec. II-A.a). If k is unknown, u0 comes from an emulated actuator lag U0 = U/(τs+1) instead of measured ω (Sec. II-A.a).
- Filtering: 20 Hz 2nd-order Butterworth on identification inputs (Sec. II-B.c, after Eq. 16). Filtering is reported as effective (Sec. III-A, Fig. 4).
- Rotor speed source: "motor rotation rate feedback at sufficiently high rate" from Betaflight, not named further (Sec. II-B.c; Sec. II-C). Protocol and rate of the ESC telemetry are not stated.
- Sync: everything runs in one 2 kHz loop on the MCU. No latency or jitter figures are given (Sec. II-C).

## 5. Online identification

- Method: standard RLS with forgetting, Eqs. (10)-(13). P0 = 10²I, Θ0 = 0. Regressors and outputs are pre-scaled to unity for single precision. P entries are capped at 10^10 (Sec. II-B.a).
- Forgetting factor: printed as λ = exp(P_s/0.2). Intended to decay errors by 63% in 0.2 s (Sec. II-B.a). See Sec. 10 on the sign.
- Parameter structure: 6 RLS filters that share regressors. Force rows need 4 parameters each; rotation rows need 8 (Sec. II-B.c, after Eq. 16).
- Count of 52 (Abstract): my reading of Table I is B1 (6 rows × 4 motors = 24) + B2 (3 × 4 = 12) + ω_max, κ, ω_idle, τ per motor (4 × 4 = 16).
- Excitation: motors excited one after another, two steps then a decreasing ramp (Sec. II-B.d, Fig. 3). Chosen because a short burst can exceed the ±2000°/s gyro range, and model-independent sine inputs are unsafe without prior knowledge (Sec. II-B.d).
- Timing in the experiment: spool-down 250 ms, then excitation, then fit complete and switchover after 450 ms (Sec. III-A).
- Convergence: parameters converge "immediately" once excitation starts. Motors 2-4 do not converge before their own step, because only idle speed precedes it (Sec. III-A, Fig. 4). No per-parameter convergence time is given.
- Identified quantities: B1 and B2 (effectiveness), ω_max, κ, ω_idle, τ per motor (Sec. II-B, Table I). Gains are not identified; they are tuned from τ and ζ (Sec. II-A.d).

## 6. Allocation and saturation

- Inner-loop allocation via pseudo-inverse, or active-set when bounds on u must hold (Sec. II-A, after Eq. 7). Which solver ran in flight is not stated.
- Feedback is disabled until identification ends (Sec. II-B.d).
- Gyro saturation is handled by the excitation abort rule: abort if Ω exceeds Ω_e + ΔΩ/n_l, with n_l the motors still to excite (Sec. II-B.d). Fig. 3 truncates motor 1 and 2 commands to protect the roll sensor.
- Command saturation during closed-loop flight is not reported. Motor commands in Fig. 5 are described as "relatively smooth" (Sec. III-A).

## 7. Hardware/firmware and quantitative results

- Platform: 3-inch quad, STM32H743, ICM-42688-P IMU, Betaflight fork "INDIflight" at 2 kHz. Attitude from Betaflight's Mahony filter. Heading, velocity and position from constant-gain observers. Optical markers are used for position control only, not for identification (Sec. II-C).
- Nominal INDI parameters from bench tests and geometry (Sec. II-C.a).
- Live: 57 controlled launches, logs kept for the last 20 only (Sec. III-A). Throws to 3.5-4 m with a pseudo-random initial rotation of 0-10 rad/s (Sec. II-C.a). Initial rate error above 20 rad/s; rate tracking within 200 ms; slight oscillation 1200-2000 ms (Sec. III-A, Fig. 5).
- Table I (live, 20 launches, mean vs bench reference), my percentages:
  - B1,z·k·10^6, motors 1-4: −0.658, −0.592, −0.792, −0.684 vs −0.621 (−6%, +5%, +28%, +10%).
  - B1,p·k·10^6: magnitudes 29.6, 30.7, 29.9, 27.4 vs 23.44 (+17% to +31%).
  - B1,r·k·10^6, motors 1 and 3: −6.59 and +6.67 vs ±2.99 (about 2.2×). Motors 2 and 4 are −22% and −28%.
  - B2,r·10^3: −0.915, 0.945, 1.061, −0.961 vs ±1.011 (within ±10%).
  - ω_max: 5253, 5278, 4812, 4919 vs 4113 (+17% to +28%).
  - κ: 1.118, 1.184, 0.994, 1.000 vs 0.460 (not close).
  - ω_idle: 504-517 vs 450 (+12% to +15%).
  - τ: 25.9-26.6 ms vs 20 ms (+30% to +33%).
- Simulation: 1000 asymmetric craft, throws near 4 m, κ in [0.25, 0.75], τ in [15, 35] ms (Sec. II-D). All 1000 stabilised (Sec. III-B). Table II RMS, my normalisation by the "nominal" column: B1 about 6-11%, ω_max 1-8%, τ 2.5-4%, κ 20-24%.
- Comparison with RL: "orders of magnitude" fewer samples than about 300,000 for RL (Introduction; Conclusions, Sec. IV). Not an equal-task comparison, and no PID comparison is made.

## 8. Limitations stated by the authors

- Only one 3-inch quad tested. Other designs and vehicle types need study (Sec. IV).
- Needs high-rate motor-speed feedback and known IMU location and orientation. Removing these is future work (Sec. IV).
- Excitation could be more sample-efficient. Adaptation is not kept active in recovery or later flight (Sec. IV).
- Bench references are "not a ground truth" (Sec. III-A).
- Motor model (15) and T = kω² "do not hold globally" in flight. Inflow effects are missing from bench and simulation (Sec. III-A).
- Covariance is capped at 10^10 instead of adaptive forgetting (Sec. II-B.a).
- Damping ζ may be too low, given the oscillation (Sec. III-A).
- Simulation reuses the same INDIflight code (Sec. III-B), so it tests the estimator under the model's own assumptions, not model mismatch.

## 9. Implications for a PX4 INDI (my interpretation, not claims from the paper)

- Effectiveness accuracy: the paper has no sensitivity study of recovery vs. B1 error, so no required accuracy is established. Live recovery worked with B1 off by 10-30% from the bench values (Table I), but those bench values are themselves uncertain (Sec. III-A). Table II suggests fits within about 10% in sim. Treat that as a benchmark, not a verified requirement.
- Identification speed: a usable fit took about 450 ms on this quad (Sec. III-A, Abstract). The RLS design time constant is 0.2 s (Sec. II-B.a). Heavier airframes with slower rotors may need longer. This is unverified.
- Telemetry prerequisite: the method needs rotor speed at about 2 kHz (Sec. II-B.c, II-C). Whether PX4's ESC telemetry path can supply this is unverified and needs checking in the drivers.
- Priors: κ and τ differ from bench values by roughly 2× and 30% in flight (Table I). Bench priors may be far off, so the identify-from-zero design matters more than bench accuracy.
- Gating: excitation needs the gyro-margin abort (Sec. II-B.d) and a switch-over gate (Sec. III-A). A PX4 port would need both.
- No PID baseline exists in this paper (only passing mentions, Sec. II-A.a and II-A.d). Any "INDI beats PID" statement needs a separate experiment.

## 10. Unverified / unclear points

1. Equations are reconstructed from a two-column text extraction: Eq. (2) bracket, Eq. (5) ("max Δu"), Eq. (6), Eq. (7), Eq. (14), Eq. (15). Check against the local PDF (research/raw/papers_dl/blaha_iros_2406.11723.pdf) before quoting.
2. The forgetting factor is printed as λ = exp(P_s/0.2), which is above 1. The intended form is probably exp(−P_s/0.2), which gives the stated 63% decay in 0.2 s. Sign likely lost in extraction.
3. The excitation abort rule (ΔΩ/n_l vs 0.5·n_l) and the "halves the permissible margin" remark (Sec. II-B.d) are garbled. The intended worst-case argument is unclear.
4. The text cross-references "II-B.0.b" (Sec. II intro). Probably a typo for II-B.b.
5. The rotor-speed source is unnamed (protocol, rate, ESC). The "2 kHz" figure is the whole loop, not a stated telemetry rate.
6. Table II: the ground-truth column reads 0.000 for B1,x/y, B2,p/q and ω_idle. That contradicts Table I and Eq. (14), where ω_idle ≈ 450. The "mean-absolute" label and normalisation are unclear.
7. κ: live fits are about 1.0-1.18 vs bench 0.46. κ > 1 gives a negative √δ term in Eq. (2), which the paper does not discuss. Simulation range [0.25, 0.75] does not cover it. Table II RMS for κ is 20-24% of nominal, which conflicts with the Abstract's "within 10%".
8. B1,r for motors 1 and 3 is about 2× bench. The paper attributes this to structure and inflow in the text only (Sec. III-A).
9. Per-motor excitation durations and how the 450 ms splits across motors are not stated.
10. Which allocation solver ran in flight (pseudo-inverse or active-set) and whether u-bounds were enforced are not stated (Sec. II-A).
11. Outer-loop (attitude, position) rates are not given. Only the 2 kHz figure for the whole algorithm appears (Sec. II-C).
12. Units: B1·k·10^6 needs the propeller thrust constant k, which is not reported. PX4 units cannot be derived from Table I.
13. Results: 57 launches, but logs exist only for the last 20. No failure count or per-launch table is given, despite "every time" in the Abstract.
14. Code and data (indiflightSupport branch, DOI) were not checked. Not downloaded per instructions.
