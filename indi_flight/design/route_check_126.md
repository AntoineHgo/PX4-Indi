# Route check 126 (S126)
Inputs: STATE.md, DECISIONS.md (D-IDENT, D-IDENT-J, headings), ANOMALIES.md, JOURNAL tail, RC122.
No flights run for this check. Evidence is what STATE/JOURNAL record.

## 1. Still the shortest path?
No. RC122 set S123 (flight), S124 (verdict + defaults draft), G5 list at the end of S124, G5 build S125-S128.
Delivered: S123 flight done, S124 roll/pitch G1 within 0.8 % of derived from three starts (conditions (i)-(iii)
effectively met for roll), S125 halved-gain roll 1757.9 PASS. All that is good, and the roll/pitch estimator is
finished. Since then S125-S126 went to the yaw axis: G1_Y 165 vs 205 (A-43), found to be an omitted rotor-drag
term in the model, residual +3/+7 % (A-44). That is a refinement of an axis whose parameter (205, derived from
source) is already kept and within bound. No defaults file exists yet, no G5 list, and stage 5 (outer loop for every
mode replacing mc_pos_control) has no code beyond the hover slice (D-S5-SLICE) and ALTCTL z (D-ALTCTL-Z).
126 sessions, G1 passed, G2-G8 open: the gates that need stage 5 (G5, then G3/G6/G7/G8 evidence) cannot move
until it exists. Ident accuracy is not on the critical path of any gate: G4 needs a defaults file and a minimal
profile, not a 3 % yaw estimate.
Slip against RC122: about 2 sessions, all of it spent below the accuracy that any gate asks for.

## 2. Which decision?
D-IDENT with owner Q6 = B (INDI flies its own identification), already named in RC122. The current symptom is its
acceptance conditions (i)-(v) plus D-IDENT-J (S125) turning every estimator discrepancy into a stage-4 task: the
yaw fit has no consumer deadline, so it has no stopping rule. Second cause, same as RC122: D-GATES-G3G8 (S94) put
evidence campaigns ahead of the defaults file and the outer loop. The structural problem is that "defaults" and
"estimator proven" were made one deliverable; the defaults depend only on derived values already agreed within
0.8 % (roll/pitch) and 7 % (yaw).

## 3. Fresh start on stage 4
- Defaults first: write the defaults file from derived airframe values (already matched by the ident for roll,
  pitch, and within 7 % yaw) with the conservative ident configuration, this session. Ident becomes a verification
  of the file, not its source.
- One acceptance table with a numeric tolerance per parameter, set once (G1 10 %, yaw 10 %, G2_Y 15 %) and a rule:
  inside tolerance on two starts = done, no keyed-estimator iteration. The yaw fit is inside 10 % today.
- Conditions (iv) and (v) as offline checks on the existing logs (conditioning number of the regression already
  computed; a PID-flown log exists from G3 probes), not new flights, not new keys.
- Estimator effort capped at 3 sessions total; the remaining physical parameters (ACT_TC, W_MAX, thrust curve,
  ERPM_DLY) take derived defaults flagged "conservative, not identified" until a G4 profile needs them.

## 4. Recommendation, next 3 sessions
- S127 (1 session): freeze stage-4 ident as is. Time-box A-44 to zero further work: keep 205, bound +7 %, park the
  V0 597 synthetic mystery (reopen only if a G4/G2 yaw cell fails or a flight uses a yaw gain that depends on G1_Y
  beyond 10 %). Do the cheap (iv) conditioning report and (v) PID-log comparison offline on existing logs, one
  paragraph each in D-IDENT. Write the defaults file (ident config, gains halved, ident-status parameter) and
  load it into the base params with fingerprint check (RC122 section 4: confirm it is read by the module).
- S128 (1 session): stage-5 build list for every mode, then code. Order by flying value: POSCTL, ALTCTL (exists),
  MANUAL/stabilized pass-through, AUTO (mission/loiter/RTL/land/takeoff via trajectory setpoints), OFFBOARD. Base
  A, POS_EN=1 in base params, no flatness, no new anomaly chase. Hover slice extended to position hold with
  setpoint tracking, one SITL smoke flight per mode (not a campaign).
- S129 (1 session): remaining modes and fallbacks (failsafes, descend/land with thrust loss), then G5 draft run on
  the smoke set; first real G5 probes of the whole stack.
Cut or defer: J statistic refinement (D-IDENT-J is already diagnostic only: no further work), yaw D-term model
polish, V0 synthetic, A-4, A-6, A-35/A-36/A-39 (A-6 ablation is stage-5 side-cell work), G3 campaign and
g3_checks/gate scripts (until a G5 exists), G4 profiles beyond one minimal profile, offline outer-cell margin work.
Identification refinement is therefore deferred behind stage 5, not time-boxed alongside it: it returns after the
first full-mode stack flies, when a failing G2/G4 cell names the parameter that needs better accuracy.
Next route check: S129 (after the G5 draft run). If S128 has no multi-mode code, the owner is asked whether stage 5
should be scoped to POSCTL + AUTO for first evidence.
