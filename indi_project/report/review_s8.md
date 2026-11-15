# Independent review of the stage-8 (INDI POS, set O) report sections

Date 2026-11-15. Scope: 05 sec. 5.9, 08 sec. 8.11, 09 sec. 9.6, 10 sec. 10.6, 11 sec. A.8, 06 GNSS-delay paragraph.
Ground truth: `results/s8n_oset.md`, `results/s8k_gnss_delay.md`, DECISIONS.md D-s8-*, `bench/scenarios.md` sec. 10,
spot checks in `bench/disturbance.py`, `bench/scenarios.py`, `bench/s8p_hover_effort.sh`, `bench/s8n_oset.sh`,
`src/lib/indi_accel_control/indi_accel_control.cpp`. Severity: major = wrong number / overclaim / wrong math /
statement contradicted by recorded data; minor = wording, missing caveat, wrong cross-reference.

## Check 1: numbers in 8.11 / 9.6 / 10.6 / A.8 against s8n_oset.md

Verified, all match (rounded to 3 significant figures): the seven rows of the 8.11 table (means, seeds, median
improvement, p 0.00195 -> 0.002 and 0.00977 -> 0.010, effort ratios 1.10/1.03/1.10/1.41/1.03/0.91/1.10), 0/70
failures, 6/7, hover 2.02x with 0.088 vs 0.044 and ranges 0.021-0.075 / 0.067-0.118, O4 secondary numbers (0.193 ->
0.19 m, 33.5 %, 0.029 -> 0.03 m, 22.9 %), 9.6 and 10.6 summaries (28-72 %, 0.9-1.1x, 1.4x, 72 %, 51 %, 4 %, 2.02x).
The hover script flies the same configuration as set O (`s8p_hover_effort.sh` line 9: `--gnss-delay 0`, v2 flags).

### R1 (major) 10_conclusion.md:75, payload magnitude wrong
- What: "a 15 % payload (72 %)". O4 uses the T7 `payload_add` profile, which is +25 % of the mass.
- Evidence: `bench/scenarios.md:59` "T7 `payload_add` ... +25 % mass added at the CoM"; `bench/disturbance.py:37`
  `PAYLOAD_FRAC = 0.25` (0.15 is `SHIFT_FRAC`, the H3/O5 CoM-shift mass); `bench/scenarios.md:218` "O4 ... payload_add
  (T7 profile)".
- Replacement: "a 25 % payload (72 %)".

### R2 (minor) 08_results.md:489 and 09_discussion.md:97, "by more than 1 %"
- What: "doubling the motor time constants (O7) changed neither controller by more than 1 % against O1". INDI POS
  O1 0.3158 -> O7 0.3196 is +1.2 % (table values 0.316 -> 0.320, +1.3 %). `s8n_oset.md` itself says "within 1 %",
  so the source rounds too.
- Evidence: `s8n_oset.md` rows O1 (0.4557 / 0.3158) and O7 (0.4563 / 0.3196).
- Replacement (both places): "changed neither controller by more than about 1 % against O1 (`pid_tuned` +0.1 %,
  INDI POS +1.2 %)".

### R3 (minor) 08_results.md:482, unsupported mechanism for the outer-loop hover effort
- What: "(plausibly accelerometer vibration reaching the thrust vector, not isolated)". Neither `s8n_oset.md` nor
  any D-s8 decision names vibration; D-s8-freeze records that halving the specific-force filter cut-off (5 Hz) did
  not lower hover effort ("the cause is not the filter bandwidth"), which argues against a vibration-bandwidth
  explanation.
- Evidence: D-s8-freeze table, hover effort indi_pos_v3 0.087/0.081 vs indi_pos_v3_lpf5 0.108/0.088.
- Replacement: "(cause not isolated; halving the specific-force filter cut-off to 5 Hz did not lower it,
  D-s8-freeze)".

## Check 2: formal verdict wording

8.11 states criterion 4 "not met, 2.02x" and the outcome "INDI POS does not outperform PID" in bold; 10.6 repeats
"does not outperform PID". Both follow sec. 10 / sec. 6 exactly. No softening of the verdict found.

### R4 (minor) 10_conclusion.md:78, "with the tracking criteria met by a wide margin"
- What: criterion 2 required >= 5 of 7 entries and got 6 of 7, one entry of margin. 8.11 says "with margin",
  `s8n_oset.md` says "met clearly". "Wide" is the strongest of the three and is not backed by a defined margin.
- Replacement: "with the tracking criteria met clearly (6 of 7 entries, 10/10 seeds on each, no failure, nothing
  worse)".

### R5 (minor) 08_results.md:478-479, mean vs median for criterion 4
- What: the criterion is judged on the mean over 10 seeds (D-s8-hover10, `s2_verdict.py --hover-runs`), while
  D-hover-spread (session 50) prescribed "pooled medians with per-flight ranges over >= 10 flights ... never as a
  ratio of two small batch means". The report does not say that D-s8-hover10 chose the mean over the earlier median
  rule, nor give the median ratio.
- Evidence: D-hover-spread bullet 2; D-s8-hover10 "judge criterion 4 on the mean over seeds 1-10"; `s8n_oset.md`
  "2.02x ... (mean motor-rate RMS 0.088 vs 0.044 ...)".
- Replacement: after "judged on 10 seeds per D-s8-hover10)" add: "as the ratio of means, which D-s8-hover10 chose
  over the pooled-median rule of D-hover-spread; the per-seed ranges, `pid_tuned` 0.021-0.075 and INDI POS
  0.067-0.118, barely overlap, so the median ratio gives the same outcome". NOT VERIFIED: the per-seed values are
  not in `s8n_oset.md`, so I could not compute the median ratio; confirm it before adding the last clause.

## Check 3: control law in 5.9.2

Verified: $f_b=R^\top(a-g)$ with $g=(0,0,+9.81)$ NED gives $a_f=Rf_{b,f}+g$ (hover: $f_b=(0,0,-9.81)$, correct);
$\dot z_b=R(\omega\times e_3)=q\,x_b-p\,y_b$ in FRD, so $j\cdot x_b=-cq$, $j\cdot y_b=cp$ and
$\omega_{ff}=(j\cdot y_b/c,\,-j\cdot x_b/c,\,0)$ matches the code (`indi_accel_control.cpp:336-337`); the nose-up
sanity check is right; $t_c=t_f+(a_c-a_f)$ follows from $a=g+t+\text{(unmodelled)}$; thrust $=c/(G_Tk_{cmd})$ is
consistent with $u=k_{cmd}\cdot$thrust and $|t|=G_T u$; gain units (1/s) correct.

### R6 (minor) 05_design_implementation.md, "Incremental law" paragraph (approx. line 358)
- What: "As in the inner loop, the reference acceleration is a measurement and so contains drag, gusts and payload
  without a model of them." The reference acceleration $a_{ref}$ comes from `trajectory_setpoint`; the quantity that
  is a measurement and contains the disturbances is $a_f$ (and $t_f$). The sentence states the law wrongly.
- Replacement: "As in the inner loop, the measured acceleration $a_f$ already contains drag, gusts and payload, so
  the increment $a_c-a_f$ corrects them without a model of them."

### R7 (minor) 05_design_implementation.md, "Saturation and thrust vector" paragraph (approx. line 364)
- What: "the angle between $-t_c$ and $-e_3$ is limited to `MPC_TILTMAX_AIR`". With $t_{c,z}\le-\epsilon$, $t_c$
  points up and $-e_3$ points up (NED), so the tilt is the angle between $t_c$ and $-e_3$; between $-t_c$ and $-e_3$
  it is $180^\circ$ minus the tilt. The code comment (`indi_accel_control.cpp:287`) carries the same slip, but the
  implementation `h_max = -t_c(2) * tanf(_tilt_max)` is the correct geometry, so this is prose only.
- Replacement: "the angle between $t_c$ and $-e_3$ (the tilt of the thrust vector from vertical) is limited to
  `MPC_TILTMAX_AIR`".

## Check 4: GNSS-delay finding

Verified against `s8k_gnss_delay.md` and D-s8-gnss-delay: 06 sec. 6.5 line 122 gives the cause (timestamp_sample ==
timestamp, stock 110 ms applied), the lags 112/92/110 ms, the 0.5 m at 5 m/s, the residuals 0/0/-20 and 4/2/-2 ms,
the SIH comparison, the non-retroactivity, and that the inner-loop sets' position-hold numbers (and earlier stages')
carry the artefact in absolute value. It states that the one-seed diagnostic is not a verdict and that its INDI POS
configuration is not a stage-1/2 controller. Fairness: 8.11 says both arms fly with delay 0 and `s8n_oset.sh` line
10 confirms `--gnss-delay 0` for all controllers; the O-13 re-fly of `pid_tuned` under delay 0 (s8l) is cited in
sec. 10 amendment and in 8.11. No defect in the substance.

### R8 (minor) 08_results.md:468-469, wrong file for the session-54 freeze
- What: "frozen in session 54 ... after the O-13 pre-check showed that `pid_tuned` can fly every entry
  (`results/s8l_o13_gnss0.md`)". The freeze pre-check in session 54 was `results/s8i_o13_precheck.md` under the stock
  delay; `s8l_o13_gnss0.md` is the session-56 re-fly under delay 0 after the amendment.
- Evidence: `bench/scenarios.md` sec. 10 "O-13 pre-check (`results/s8i_o13_precheck.md`)" and the amendment "The
  O-13 pre-check was re-flown under it (`results/s8l_o13_gnss0.md`)"; D-s8-gnss-delay last decision sentence.
- Replacement: "after the O-13 pre-check showed that `pid_tuned` can fly every entry
  (`results/s8i_o13_precheck.md`); the pre-check was re-flown for `pid_tuned` under SENS_GNSS0_DELAY 0 before the
  verdict (`results/s8l_o13_gnss0.md`, set unchanged)".

### R9 (minor) 10_conclusion.md:81, "a simulator artefact"
- What: D-s8-gnss-delay classifies the cause as "an estimator configuration error, not a vehicle property" (stock
  gz airframe parameter applied to a zero-latency simulated sensor); 5.9.8 calls it "the simulator's known estimator
  timing issue". Three sections, three labels.
- Replacement (10.6): "after a configuration artefact of the simulated setup was found and removed: the stock
  110 ms `SENS_GNSS0_DELAY` applied to a zero-latency simulated receiver ...". (5.9.8 last bullet: "with the GNSS
  delay-compensation artefact of chapter 6".)

## Check 5: limitations

Stated: single airframe and fixed thrust model (5.9.8), SITL only (5.9.8, 8.11, 6.5), set O frozen before any INDI
POS flight and `indi_pos_v3` screened on T5/H1 only (8.11 protocol, scenarios sec. 10), feedforward share
unmeasured and FF-0 ablation under the old delay (8.11, 9.6, 10.6), O4 payload without inertia and O5 near-level
only (5.9.8), attitude RMS not comparable across pipelines (8.11), accel-bias path not exercised (5.9.4, 5.9.8),
MC_INDIP_DLY identified in sim only (5.9.8), GNSS has no latency in sim (8.11, 9.6).

### R10 (major) 09_discussion.md:103-104 and 10_conclusion.md:82-83, proposed remedy contradicted by the recorded screen
- What: 9.6 "Lowering it, for example by scheduling the specific-force filter by flight phase, is untested"; 10.6
  "Reducing hover effort, for example with a lower outer-loop specific-force bandwidth in hover ... [is a] next
  step". D-s8-freeze tested exactly a lower specific-force bandwidth (5 Hz, half of 10 Hz) on the hover seeds and it
  did not lower hover effort; 5.9.4 of the same report says so ("the hover effort, the failing criterion, was not
  lowered by it (the cause is not the filter bandwidth)"). Presenting it as the untested next step contradicts
  5.9.4 and the decision log.
- Evidence: D-s8-freeze table: hover effort indi_pos_v3 (LPF 10) 0.087, 0.081; indi_pos_v3_lpf5 0.108, 0.088;
  "The 5 Hz filter does not lower it, so the cause is not the filter bandwidth."
- Replacement 9.6 item 3 last sentence: "A lower specific-force filter cut-off (5 Hz) did not reduce it on the two
  screening seeds (D-s8-freeze), so the remedy is not the filter bandwidth; the outer-loop share has no identified
  cause yet, and no other reduction was tried."
- Replacement 10.6 last sentence: "Identifying the cause of the outer-loop share of the hover effort (a lower
  specific-force filter cut-off did not reduce it, D-s8-freeze), and an FF-0 ablation on set O, are the next steps
  before flight."

### R11 (minor) 09_discussion.md:92-93, unmeasured attribution stated as fact
- What: "their gains (72 %, 51 %) come mostly from the measured specific force". Not measured; it is an inference
  from the same paths without disturbance, which the text should make explicit.
- Evidence: O1 (same lemniscate, no disturbance) 31 %; O6 (same vertical sine, no CoM step) 4 % (`s8n_oset.md`).
- Replacement: "The disturbance entries O4 and O5 are less exposed to this: on the same paths without the
  disturbance the gain is 31 % (O1) and 4 % (O6), so most of the 72 % and 51 % is attributable to the response to
  the disturbance rather than to the feedforward."

### R12 (minor) 05_design_implementation.md 5.9.8, "Noise passes into the command" bullet
- What: gives the freeze-time hover effort "about 2.7 times `pid_tuned` on two screening seeds" without the final
  10-seed value 2.02x of 8.11, so the report carries two hover-effort ratios with no link between them.
- Replacement: append "On 10 seeds the ratio was 2.02x (section 8.11, D-s8-hover10)."

### R13 (minor) 11_appendix_reproduce.md:96-97, frozen-firmware condition incomplete
- What: "b9fb3ce5a9 or later without changes to `src/modules/mc_indi_pos_control`". The law is in
  `src/lib/indi_accel_control/` (5.9.3); a change there also invalidates the reproduction. Also, `s8p_hover_effort.sh`
  blocks until `S8N_DONE` appears in `results/s8n_oset.log` (script line 12), which the one-line sequence does not say.
- Replacement: "(b9fb3ce5a9 or later without changes to `src/lib/indi_accel_control` or
  `src/modules/mc_indi_pos_control`)" and after the second command: "# `s8p` waits for `S8N_DONE` in the set-O log
  and writes seeds 3-10 next to the `s8m` seeds 1-2".

## Check 6: internal contradictions

- R10 is the one substantive contradiction (5.9.4 vs 9.6/10.6 on the filter-bandwidth remedy).
- R9: three different labels for the GNSS-delay cause (6.5 / 5.9.8 / 10.6); substance consistent.
- R4: "with margin" (8.11) vs "wide margin" (10.6) vs "met clearly" (s8n).
- Hover attribution "about half / half" (8.11, 9.6, 10.6) is consistent with `s8n_oset.md` (0.03 / 0.05 / 0.08 on
  seeds 1-2) and with 5.9.8's "0.02 inner, 0.03 outer"; all sections say it comes from the s8o screen.
- 8.11 "section 6.5" cross-reference exists (06 line 108).

## Not verified (outside the allowed reads or budget)

- Whether the stock arm receives the reference acceleration through MAVLink (afx/afy/afz) or only position/velocity:
  the report and O-9 say the baseline gets no flatness feedforward; `s8k_gnss_delay.md` says "no acceleration
  feedforward through the stock velocity loop". The runner's type_mask was not inspected.
- The median hover-effort ratio (R5); per-seed values are not in `s8n_oset.md`.
- The s8o screen file itself (attribution 0.03 / 0.05 / 0.08) was read only as quoted in `s8n_oset.md` and
  D-s8-freeze.
- 5.9.6's test count (19) and 5.9.5's identification numbers (`results/s8_ident_gt.md`) were not re-read.

## Overall verdict

Every number in 8.11 matches `s8n_oset.md` and the formal verdict is worded exactly as the criteria require; the
sections are honest about the failed criterion. Two major defects: 10.6 states the O4 payload as 15 % (it is 25 %),
and 9.6/10.6 propose a lower specific-force bandwidth as the untested remedy for hover effort although D-s8-freeze
and 5.9.4 record that it was tested and did not help. Eleven minor wording, cross-reference and caveat items.
