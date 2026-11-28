# Re-review of the ch01/02/05 fixes and chapter-level review of ch01, 02, 03, 05

Reviewer: fresh agent, read-only (no .tex edited, nothing committed). Date 2026-11-28.
Sources used: GATES.md (G3 verdict S199, G5, G7 verdict and S259 note), GATE_STATUS.tsv, results/freeze10_s193/G2_SCORES.md,
bench/margins_models.py, bench/params/quad5in_indi_defaults.params, src/modules/mc_indi_rate_control (yaml, constants),
src/lib/indi_rate_control/indi_rate_control.hpp, report/01_inner_loop_design.md.
Build: copy of the pdf folder built in /tmp/indi_pdf_rr with latexmk -lualatex (ch06 to ch09 were still 3-line stubs in the
copy; ch06 has since grown to 520 lines in the repo, so ch06 was not part of this build). Result: 0 undefined references, 0 undefined
citations, 0 overfull or underfull boxes. The ch02 airframe table renders inside the text width (page image checked).
Not verifiable by me: whether the final ch06 to ch09 will satisfy the forward references made by ch01 to ch05 (listed in section 3).

## 1. Re-review of the fixes (task A)

Status words: CLOSED, OPEN, NEW (problem introduced or exposed by the fix).

### Chapters 1 and 2 (ch01_02_section_review.md)

| Id | Status | Note |
|----|--------|------|
| R1 | CLOSED | ch01:105-108. Checked at source (GATES.md l.725-735): runs 245 and 264 lost control, 79 of 297 item-2 fails, PID without LOC on both, campaign not repeated. See NEW N1 for "final frozen firmware". |
| R2 | CLOSED | ch01:100-102. 49.1 deg in 24 cells, rate 46.9 deg roll only, thin: all match G2_SCORES.md. Attitude spot cell (48.0 deg) not mentioned, acceptable. |
| R3 | CLOSED | ch01 C5 row (l.88) and box (l.103). Not-tested list matches GATES.md G5 verdict. |
| R4 | CLOSED | ch01:71-72 and 46. Text now relies on ch06 to list the amendments; ch06 (new, in repo) must carry them (not verified). Abstract still says "fixed before the tests" with no caveat (M3). |
| R5 | CLOSED | ch02:8,14-15,21,25,75-76 and ch04:238 (`\bar u`): u = normalised torque, u_i = rotor state, u_rot, B all consistent with ch03:38-39,162-168. |
| R6 | CLOSED with MINOR residue | Table 2.2 has B, u_rot, u_trim, b, t_b, l, c, Delta_max, H, omega_ref, u_mod,f, u_meas,f, Omega_max. Still undefined but used in ch03: omega_ref_dot_f (l.90,100), u_act, u_alloc, u_meas (l.153,166), and ubar of ch04 (see m6). |
| R7 | CLOSED with MINOR residue | No `\mathbf` left in ch02. Rule at ch02:149-151 holds in ch03 (plain nu, omega, u per axis; bold only for u_rot, u_trim). Residue: macro `\aref` (preamble.tex:154) is upright bold `\mathbf`, while `\vect` is bold italic, so a_ref prints differently from a_f in ch02:103-104 and the table. |
| R8 | CLOSED | Rows a, aref, T/tau match ch04:80-86. |
| R9 | CLOSED | ch02:92-93. |
| R10 | CLOSED | ch02:76-77, matches IndiEscThrust (mean of four). |
| R11 | CLOSED | ch01:60-61. The abstract no longer contains "no assumption specific to one vehicle" (grep): that follow-up is closed. |
| R12 | CLOSED | ch01:28-29, ch02:47. See NEW N2 (ch03 contradicts it). |
| R13 | CLOSED | ch02:25,31,33,58-59. |
| R14 | CLOSED, one NEW | k_T unit (4 x 1.5e-6 x 999^2 = 5.99 N = m g), arm 0.0795 x sqrt2 = 0.1124, exponents, k_Q/k_T, poles all right. NEW N3: the ACT_TC remark (ch02:143). |
| R15 | CLOSED | ch02:141. (205-165)/205 = 19.5 %, "about 20 %" correct (report 01 l.325). |
| R16 | CLOSED, C1 left OPEN by choice | C2 simulated flight and delay margin, C7 v5x/v6x (+64.8 kB, v6x overflow 23.5 kB, GATES.md l.951-953), C8 unverified claims, "PASSED means with limits" all present. C1 qualifier (G1.5 deferred per injector) deliberately not added: MINOR, accepted. NEW N4 on the C2 cell. |
| R17 | CLOSED for wording, OPEN for px4guide | ch01:15 neutral wording. Bibliography entry px4guide (main.tex:95) is still never cited (grep over all chapters). Build shows no warning because thebibliography does not complain. |
| R18 | CLOSED | ch01:57-58. |
| R19 | CLOSED | ch01:56. |
| R20 | CLOSED | ch01:86. |
| "4 of 8" | NOT APPLICABLE, confirmed | No such text in ch02. The 7 of 8 is in ch05:181 and is right (G2_SCORES.md: pt0 D 4 n/a, pt1 D 3 n/a, only the 800 Hz seed-2 cell has 22.4 dB). |

### Chapter 5 (ch05_section_review.md)

| Id | Status | Note |
|----|--------|------|
| R1 | CLOSED | ch05:244 and 319 say 267 Hz not flown on the final configuration, consistent with ch05:92 and GATES.md. FIGURES.md:13 still carries "The 250 Hz controller rate was not measured" (outside the .tex; follow-up). |
| R2 | CLOSED | L_tq, no M3a left (grep 0). |
| R3 | CLOSED | A_att = p z^-1 Ts/(z-1) equals margins_models.py:198 (`att_p*zi**lat*T*zi/(1-zi)`, zi = z^-1, so zi/(1-zi) = 1/(z-1)). |
| R4 | CLOSED | ch05:141-143, assumed stock defaults (source: model_vs_measured.md, Ki 0.4, Kd 0.2). |
| R5 | CLOSED | ch05:145-146. |
| R6 | CLOSED | Plateau GM defined at l.83-84; l.181-183 and table note match G2_SCORES.md (16.3 dB key 2, about 28 dB key 2 in 4 cells, 12.88 minimum). |
| R7 | CLOSED | ch05:312: 9 of 9, overshoot <= 5 %, settle <= 450 ms (yaw 1350), worst 0.65 % and 347.5 ms: all match G2-STEP table. |
| R8 | CLOSED | No pt0/pt1/texttt left. Table an_outer recomputed from G2_SCORES.md for all six rows incl. the re-fly: every range correct (e.g. Accel E PM 52.9 to 56.9, DM 461 to 485). |
| R9 | CLOSED | ch05:70,310. |
| R10 | CLOSED | 22.5 ms gap, 11.25 ms excess, limit 10 ms (G2_SCORES.md). |
| R11 | CLOSED | ch05:99-100, 320. |
| R12 | CLOSED | ch05:91. |
| R13 | CLOSED | ch05:95-96. 1/(8 f_c) is correct for 45 deg. See NEW N5 (f_c clash). |
| R14 | CLOSED | ch05:54. |
| R15 | CLOSED | ch05:260. |
| R16 | CLOSED | Table an_att deltas recomputed (measured minus model: -0.3/+1.6, +0.2/+3.4, +0.2/+4.6): correct; "all above 17 dB" correct (min 17.2). |
| R17 | CLOSED | ch05:301-303. |
| R18 | CLOSED | ch05:246-252 (-133 deg, 46.9 deg, 15.7 dB, 18 bins, no overlay). |
| R19 | CLOSED | ch05:237-243. |
| R20 | CLOSED for the pointer, NEW N6 | ch05:307 "gate G2 (tab:criteria)": the table labels the criterion C2, not G2. |
| R21 | CLOSED | ch05:113. |

NEW problems introduced or exposed by the fixes: N1 to N6 (details in section 2).

## 2. Chapter-level findings (task B)

Severity: BLOCKER 0. MAJOR 3. MINOR 14. Totals at the end.

### Cross-chapter

**M1 (MAJOR) Chapter 3 claims "no integrator / no windup state" without the blend, contradicting ch01, ch02 and ch04 (this is N2).**
ch03:113-117 (key box "No integrator, no disturbance estimator", "no windup state") and ch03:250 ("The law has no integrator, so there is no windup state"). The same chapter introduces the blend state b (l.208-246, bounded |b| <= 2, frozen while maybe landed, with a 1 s time constant) that restores a steady correction; ch01:28-29 and ch02:47 now carry the qualifier "apart from the slow blend", and ch04:306 calls the blend's freeze rules "an anti-windup". Source: indi_rate_control.hpp header (blend "restores the integral action"), kMaxBlend = 2. Fix: add to both ch03 places "apart from the slow blend of Section 3.5, which is bounded and frozen when ...".

**M2 (MAJOR) "Final configuration" / "final frozen firmware" is never defined, and ch01 contradicts itself.**
ch01:105 ("campaign on the final frozen firmware") against ch01:108 ("not repeated on a later firmware"); ch05 uses "final configuration" 9 times (l.7,142,158,202,210,213,244,260,307,319) and "pre-final binaries" (l.256). Nothing in ch01 to ch05 says what is frozen, that the margin cells (firmware 7fe6206fcc), the robustness campaign (binary d220e193) and the code reviewed for G7 are different states, nor that commits followed the freeze (arming check, review fixes: GATES.md G7 note S259, flash +66.1 kB at the new head). Since ch03 describes the arming refusal (W_MAX 0), a reader will assume ch05's margins were measured with it. ch06:"A verdict holds for one firmware ... G2, G4 and G5 were flown on the final configuration" says it later, but ch01 to ch05 come first. Fix: one sentence in ch01 sec:scope or ch05 introduction: "The final configuration is the firmware at the last freeze of the control code; later commits changed arming checks, naming and comments only (Chapter 6)." Use "frozen firmware" or "final configuration", not both.

**M3 (MAJOR) Abstract (main.tex:34-36) still overstates: "Measured in flight", "fixed before the tests", "work in every flight mode".**
All evidence is simulation (the title page says so). ch01 and ch05 were corrected (simulated flight, tested modes, later amendments of test definitions) but the abstract was not. Source: GATES.md G5 verdict (modes not tested), GATES.md S187/S197/S208/S214/S243 amendments. Fix: "Measured in simulated flight", "Eight acceptance criteria were fixed before the tests (later test-definition fixes are listed in Chapter 6)", "are designed to work in every flight mode (the tested modes are in Chapter 6)". Same for ch05:244 and ch05:7,202 phrasing "in flight" (see m9). Known follow-up: still OPEN for these three phrases; the phrase "no assumption specific to one vehicle" is gone (closed).

### Chapter 1 (Introduction)

Flow problem -> idea -> goals -> scope -> criteria and results -> reading guide is clear. No development trail (grep of ch01 to ch05 for D-, Sxxx, Qxx, A-xx, F-x, file extensions, line citations, run numbers: 0 hits). The result box is now accurate against GATES.md.

- **m1 (MINOR) N4: C2 row (ch01:85) says delay margin "at least two control periods plus telemetry latency"; ch05:99-100,320 says the latency was not recorded and the margin was only compared with the control periods.** Add "(telemetry latency not measured, Chapter 5)".
- **m2 (MINOR) ch01 uses C1 to C8 and "criterion"; ch05:307 and ch06 use "gate G2" (ch06 defines "Gate Gn is criterion Cn" at its start, after ch05).** Add the same sentence to ch01 sec:criteria (before the table) so ch05 can use either word. (This is N6.)
- **m3 (MINOR) ch01:100 "In simulation the controllers meet the stability limits" is followed by thin-margin text, fine, but the box never mentions the 48.0 deg attitude cell or that yaw/pitch rate loops were not measured for the attitude loop.** Optional.
- **m4 (MINOR) ch01:105 "scored flights showed a sustained oscillation on at least one of the two scoring methods": the 79 include 25 landing-window and 9 borderline key-1-only runs (GATES.md l.733-736) and runs PID also fails (008, 262).** The claim is correct as a count; add "some of which PID shares" only if space permits. The next sentence says PID did not lose control, which is true; do not let it read as "PID passes the oscillation test".

### Chapter 2 (Background)

Order principle -> rotor speed -> PX4 chain -> airframe -> notation is right and the derivation (eq. 1 to 5) is algebraically consistent with ch03 eq. (inner_inc) at c = 0.

- **m5 (MINOR) N3: ch02:143 "the mapping between the two is not verified" contradicts ch03:387-388 ("the value the identification step returns for this airframe") and report 01 l.327-328 (identification grid returns tau_sym within 0.4 % of the true value in simulation).** The parameter-file comment that says UNVERIFIED is stale. Fix ch02 to "agrees with the identification result in simulation; not verified on hardware", and make ch03:388 say "in simulation".
- **m6 (MINOR) Notation table (ch02:153-189) vs ch03/ch04/ch05.** Missing: omega_ref_dot_f (ch03:90), u_act/u_alloc/u_meas, ubar (ch04:238), p (attitude gain, ch05:124), K_p/K_v/K_i/K_d (ch05, defined locally, fine). Clashes: c = lead gain (ch02:179, ch03) against c = controller output in ch05:16-18 (`u = c + d`); omega = body rate (ch02:161) against omega = angular frequency in ch05:24 (`L(j omega)`); **f_c = control rate (ch02:135,186) against f_c = gain crossover frequency (ch05:77,81,96)**; T = specific thrust vector (ch02:184) against T_p, T_cl in ch05 (subscripts make it safe). The f_c clash is the one a reader will notice in eq. (an_dm): DM = PM/(360 f_c) next to "controller rate f_c = 800 Hz". Fix: use f_x for the crossover in ch05 (or f_s for the control rate in ch02 and ch05:91-92), and c_out or u_c for the controller output in an_inj.
- **m7 (MINOR) Table 2.1 (ch02:116-138):** fits (no overfull, verified in the log and page image). The follow-up "ch02 airframe table overfull" is CLOSED.

### Chapter 3 (Inner loop)

Flow (problem, three questions, law, actuator state, filters, blend, saturation, ground, guards, parameters, margins) is clear and the three questions of sec:inner_problem are answered in the order promised. Parameter defaults and references checked against yaml and quad5in_indi_defaults.params: all 21 rows match (EN 0, W_MAX 0/2700, G1 1757/1640/205, G2 27, K 20, ACT_TC 0.05 default and 0.033 reference, ERPM_TO 0.02, ACT_BLD 1.0, LND_SLEW 5, ERPM_FRZ 0.5, SP_TO 0.5); nine INJ_* parameters correct; library constants (20 valid cycles, 3 hold cycles, blend bound 2, lead bound 2, 0.03 s and 1000 rad/s^2 for the setpoint derivative, 4 delay samples, dt range 0.000125 to 0.02, 0.45 yaw cut ratio, 10 % redesign, 1.5 rpm ratio, 50 ms feed-forward age) match indi_rate_control.hpp and the module headers. ID_OK 0 in the reference column is what the margin cells were flown with (run.json: ID_OK 0), so K is effectively 10 1/s and the 1.72 Hz crossover is consistent. W_MAX 0 blocks arming: ch03:175-177,313,351 correct (yaml "with 0, INDI refuses to arm"); the known follow-up is CLOSED in ch03 and ch04:240. ch05 does not mention W_MAX at all: nothing to fix there.

- **M1 above (no integrator).**
- **m8 (MINOR) ch03:6 says the chapter "ends with the parameters a user can set", but the last section is the rate-loop margins (l.393-402).** Change to "and ends with the measured margins of the finished loop".
- **m9 (MINOR) "in flight" for simulation:** ch03:399 ("not measured in flight"), ch05:244 caption ("measured in flight"), ch05:7 and 202 contexts. Use "in simulated flight" at least in the caption and ch03:399.
- **m10 (MINOR) ch03:136-137 and table (G1_Y 205, G2_Y 27) give no hint that the yaw 205 is disputed (ch02:141 says a fit gave 163 to 166).** One clause in ch03:337 ("the yaw value is the less certain, see Section 2.4") closes it.
- **m11 (MINOR) Cross-check ch03 against ch05 numbers:** ch03:397-398 and fig. caption (1.72 Hz, 46.9 deg, 18.3 Hz, 15.7 dB, 75.5 ms) equal ch05:204,246-249 and margins.txt. Consistent. ch03:243 gives crossover 1.7 Hz while report 01 l.141 says "about 4 Hz" (older measurement); ch03 is right for the final loop.

### Chapter 5 (Analysis)

Flow measurement method -> criteria -> models -> results -> model agreement -> verdict is clear, the evidence limits are honest, every table and figure is referenced and explained (tab:an_break, an_outer, an_spot, an_att, fig:g2_margins, fig:bode_rate). Numbers recomputed against G2_SCORES.md: no error found.

- **m12 (MINOR) L_rate is never defined (ch05:122,129).** Source (margins_models.py:214,222): L_rate is the rate loop with the attitude path open; the loop measured at the torque setpoint (table an_break, fig. 3.2) is L_tq, which already contains the attitude path. A reader will take the "rate loop" PM 46.9 of the spot cell and the "rate model" PM 23.6/22.3 of ch05:260 as the same object. Add: "L_rate is the rate loop with the attitude loop open; the break at the torque setpoint measures L_tq".
- **m13 (MINOR) N5/m6: f_c clash in ch05:77-96** (see m6) and "G2" in ch05:307 (m2).
- **m14 (MINOR) ch05:134-147 versus ch04:** ch05 now says K_p, K_v here are the stock gains and differ from ch04. Consistent. The reader still cannot see why the final configuration's own outer loop (ch04 gains MC_INDI_XY_P 1.2, XY_VP 2.4) is checked with a different model; one sentence ("no model of the final loop was built") already exists at l.147 and is enough. Nothing to do.
- **m15 (MINOR) ch05:256-257 "pre-final binaries" and ch05:7 "on the final configuration"** (M2) need the definition of final.
- **m16 (MINOR) Gap between ch05:7 ("It then compares the measurements with linear models") and the cross-check being pre-final only (l.256-257, table an_att, "Pre-final binaries").** The introduction should say that the model comparison uses older measurements.

## 3. Known follow-ups, status

| Follow-up | Status |
|-----------|--------|
| ch05 notation consistent with ch02 table (ubar, plain nu, omega, u) | Partly open: no bold per-axis symbols, u not used for rotor mean in ch04; but c, omega, f_c are used with a second meaning in ch05 (m6). |
| Text that W_MAX 0 blocks arming | CLOSED: ch03:175-177,313,351; ch04:240,434; ch02:79. Source yaml. ch05 does not say the opposite. |
| "4 to 5 % edge step" described as the re-arm take-off | CLOSED: ch04:365 and diagrams/ground_logic.tex:16 (GATES.md l.715: re-arm take-off 4.0 to 4.7 %, limit 10 %). |
| Abstract "no vehicle-specific assumption" | CLOSED (phrase gone). |
| Abstract "measured in flight" | OPEN (M3). |
| px4guide uncited | OPEN (main.tex:95; cite it in ch02 sec:px4_chain or delete). |
| ch02 airframe table overfull | CLOSED (log clean, page image fine). |
| FIGURES.md g2_margins caption still says 250 Hz | OPEN (FIGURES.md:13, not .tex). |
| Forward references to ch06/ch07/ch08 | ch01:46,58,72,99,119-120 and ch03:261,318 rely on ch06 listing the test-definition amendments and the flown modes, and on ch07 listing the limits. ch06 was not complete in my build; not verified. |

## 4. Totals

BLOCKER 0. MAJOR 3 (M1 no-integrator contradiction in ch03, M2 undefined "final configuration"/self-contradiction in ch01, M3 abstract overstatement). MINOR 16 (m1 to m16; m7, m11 and m14 are "no action" confirmations, so 13 actionable).
Re-review: 40 of 41 fix rows CLOSED (R16 C1 qualifier and R17 px4guide left open by choice, one NOT APPLICABLE); 6 new problems (N1 to N6) are folded into M2, M1, m5, m1, m6, m2.
