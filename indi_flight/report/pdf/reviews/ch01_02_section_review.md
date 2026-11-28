# Section review: chapters 1 (Introduction) and 2 (Background)

Files: `indi_flight/report/pdf/chapters/01_introduction.tex` (114 lines), `02_background.tex` (169 lines).
Reviewer: fresh agent, did not write the text. Read-only review, no source edited.
Scope: technical correctness against sources, clarity for a control reader new to the project, no-development-trail rule, item R8 (notation table versus chapter 3).
Sources used: `indi_flight/GATES.md`, `GATE_STATUS.tsv`, `report/01..04, 03_validation.md`, `design/ref_airframe_model.md`, `design/airframe_requirements.md`, `design/a43_closing_s126.md`, `bench/params/quad5in_indi_defaults.params`, `bench/params/quad5in_indi_g1.params`, `sim/models/quad5in*/model.sdf`, `src/lib/indi_rate_control/`, `src/modules/mc_indi_{rate,pos}_control/`, `chapters/03_inner_loop.tex`, `04_outer_loop.tex`, `main.tex` (bibliography).
The tex line numbers below refer to the files as read on 2026-11-28.

## Verified without finding

No-development-trail rule: a grep of both chapters for file extensions, decision ids (D-...), session numbers (S###), Q numbers, A-numbers, G1-G8 gate names, "freeze", line citations and run/draw numbers returns nothing. Names used are module names, parameters (`MC_INDI_EN`, `MC_INDI_POS_EN`, `MPC_THR_HOVER`) and the criterion labels C1-C8. This is acceptable under directive item 4. (The writer's choice of C1-C8 for G1-G8 is consistent: Cn = Gn in the table.)

Verdicts (ch01 Table 1.1): C1 PASSED, C2 PASSED, C3 NOT PASSED, C4 PASSED, C5 PASSED, C6 NOT PASSED, C7 PASSED, C8 PASSED match `GATE_STATUS.tsv` rows G1..G8 exactly. "Six of eight" is correct (G1, G2, G4, G5, G7, G8).
Criterion titles match GATES.md: G1 Evidence integrity, G2 Stability margins, G3 Robustness, G4 Noise and effort, G5 Modes and transitions, G6 Defaults and identification, G7 Code, G8 Report.
C2 thresholds PM >= 45 deg and GM >= 6 dB: GATES.md "G2 Stability margins, measured" and 03_validation.md 3.2. C3 "300 randomised flights" and "no LOC, no sustained oscillation" are items 1 and 2 of G3 (but see R12). C6 "must pass C2, C3 and C5, requires C3": GATES.md G3-G8 FINAL item 7 and "Owner amendment S243", G6 consequence. C7 content (stock modules untouched, unit tests, format, size, review): GATES.md "G7 verdict (S252)". C8 content: GATES.md "G8 verdict (S257)". "Three noise profiles" (quiet, typical, harsh): GATES.md section 4.
"PID flown on the same draws": run 245 and 264 PID without LOC (GATES.md "G3 verdict at freeze-10 (S199)"), draw 3 item 2 PID passes (route B S242). Direction of the statement is correct; the wording is the problem (R1).
"Simulation only", Gazebo SITL, no real flight: GATES.md G8 limits, 04_limits.md 4.5.
Reference airframe table (Table 2.1), each value against `design/ref_airframe_model.md` and `sim/models/quad5in*/model.sdf`:
- mass 0.610 kg = 0.566 + 4 x 0.011 (SDF). Inertia 1.40/1.50/2.70e-3 recomputed by parallel axis from the SDF (base 1.022/1.122/1.944e-3 + 4 rotor links at 0.0795 m): matches. Units kg m^2 are confirmed (SDF is SI). This closes the writer's "unverified unit" note.
- rotor offset 0.0795 m (x and y), `motorConstant` 1.5e-6, `momentConstant` 0.01267, `maxRotVelocity` 2700, `timeConstantUp/Down` 0.033: all in the SDF. kQ/kT 0.01267 m: matches.
- k_T unit: thrust check 4 x 1.5e-6 x 999^2 = 5.99 N against m g = 0.610 x 9.81 = 5.98 N confirms F = k_T Omega^2, so the unit is N s^2/rad^2 (see R14).
- hover 999 rad/s (eRPM 9537 rpm = 998.7 rad/s, `ref_airframe_model.md` stock-PID check), u_h = (999/2700)^2 = 0.137 = `MPC_THR_HOVER` 0.137: consistent.
- J_r 5e-6 marked assumed: source says "5e-6 (ASSUMED)". Poles 14: `SIM_GZ_ERPM_POL` 14. W_MAX 2700 is the value in `quad5in_indi_defaults.params` (`MC_INDI_W_MAX 2700`), so the "unverified" W_MAX claim in NOTES_A is verified.
- G1 1757, 1640, 205: `quad5in_indi_defaults.params` and `quad5in_indi_g1.params`; unit rad/s^2 per unit normalised torque: `mc_indi_rate_control_params.yaml` ("Roll angular acceleration per unit of normalised torque", unit rad/s^2). Ratio 1757/1640 = 1.071 = 1.50/1.40 (inertia ratio), consistent.
- sample rates 800, 400, 266.7 Hz: report 01 section 1 and GATES.md G2 configurations.
Hover table claim "hover normalised thrust is the value stored in MPC_THR_HOVER": ref_airframe_model.md, `MPC_THR_HOVER` 0.137.
Eq. (1)-(5) of ch02 are algebraically consistent: subtracting the equation at t and t+T_s gives eq. (2); setting the left side to nu gives eq. (3); eq. (4) gives a first-order decay with time constant 1/K; eq. (5) is a first-order lag. G_2 "matters for the yaw axis only": firmware has only `MC_INDI_G2_Y` (`indi_rate_control.hpp` lines 59-62, `setG2Yaw`). u_i = (Omega_i/Omega_max)^2 matches `IndiEscThrust.hpp` and ch03.
"The INDI stack refuses to arm without rotor-speed telemetry or the rotor geometry": GATES.md G8 note S259 (commander external arming check refuses without fresh rpm on every motor and without `MC_INDI_W_MAX` and `CA_*` geometry); `design/airframe_requirements.md` R1, R2. The NOTES_A "unverified" item is verified.
PX4 chain (position -> thrust vector and attitude target -> attitude P -> rate setpoint -> torque setpoint -> allocator): stock PX4, consistent with `mc_indi_pos_control` (stock `PositionControl` cascade gives the acceleration reference, thrust output never published) and with report 02 section 1. "Only one module of each pair runs": report 01/02 section 1 and `rc.mc_apps` description. Body-rate feed-forward from the acceleration module to the rate module: `indi_rate_feedforward` topic (report 02 section 1).
The architecture diagram (`diagrams/architecture.tex`) is consistent with the text: stock and INDI module shown as alternatives selected by `MC_INDI_POS_EN` and `MC_INDI_EN`, attitude loop, allocator and estimator kept, feed-forward arrow to the INDI rate module.
Cross-references: all `\cref` labels used in ch01 and ch02 exist (ch:background, ch:inner_loop, ch:outer_loop, ch:analysis, ch:validation, ch:limits, ch:bringup, ch:conclusion, ch:traceability, sec:airframe, sec:criteria, tab:criteria, eq:*, fig:architecture). The reading guide order matches `main.tex`. The last build log (`build/main.log`) has no overfull box, undefined reference or warning.
Bibliography: the four cited INDI papers (Sieberling/Chu/Mulder JGCD 33(6) 2010; Smeur/Chu/de Croon JGCD 39(3) 2016; Smeur/de Croon/Chu Control Eng. Practice 73, 2018; Tal/Karaman IEEE TCST 29(3) 2021) match the published titles and volumes as far as I know them. Not re-checked online (see R17).

## Findings

### R1 MAJOR: ch01 lines 96-97, "Two failures belong to INDI alone"

Problem: the sentence says only "two failures" and does not say what they are or out of how many. The reader cannot tell if two runs failed in 300 or if two causes remain. The campaign evidence is much larger: 79 of 297 scored runs failed the oscillation test on at least one scoring method, two runs lost control (245, 264), and the later re-flies were halted. "Two failures ... PID does not fail them" also hides that PID shared some failures (run 008 oscillation fails for PID too; item 4 fails for PID on draws 0, 2, 3).
Source: GATES.md "G3 verdict at freeze-10 (S199)": item 1 FAIL runs 245 (2 Hz pitch divergence, corner C1) and 264 (corner C3, tilt > 60 deg), PID without LOC on both; item 2 FAIL 79 of 297. "G3 verdict, route B (S242)": draw 3 item 2 INDI q line 2.00 Hz, PID passes. 03_validation.md 3.3 verdict: "the 300-run result is not available for any firmware after freeze-10".
Fix text (replace lines 96-97):
"They are not robust enough over the full randomised campaign. In the 300 flights, two lost control (one in a growing 2 Hz pitch oscillation, one by tilting past 60 degrees when a fault hit a saturated vehicle with a weak motor), and 79 of 297 scored flights showed a sustained oscillation on at least one of the two scoring methods. PID flown on the same draws did not lose control. Two INDI-specific limits remain after the repair attempts: a 2 Hz pitch oscillation with slow motors, and the loss of control at the saturated weak-motor corner. The campaign was not repeated on a later firmware."

### R2 MAJOR: ch01 line 95, "stable with good margins"

Problem: the evidence calls the rate-loop margins thin, and only one rate cell was measured. "Good margins" is not supported and contradicts the abstract's own "46.9 deg against a limit of 45 deg".
Source: GATES.md "G2 verdict at freeze-10 (S194)", limit (2): "rate and attitude spot margins thin (+1.9/+3.0 deg)"; spot rate cell roll800_fwdef_s2 PM 46.9, no second key; 03_validation.md 3.2 evidence limits 2-3; report 01 section on margins: "only the roll spot cell was scored for the rate loop ... pitch and yaw rate margins and the 266.7 Hz measured-path cell were not flown on the frozen pair". Outer loops: 24/24 cells, PM >= 49.1, GM >= 13.5 dB (key 2 blocked on agreement on 3 cells, both keys above limits).
Fix text (replace the first sentence of the box, line 95):
"In simulation the controllers meet the stability limits. The outer loops have a phase margin of at least 49.1 degrees in 24 cells. The rate loop was measured in one configuration (roll axis) at 46.9 degrees against a limit of 45 degrees, so this margin is thin; pitch and yaw rate margins were not measured."

### R3 MAJOR: ch01 line 84 (C5 row) and line 95, modes and transitions "behave as specified"

Problem: C5 PASSED with rows dropped or not tested, but the table reads as full coverage ("All flight modes ... behave as specified").
Source: GATES.md "G5 verdict at freeze-10 (S198)": "Not tested: G5.6 and G5.11 z reset (owner Q8(b)); accel-only offboard and take-off on an offboard setpoint alone (owner decision F-8); G5.10 SAT part dropped (Q21: no stack reaches 4 motors >= 0.99 for 1 s)". Mission and RTL have one scoring method only; mission waypoint margin 0.03 m (0.970 m against 1.0 m). 04_limits.md line 54.
Fix text for the C5 "Meaning" cell:
"Position, altitude, stabilised, acro, hold, mission, take-off, land, return and offboard modes; mode switches; failsafes; kill and re-arm; estimator resets. Not tested: a false maybe-landed flag, a vertical estimator reset, sustained thrust saturation, and offboard acceleration-only setpoints. Mission and return are scored by one method only."
(Keep it shorter if the table is tight, but the "not tested" part must appear.) In the key-result box, change "handle noise, modes and transitions" to "handle noise and the tested modes and transitions".

### R4 MAJOR: ch01 lines 45 and 68, "written before the tests" / "fixed before the tests"

Problem: the criteria names and thresholds were written before the first test, but several test definitions were changed after first tests, some of them relaxing a limit or changing a scoring rule. A reader of lines 45 and 68 (and the abstract) will assume no later change. The owner directive item 3 also asks for a clear reasoning line; honesty on this point protects the verdicts.
Source: GATES.md "Owner amendments S187 (Q20, Q21, Q22)" (G4 guard rule; G4 NOT PASSED at freeze-9, PASSED after the Q20 rule), "S197" (GNSS delay range narrowed from +-100 to +-50 ms; G5.5 trajectory limit H_lim = max(0.5 m, tau_att x v_rms)), "S208" (Q27 test-definition changes after the first G3 test), "S214" (G3 steady-state window), "S243" (item 5 reading changed, PID guard on item 4). G3-G8 FINAL (S94) says "Changes after a gate's first test only fix a test defect, logged here".
Fix text (line 68): "Eight acceptance criteria were fixed before the tests, with thresholds. Where a test turned out to be defective, its definition was amended afterwards by the project owner and the change was logged; \cref{ch:validation} lists each such change next to the result it affects." And line 45: "Test them against acceptance criteria that were fixed before the tests (later test-definition fixes are listed in Chapter X)." Ch06 (validation) must then carry that list; add it to the hand-off for the ch06 writer.

### R5 MAJOR: ch02 lines 8-13, 31, 150-155 (R8 part): the symbol u has three incompatible meanings, and G_1^{-1} is not defined

Problem: in ch02, `u` is the "actuator state vector" (rotor states, thrust-like, in [0,1]) and `G_1` maps it to angular acceleration, but then `G_1^{-1}` in eq. (3) does not exist (4 rotor states, 3 axes: non-square) and G_1 in the table (1757 rad/s^2 per unit normalised torque) is a 3x3 diagonal effectiveness in torque space. In ch03, `u` is the per-axis normalised torque in [-1,1], rotor states are `u_i` and `u_rot`, and `u = B (u_rot - u_trim)`. In ch04 (line 224), `u` is the mean of the four rotor states. The reader of ch02 reaches ch03 with a different object under the same letter.
Source: `src/lib/indi_rate_control/indi_rate_control.hpp` header ("Control law in normalised torque space"), yaml `MC_INDI_G1_R` ("angular acceleration per unit of normalised torque"), ch03 lines 38-39, 164-168, ch04 lines 224-225.
Fix: state in ch02 that the law is applied in normalised torque space. Concrete edits:
1. Line 8: replace "the actuator states $\mathbf{u}$" by "the normalised torque $\vect u$ (roll, pitch, yaw) that the rotors produce".
2. After eq. (1), add: "Here $\vect u$ is the normalised torque of the three axes, so $G_1$ is a diagonal $3\times3$ matrix and can be inverted. The rotor speeds enter through the measured torque $\vect u = B(\vect u_{\mathrm{rot}}-\vect u_{\mathrm{trim}})$ of \cref{sec:rotor_speed}."
3. In section 2.2 (line 64-70), call the rotor states $u_{\mathrm{rot},i}$ and the vector $\vect u_{\mathrm{rot}}$ (as ch03 line 168 does), and add the measured-torque relation with $B$ and $\vect u_{\mathrm{trim}}$. Keep `u_i = (\Omega_i/\Omega_max)^2` as the definition of $u_{\mathrm{rot},i}$... but ch03 line 162 and `eq:u_state` use `u_i`; either keep `u_i` in both and say "$\vect u_{\mathrm{rot}}$ collects the $u_i$", or rename in both. Preferred: keep `u_i` (rotor), `u_rot` (vector), `u` (torque).
4. Ch04 line 224: rename the mean rotor state (for example $\bar u_{\mathrm{rot}}$) so `u` keeps one meaning. This is outside the files under review; pass to the ch04 reviewer.

### R6 MAJOR: ch02 notation table (lines 146-168), rows to add or change (item R8)

Chapter 3 uses symbols that the table does not define, or defines differently. Exact changes (symbol | meaning to put in the table):

Add:
- `$B$` | control-effectiveness matrix of the rotors: maps rotor states to normalised torque, built from the control-allocation geometry (`CA_*`).
- `$\vect u_{\mathrm{rot}}$`, `$\vect u_{\mathrm{trim}}$` | rotor states $u_i$ collected in a vector; trim (hover) rotor state.
- `$b$` | blend state per axis (normalised torque): slow correction that carries the steady difference between modelled and measured torque (ch03 eq. 3.10, also used for thrust in ch04).
- `$t_b$` | time constant of the blend (s), `MC_INDI_ACT_BLD` (rate) and `MC_INDI_POS_TB` (acceleration loop).
- `$\ell$` | lead scale, `MC_INDI_LEAD`: 1 turns the lead on, 0 off.
- `$c$` | lead gain, $c=\min(\ell K\tau_a, 2)$, dimensionless: weight that compensates the actuator lag in the rate law.
- `$\Delta_{\max}$` | largest increment of normalised torque per cycle, `MC_INDI_INC_MAX` (default 1: no bound).
- `$\omega_{\mathrm{ref}}$` | rate setpoint (rad/s) (used in ch02 eq. 4 and ch03; absent from the table). Also `$\dot\omega_{\mathrm{ref},f}$` | filtered derivative of the rate setpoint.
- `$H$` | filter chain applied identically to angular acceleration and to torque (second-order low pass followed by the derivative filter).
- `$u_{\mathrm{mod},f}$`, `$u_{\mathrm{meas},f}$` | filtered modelled and measured torque (these two appear in ch03 eq. 3.9-3.10 and in ch04).
- `$\Omega_{\max}$` | rotor speed at full command, `MC_INDI_W_MAX` (the row $u_i$ uses it but it is not listed alone).
- `$\vect g$`, `$R$`, `$\vect f_b$` | only if ch02 keeps `a` in the table; otherwise move to ch04 (see R8).

Change:
- Row `$\mathbf{u}$, $\mathbf{u}_c$`: "normalised torque of the three axes and its command" (see R5). Row `$u_i = \ldots$`: "normalised state of rotor $i$ (proportional to its thrust)".
- Row `$\vect\nu$`: add "(plain $\nu$ in the per-axis equations)".
- Row `$G_1$`: "control-effectiveness matrix (diagonal; rad/s$^2$ per unit of normalised torque)". Row `$G_2$`: "rotor spin-up matrix, yaw only (rad/s)" with unit.
- Row `$\tau_a$`: "time constant of the actuator (motor) lag; the plant value in Table 2.1, the controller setting is `MC_INDI_ACT_TC`". This matters for the main limit in ch07 (model mismatch hypothesis).
- Row `$K$`: "bandwidth gain of one rate axis (1/s), set per axis" (it is a diagonal matrix in eq. 4, and ch03 says it is halved while `MC_INDI_ID_OK` is 0).
- Row `$T$`: see R8.
- Intro sentence (line 139-140): see R7.

### R7 MINOR: ch02 lines 139-140 and passim, bold versus plain convention (item R8)

Problem: the sentence "Bold symbols are vectors or matrices" is wrong in the table itself: `G_1`, `G_2`, `K`, `B` are matrices printed plain, `\mathbf{...}` (upright bold) and `\vect{...}` (bold italic, `\symbf`) are both used (eq. 1, 3: `\mathbf{u}`, `\mathbf{f}`; the rest `\vect\omega`, `\vect\nu`). Ch03 writes `\nu`, `\omega`, `\dot\omega_f`, `u` plain in per-axis equations, bold `\vect\nu` in its table and caption, and ch04 uses `\vect a_f`. A reader sees `\nu` bold in ch02 and plain in ch03 with no rule.
Fix: (a) replace every `\mathbf{` in ch02 by `\vect{` (lines 8, 11, 19, 24-25, 27, 31, 41-42, 59, 66, 96, 154, 160, 162-163); (b) replace line 139-140 by: "Vectors are written in bold, matrices in plain capitals ($G_1$, $G_2$, $B$, $K$). A subscript $f$ marks a filtered signal. The design chapters work axis by axis: there the same symbols appear without bold ($\nu$, $\omega$, $\dot\omega_f$, $u$) and mean the component of one axis; $G_1$ is then the diagonal entry of that axis."
(c) Make the same rule in ch03 caption of Figure 3.1 and Table 3.1: they use `\vect\nu` and `\vect\omega` for a one-axis diagram; this should be plain per the rule (ch03 reviewer).

### R8 MINOR: ch02 lines 162-164, notation of `a` and `T` clash with ch04

Problem: ch02 defines `a` as "specific force or linear acceleration measured on board" (two different quantities, no frame) and `T` as "collective thrust". Ch04 defines the specific force `f_b = R^T (a - g)`, the measured acceleration `a_f = R f_{b,f} + g` (world frame north-east-down, body frame forward-right-down) and `\vect T` as the specific thrust vector in m/s^2, with scalar magnitude `\tau`. So `T` is a scalar force in ch02 and a vector in m/s^2 in ch04.
Source: ch04 lines 74-90, 124.
Fix: ch02 rows: `$\vect a$` | "linear acceleration of the vehicle in the world frame (m/s$^2$), computed from the measured specific force"; `$\aref$` | "acceleration reference of the outer loop (world frame)"; `$\vect T$` | "specific thrust vector (thrust per unit mass, m/s$^2$), body down axis, see ch04"; delete "T collective thrust" or rename to `$\tau$` | "magnitude of $\vect T$". Line 70 then reads "the collective thrust $\tau$" if kept.

### R9 MINOR: ch02 line 85, sensors feeding the loops

Problem: "The gyroscope and the accelerometer feed the rate loop and, in the INDI case, the acceleration loop" suggests the rate loop uses the accelerometer. The rate module uses only the gyro rate and its derivative (`vehicle_angular_velocity` `xyz_derivative`); the acceleration module uses the accelerometer (`vehicle_acceleration`).
Source: `McIndiRateControl.cpp` (angular_velocity.xyz_derivative, no accelerometer input), report 01 section 1 input table, report 02 section 1 ("Specific force: `vehicle_acceleration`").
Fix: "The gyroscope feeds the rate loop, with its derivative as the measured angular acceleration. The accelerometer feeds the acceleration loop in the INDI case."

### R10 MINOR: ch02 lines 69-70, how the measured rotor states give torque and thrust

Problem: "With the control allocation geometry, the measured u_i give the torque and the collective thrust T that the rotors really delivered." In firmware the torque comes from the allocation geometry through B; the thrust is the mean of the four normalised rotor states (`IndiEscThrust::meanRotorThrust`), not a geometry product, and requires exactly four motors reporting.
Fix: "The allocation geometry turns the measured rotor states into the torque of the three axes. The mean of the four rotor states gives the collective thrust (quadrotor)." Links to R11.

### R11 MINOR: ch01 lines 58-59 and abstract, "makes no assumption specific to one vehicle"

Problem: the outer-loop measured thrust is built for four rotors; ch04 line 225 says "The mean is for four rotors (a quadrotor)", and the module treats any other count as invalid (`IndiEscThrust.hpp`: motors 0-3 only, invalid if one is missing). The claim "generic design" and "PX4 multicopters" in the abstract is stronger than the code. Evidence is one quadrotor.
Source: `src/modules/mc_indi_pos_control/IndiEscThrust.hpp`; report 02 section 1 line 198 ("over the four motors").
Fix: line 58: "The design is not tied to one vehicle, with one exception: the measured collective thrust assumes four rotors. Other layouts are untested." Same sentence for the abstract (main.tex; not in scope but noted).

### R12 MINOR: ch01 lines 26-28 and ch02 lines 40-44, "no integrator, no estimator" versus the blend

Problem: both chapters say there is no integrator and no estimator. The design does include a slow state that corrects the steady command/output gap, and ch04 line 284 calls it "an integral action with the time constant t_b". Ch03 also states the blend restores a steady correction. The claim is true for the basic law but a careful reader will meet the contradiction in ch03/ch04.
Source: `indi_rate_control.hpp` header (blend: "restores the integral action of the model state against a steady command/output gap"); ch04 lines 268-284.
Fix: ch01 line 28: "...so no integrator on the error and no disturbance estimator are required. A slow blend state, introduced in Chapter 3, only corrects a steady gap between commanded and delivered thrust." Same for the key-result box in ch02 (line 43): add "apart from the slow blend of Section 3.4".

### R13 MINOR: ch02 lines 19-29, 24-25, eq. (2) and (3): small gaps in the derivation

Problem: (a) `\Delta\dot{\mathbf u}` is not defined (should be $\dot{\mathbf u}_c-\dot{\mathbf u}_f$ or the derivative of the increment). (b) Setting the new state equal to $\mathbf u_c$ assumes an instant actuator; the text says so only after eq. (5). (c) Eq. (3) has no actuator-lag lead, but ch03 eq. (3.5) uses $(1+c)\dot\omega_f$ and $c\dot\omega_{\mathrm{ref},f}$; the reader finds the law different from ch02 with no warning. (d) The first-order lag is applied to the command of the rotor state, while ch03 applies it to torque with the allocated command; fine, but say "the same lag applies to the normalised torque".
Fix: after eq. (3) add: "This is the basic law. It assumes that the actuator state reaches the command within one sample. Chapter 3 adds a lead term that compensates the actuator lag of eq. (5), and the rotor spin-up term $G_2$ on the yaw axis." After eq. (2): "$\Delta\dot{\mathbf u}$ is the change of the actuator rate between the two samples."

### R14 MINOR: ch02 Table 2.1 (lines 112-130), units and meaning

Problem: (a) `k_T` has no unit; verified unit N s^2/rad^2 (thrust of one rotor = k_T Omega^2; 4 k_T 999^2 = 5.99 N against m g = 5.98 N). (b) "Rotor position (each axis, +-) 0.0795 m": the rotors sit at x = +-0.0795 m and y = +-0.0795 m, so the distance from the centre is 0.1124 m; a control reader can take 0.0795 m as the arm length. (c) "Moments of inertia ... $1.40$, $1.50$, $2.70\times10^{-3}$" reads as only the last number scaled; write "$1.40\times10^{-3}$, $1.50\times10^{-3}$, $2.70\times10^{-3}$". (d) `k_Q/k_T` has no explanation (yaw torque per unit thrust, m). (e) "Motor poles (telemetry) 14" is the number used to convert electrical to mechanical rotor speed; say so. (f) The time constant row is the plant motor time constant; the controller setting `MC_INDI_ACT_TC` is separate and is set to 0.033 (same value), but the mapping is marked unverified in the parameter file ("UNVERIFIED mapping tau->ACT_TC"). A short remark avoids the reader assuming the identity.
Fix: apply (a)-(f) in the table; add "N s$^2$/rad$^2$" to the `k_T` row, "(arm length $0.112$ m)" to the rotor-position row.

### R15 MINOR: ch02 lines 132-133, yaw effectiveness 205 without its caveat

Problem: the text calls 205 the "derived value G_1 for yaw" and gives only the J_r assumption. The source records an unresolved discrepancy: a flight-based identification gave 163-166, 20 % lower than the derived 205.3.
Source: `design/a43_closing_s126.md` line 50 ("yaw ... 205.3 ... 163-166 (-20 %)"), `report/01_inner_loop_design.md` line 325, `report/UNVERIFIED_S217.md` ("J_r / G2_Y 27 vs IV 163-166, open: needs identification").
Fix: append to line 133: "The yaw value was derived from the airframe data. A fit to simulated flight data gave about 20 % less (163 to 166); the difference is not resolved."

### R16 MINOR: ch01 Table 1.1 qualifiers (rows C1, C2, C7, C8)

Problem: several PASSED rows drop qualifiers the verdict itself carries. (a) C2 "measured in flight": all flights are simulated (also abstract "Measured in flight"). (b) C2 omits the delay-margin rule (at least two control periods plus telemetry latency). (c) C7 "flash size": the build fits a v5x board (+64.8 kB flash, 8.9 kB left) and overflows fmu-v6x by 23.5 kB with both modules. (d) C8 "PASSED with the listed limits": 47 report claims marked unverified. (e) C1 was frozen with stated evidence limits (G1.5 deferred per injector).
Source: GATES.md "G7 verdict (S252)" (e); "G8 verdict (S257)" limits; "G1 FINAL"; "G2 Stability margins".
Fix: C2 cell: "...measured in simulated flight by multisine injection, delay margin of at least two control periods plus telemetry latency, and clean attitude steps." C7 cell: add "The firmware fits a v5x flight controller; it does not fit a v6x with both modules." C8 cell: "...are written down; some claims are marked unverified (see Chapter X)." In the box line 93-94 or a footnote under the table: "PASSED means passed with the limits listed in \cref{ch:limits}."

### R17 MINOR: ch01 line 15 and bibliography, "flown on aircraft"

Problem: the cited aircraft paper (Sieberling et al. 2010) is, to my recollection, a simulation study on a transport aircraft model, not a flight test; "flown" for aircraft may be wrong. I could not confirm offline, so this is unverified; the writer's NOTES_A already marks the claim "from the titles, not re-read". Also the `px4guide` bibliography entry is never cited in the text, and the original INDI references are absent.
Fix: write "has been applied to aircraft, micro air vehicles and aggressive quadrotor flight" (neutral), or cite precisely. Cite `px4guide` in section 2.3 or delete the entry.

### R18 MINOR: ch01 line 56, "Every flight mode"

Problem: the design covers every multicopter mode (report 02 section 1, `mc_indi_pos_control` replaces `mc_pos_control` in all modes), but the evidence does not: orbit, follow and goto were not flown in the gates; offboard acceleration-only and take-off on an offboard setpoint alone were explicitly not tested (owner decision F-8).
Fix: "Every flight mode. All manual, assisted, automatic and offboard modes go through the same two modules by design; the modes that were flown in the tests are listed in \cref{ch:validation}."

### R19 MINOR: ch01 line 55, "the vehicle flies exactly as before"

Problem: not demonstrated by flight; the support is a zero-line diff over the stock paths and the fact that the INDI modules do not start. "Exactly" is stronger than that.
Source: GATES.md "G7 verdict" (a): 0 lines over the 6 stock paths, 75 files.
Fix: "With both at zero the INDI modules are not started and the stock modules run unchanged (checked by a code diff)."

### R20 MINOR: ch01 Table 1.1, row C3

Problem: the "Meaning" lists only "no loss of control and no sustained oscillation"; the G3 pass rule also requires steady state, tracking (lemniscate RMS <= 0.5 m), recovery after a fault or gust, and rate-mode hold in every valid run. A reader may think C3 failed only on two items while items 3-6 also had misses (15 item-3 misses in 297 scored runs).
Source: 03_validation.md 3.3 ("Pass items per run: 1 ... 6"); GATES.md S199 verdict.
Fix: "A campaign of 300 randomised simulated flights: no loss of control, no sustained oscillation, and steady-state accuracy, tracking, recovery and hold within limits in every run."

## Clarity notes (no severity, for the writer)

- Ch02 reads well; the order (principle, rotor speed, PX4 chain, airframe, notation) is right. The "What INDI buys" box is clear.
- Ch01 lines 22-34 (benefits) say "The inner loop needs the control effectiveness of each axis and the time constant of the motors"; add "and the maximum rotor speed", since without it the measured path and the arming check refuse (R1 of the airframe requirements).
- Ch01 uses "C1-C8" and ch02 uses nothing for gates, which is fine, but the appendix must map C-numbers to the gate evidence; the table points to it (`ch:traceability`).
- Equation numbering: ch02 uses `\cref{eq:...}` forms ("Equation (n)"); the sentence "\Cref{eq:plant} holds at the present time and again one sample later" is clear.
- Ch01 line 63 and 62: "\Cref{ch:limits} and \cref{ch:bringup} say what this means" reads well.

## Totals

BLOCKER 0, MAJOR 6 (R1-R6), MINOR 14 (R7-R20), total 20.
Most important: R1/R2/R3 together, the one-paragraph result in ch01 (lines 92-98) overstates margins and mode coverage and understates the G3 failure picture (79 of 297 oscillation runs, two losses of control); R5/R6 are the next priority because the notation table does not define the symbols ch03 uses and `u` has three meanings across ch02-ch04.
