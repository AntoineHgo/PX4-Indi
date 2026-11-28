# Fixes: chapters 1-2 review (R1-R20), chapter 4 re-review (C1-C8, R5, R8)

Sources checked: GATE_STATUS.tsv, GATES.md (G2 verdict at freeze-10, G3 verdict at freeze-10, Owner amendment S243, G5 verdict at freeze-10, G7/G8 verdicts), firmware yaml/rate module for W_MAX. No verdict or value changed.

| Id | Result | What / source |
|----|--------|---------------|
| R1 | FIXED | ch01 result box rewritten: 6 of 8 named, campaign identified (300 flights on the final frozen firmware, 2 LOC, 79 of 297 oscillation), PID without LOC on same draws, two INDI-specific limits remain, campaign not repeated, C3 final NOT PASSED (GATES.md G3 verdict at freeze-10, Owner amendment S243). |
| R2 | FIXED | Margins sentence: outer PM >= 49.1 deg in 24 cells, rate 46.9 deg in one roll cell, thin (GATES.md G2 verdict at freeze-10). |
| R3 | FIXED | C5 row lists the not-tested items and one-method modes; box says "tested modes" (GATES.md G5 verdict at freeze-10). |
| R4 | FIXED | ch01 states criteria fixed before tests with thresholds, later definition fixes by the owner are logged and listed in ch06 (GATES.md owner amendments). Ch06 must carry that list (see follow-up). |
| R5 | FIXED | ch02: u is normalised torque (G_1 diagonal), rotor states u_i, vector u_rot, u = B(u_rot - u_trim); ch04 mean rotor state renamed ubar. |
| R6 | FIXED | Notation table: added B, b, t_b, l, c, Delta_max, omega_ref, H, u_mod,f, u_meas,f, u_rot, u_trim, Omega_max; changed u, nu, G_1, G_2, tau_a, K, a, T/tau rows. |
| R7 | FIXED | \mathbf -> \vect in ch02; bold/plain rule stated; ch03 figure caption and text use plain nu, omega_f; ch03 u_rot/u_trim use \vect. |
| R8 | FIXED | Rows a, aref, T/tau per ch04 definitions (T specific thrust vector, tau magnitude). |
| R9 | FIXED | Gyro to rate loop, accelerometer to acceleration loop. |
| R10 | FIXED | Torque via B, thrust from the mean of four rotor states (quadrotor). |
| R11 | FIXED | ch01 scope: not tied to one vehicle except four-rotor measured thrust; other layouts untested. Abstract (main.tex) not in scope, listed below. |
| R12 | FIXED | ch01 benefits and ch02 key box mention the slow blend. |
| R13 | FIXED | Delta u-dot defined, instant-torque assumption stated, "basic law" with lead and G_2 pointer, lag applies to torque. |
| R14 | FIXED | Table 2.1: k_T unit, arm length 0.112 m, inertia exponents, k_Q/k_T and poles explained; ACT_TC mapping note. |
| R15 | FIXED | Yaw 205 caveat (fit 163-166, about 20 % less, unresolved). |
| R16 | FIXED | C2 simulated flight and delay margin, C7 v5x/v6x, C8 unverified claims, "PASSED means with limits of ch07" in box. C1 deferred-evidence qualifier not added (kept short; see ch06). |
| R17 | FIXED | "applied to" wording. px4guide bibliography entry left uncited (main.tex bibliography outside scope; follow-up). |
| R18 | FIXED | "By design" and pointer to ch06 for flown modes. |
| R19 | FIXED | Modules not started, stock unchanged, checked by code diff. |
| R20 | FIXED | C3 row lists all pass items. |
| ch02 "4 of 8" | NOT APPLICABLE | No such text in ch02 (grep of ch01-04 finds nothing); nothing changed. |
| C1 | FIXED | ch03 text and table: W_MAX must be set, default 0 refuses arming (yaml: "with 0, INDI refuses to arm"; McIndiRateControl.cpp arming check). |
| C2 | FIXED | Text after Fig. 4.1 explains H blocks, force-source switch, thrust-state block; fig:outer_ground caption sentence on the edge note. Colour convention not re-checked in the diagram source. |
| C3 | FIXED | Fourth question added; roadmap lists state, modes, ground, resets, guards. |
| C4 | FIXED | (b) u_f scalar note, (c) model-path note, mean state renamed ubar. (a) tau vs tau_a left (subscript distinguishes). (d) no change needed. |
| C5 | FIXED | Force filter per sample, stage per position-estimate update (about 89 Hz). Source: reviewer's firmware reading. |
| C6 | FIXED | Text and table state the condition (rate module refuses to arm; outer loop has no measured thrust). |
| C7 | FIXED | \cref added for outer_fb, outer_gt, outer_cmd, outer_blend, outer_ff. |
| C8 | FIXED | "In the reference simulation" added to the vibration figures. |
| R5 (diagram) | FIXED | diagrams/outer_loop.tex jerk block now divides by tau. |
| R8 (edge step) | FIXED | ch04 and ground_logic.tex line 16 say the 4-5 % step is from the re-arm take-off, limit 10 % for every take-off (GATES.md G5 verdict: 4.0-4.7 % in G5.9d; F-7 <= 10 %). |

Counts: 33 FIXED rows (R1-R20, C1-C8, R5, R8 = 30 ids all fixed, C4 partly), 0 REJECTED, 1 NOT APPLICABLE ("4 of 8").

## ch05 follow-up
- Rename any use of u for the mean rotor state to ubar (ch04 now uses ubar).
- Per-axis equations in ch05 should use plain nu, omega, u per the ch02 rule; check any bold symbol used for one axis.
- Check that ch05 does not say MC_INDI_W_MAX 0 turns the measured path off (it blocks arming).
- Check the 4-5 % edge step is attributed to the re-arm take-off.
- ch06 must list the owner test-definition amendments (R4); abstract in main.tex still says "makes no assumption specific to one vehicle" and "measured in flight" (R11, R16); px4guide entry uncited (R17).
