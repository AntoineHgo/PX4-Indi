# Review of chapter 4 (outer loop): chapters/04_outer_loop.tex

Scope: numbers, equations, signs, frames, units, parameters, verdicts against firmware (src/lib/indi_accel_control/, src/modules/mc_indi_pos_control/), the params yaml, bench/params/quad5in_indi_defaults.params, DECISIONS.md and GATES.md. Line numbers are tex lines.
Totals: BLOCKER 0, MAJOR 4, MINOR 13.

## Verified without finding
- Eq fb, a_f = R f + g, g = (0,0,+g), T = -c z_b, T_f = -g_t u_f z_b, g_t = g/h_t, collective = c/g_t, T_c = T_f + (a_ref - a_f): match IndiAccelControl::update (indi_accel_control.cpp ~L330-430; thrust_gain = g/h_t, mean_thrust_per_command 1).
- Modelled-force cancellation T_c = a_ref - g: holds in code (substituted f_b uses same delayed u plus the same blend, same filter).
- Blend equation, bound 0.5, freeze list (hold flag, invalid telemetry, clamped, mean u >= 0.98, allocator saturation): match. Blend hold = landed or maybe_landed or modelled-force mode: matches.
- Saturation order (min-up 0.1 m/s^2, tilt on horizontal part, c above max shrinks horizontal first, below min scales whole vector): matches. omega_ff = (j.y_b, -j.x_b, 0)/c, 3 rad/s, jerk 50, hold 0.1 s, jerk own difference (j_ref = NaN in the module): match.
- Parameters and defaults in tab:outer_params (EN 0, LPF 10.0, DLY 1, TB 0.3, XY_P 1.2, XY_VP 2.4, W_MAX default 0; reference EN 1, W_MAX 2700), eight PINJ params, stock defaults 45/12 deg, 3.0 s, 1.5 m/s, MPC_THR_HOVER 0.137 and MPC_THR_MIN 0.05 (airframe 4040_gz_quad5in; stock yaml default of MIN is 0.12): match.
- Freshness numbers 20 ms (attitude, acceleration), 100 ms (ESC), 200 ms (allocator), 20 ms recovery: match (kStageMaxAge, kEscMaxAge, kAllocMaxAge, kAccRecoverTime).
- Items NOTES_E lists as unverified, now checked: 5.7 deg = asin(0.1), from rejection when thrust_dir_z >= -0.1 |n| (indi_accel_control.cpp L296-307): OK, say "about 5.7 deg". 0.3 m/s^2 blind descent: FailsafeSetpoint.hpp, OK. 200 ms fallback: McIndiPosControl.cpp L1064 `last_valid_setpoint.timestamp + 200_ms`, OK. 1.9 deg yaw-reset tilt spike: DECISIONS.md D-T10-RESET, OK (but see R9). 95.7 -> 6.8 Hz: DECISIONS.md D-AF-ALIAS, 95.73 - 88.89 = 6.84, OK (see R10). 267 Hz: DECISIONS.md D-AF-ALIAS (vehicle_acceleration 267 Hz): found, but simulation-specific (R11). 10 % edge step: see R8. Ground acceleration 100 m/s^2 (cpp L959), extrapolation cap 0.5 s and formulas: OK.

## Findings

### R1 MAJOR - delay line and blend "restart" contradicts the blend rule (L249, L280, L352, L363)
L249 says "The delay line and the blend restart from the commanded collective at every reset of the stage." Firmware: IndiAccelControl::reset() never touches the blend (comment "b is held, never reset"); it seeds the delay buffers and filters with the measured mean rotor state when the ESC data is valid, and with u_model - b only when it is not (indi_accel_control.cpp L152-175; McIndiPosControl.cpp L295-298 passes the measured mean u when fresh). The blend is zeroed (resetBlend) only at an arm/disarm edge (McIndiPosControl.cpp L425, L811). So L249 is wrong on both counts, and it contradicts L280 and L363 ("keeps the blend"). L280 and L363 are also not true for the arm and disarm resets that L352 lists as zeroing the blend. Correct: a stage reset (entry to position control, return from hold, estimator restart) keeps the blend and re-seeds the thrust path from the measured rotor state if valid, else from the commanded collective minus the blend; only arming and disarming clear the blend.

### R2 MAJOR - W_MAX = 0 described as a usable "measured path off" state (L231, L388, table L411)
The firmware refuses to arm the INDI stack when MC_INDI_W_MAX is 0 or the rotor geometry is missing (McIndiRateControl.cpp L290-294, "Arming denied: set MC_INDI_W_MAX"; params yaml of the rate module: "with 0, INDI refuses to arm"), and ch02 says the same (L72). The chapter says that with W_MAX = 0 "the law then uses the commanded collective", the guards list says "the stage runs on the modelled collective", and the table says "0 turns the measured path off". A reader will think the loop can fly without rotor telemetry. Correct: W_MAX must be set (default 0 blocks arming). The fallback to the modelled collective is for a motor going offline or stale ESC data in flight, not for W_MAX = 0. Rewrite the three places and the Default-column meaning.

### R3 MAJOR - freshness paragraph states requirements that are not what the code does (L241-243, tab:outer_stage L223)
"Attitude, acceleration and thrust data must be younger than 20 ms" : "thrust data" here is vehicle_thrust_setpoint (the commanded collective). Its age only chooses the value used to restart the stage (McIndiPosControl.cpp L116, L300); it is not a run condition and is not the measured thrust the chapter has just defined, so the sentence misleads. ESC age (100 ms) does not change the stage mode: stale ESC data makes only the measured thrust invalid (law runs on the model path, blend frozen), the force still comes from the accelerometer. Allocator age (200 ms) only decides whether the saturation flag is used. Table row "Measured: all data fresh" is therefore too strong. Correct: state per signal what a stale value does (attitude and acceleration change the mode; ESC invalidates the measured thrust; allocator status is ignored when older than 200 ms; the commanded-collective age only picks the restart value).

### R4 MAJOR - symbol T_c used for a vector and for a scalar (L123 vs L143, figure caption L91, diagram)
Eq outer_inc defines the bold vector T_c, then eq outer_cmd defines non-bold T_c = c/g_t, a normalised collective, with c = |T_c| in the same line. Two meanings of one symbol next to each other, distinguished only by boldface, and the diagram uses the non-bold one. Rename the normalised collective (for example $\theta_c$ or $\delta_c$, or "$T_{\mathrm{col}}$") and update the diagram label ("Modelled thrust from $T_c$").

### R5 MINOR - symbol c clashes with ch03 (L88, L143, L192 vs 03_inner_loop.tex L88-127)
ch03 uses c for the lead coefficient in (1+c); ch04 uses c for the collective magnitude. Use another letter for one of them (for example $T_\Sigma$ or $\lVert\vect T_c\rVert$ written out in eq outer_ff).

### R6 MINOR - u_meas / dt notation against ch03 (L258)
ch03 uses $u_{\mathrm{meas}}$ for the measured torque vector (eq inner_meas); ch04 uses $u_{\mathrm{meas},f}$ for the scalar mean thrust state. Say once that the scalar is the mean of the four rotor states, or rename ($\bar u$). The stage period is written $\dd t$ in eq outer_blend and in the extrapolation formula (L114) with different meanings (cycle period vs. setpoint age); ch03 uses $\ts$. Use $\ts$ for the period and another name for the extrapolation time.

### R7 MINOR - eq vsp/aref are written with scalar gains (L101-102, L109)
K_p and K_v are only the horizontal gains; the vertical gains are stock and are different parameters. Write the equations per axis, or say "K_p, K_v are diagonal; horizontal entries are MC_INDI_XY_P and MC_INDI_XY_VP, the vertical entry is the stock gain". Also say once what the "stock derivative term" is for the reader who does not know it, or drop L105.

### R8 MINOR - 10 % is the gate limit, not the measured step (L343, ground diagram caption)
Source (GATES.md, "G5 verdict at freeze-10") says every take-off stayed within the limit "edge step <= 10 % of hover"; the measured step is 4.0-4.7 % of hover (take-off after re-arm; report/03_validation.md G5.9d). "It was at most 10 % ... on every measured take-off" presents the limit as a measurement. Say "4 to 5 % of the hover thrust on the measured take-offs, always below a 10 % limit", in the text and in diagrams/ground_logic.tex ("measured step at most 10 % of hover thrust").

### R9 MINOR - history of a removed design (L361)
"Re-seeding them from a single raw sample caused a tilt spike of 1.9 deg at a yaw reset" tells a development story (a defect found and removed). State the design reason: a single raw accelerometer sample carries vibration of about 0.25 m/s^2 against 0.04 m/s^2 after the filter, so re-seeding from it would step the acceleration estimate (about 2 deg of tilt command at the 1.9 deg figure). If the number is kept, mark it as simulation-measured.

### R10 MINOR - aliasing example is not reproducible from the text (L161)
The reader is not told the stage rate. Add "the stage runs at about 89 Hz in the reference simulation, so a 95.7 Hz line would fold to 6.8 Hz" and that the line is a simulation vibration. Also "stage rate" is used at L162 with no number.

### R11 MINOR - 267 Hz is a simulation setting (L58)
Source: DECISIONS.md D-AF-ALIAS records the vehicle_acceleration rate of the reference simulation. On other flight controllers the topic rate depends on the IMU and sensors-module configuration. Write "for example about 267 Hz in the reference simulation".

### R12 MINOR - guard "stage interval between 2 ms and 0.2 s" is wrong at the lower end (L382, consistent with L221)
IndiStageMode.hpp: an interval below 2 ms is clamped to 2 ms (kStageDtMin), only above 0.2 s does the stage hold. Write "an interval above 0.2 s holds; shorter intervals are clamped to 2 ms".

### R13 MINOR - ground handling details (L330, L337, L349)
(a) The 100 m/s^2 empty setpoint is also applied in flight state while ground contact is reported (flying_but_ground_contact, cpp L953-960), not only before take-off. (b) L337 "The feed-forward acceleration is cleared during the ramp": only the vertical component is cleared, and only when a vertical velocity setpoint is finite (cpp L951). (c) L349 the altitude-derivative blending is not specific to landing: it applies whenever altitude is not controlled and a nonzero vertical speed is commanded (cpp L1041-1047), for example a climb-rate command in Altitude mode. Move it to the section on the cascade or say "while descending or climbing at a commanded vertical speed".

### R14 MINOR - hover thrust choice (L137)
Code: the estimate is used only in flight (take-off state flight) while valid; before that, MPC_THR_HOVER. The code also floors h_t at 0.05. Say "in flight, while the estimate is valid".

### R15 MINOR - constants list incomplete and a statement of fact missing (L425, L192)
The rate feed-forward is zero when c < 1 m/s^2 (kMinThrustForFf); add to the library constants or to L195. Mention that the measured thrust is the mean of exactly four rotors (quad only, L229).

### R16 MINOR - negative-history phrasing (L36, L321)
"There is no fallback to the stock thrust path" and "There is no stock thrust path and no hand-over of the hover thrust" describe what was removed. Keep one positive statement ("one law from arming to disarming; the stock thrust is never published") and drop the "no hand-over" clause.

### R17 MINOR - blend explanation (L265-269)
"A thrust gap then appears as a rotor-speed deficit that the blend absorbs" is unclear. Suggest the argument that makes the integral action visible: with a gap the measured rotor state is a fraction rho of the commanded state, so the loop of eq outer_inc settles at a_f = a_ref - (1 - rho) T_c; the blend restores u_f to the model at low frequency and removes that error. The statement at L139 (a wrong g_t gives no offset) holds for the same reason and is worth one sentence, because it is the key difference between the two cases.

## Development-trail scan
Grep of the tex for D-, S-numbers, A-, Q-, gate ids, file names, ".cpp/.md/.yaml": no hits. Remaining trail-like text: R9, R16, and the "measured take-off" claim R8. Topic names and parameter names are interface names, acceptable.
