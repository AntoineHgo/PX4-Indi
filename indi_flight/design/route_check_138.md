# Route check 138 (written for S139)

Read: STATE.md, DECISIONS.md (D-F7-GROUND, D-KY, headings), ANOMALIES.md, JOURNAL.md tail 5, GATES.md section 5, route_check_133.md.

## 1. Still on the shortest path?
Yes. The RC133 drift (no G5 criteria, edge-seam patches) is fixed: G5 text is final (S134), the seam was removed rather than
patched (D-F7-GROUND), A-46 closed (S135). Sessions S135-S137 each moved a gate row. One mild drift: S136-S137 spent three
sessions on one row (G5.1), because a K_Y archive default (10) was never justified. Rows left: G5.2/5.3/5.5/5.7 (existing
scenarios, only checkers missing) and G5.6/5.8-5.11 (injectors). G2-G8 stay open until the stage-6 freeze re-fly.

## 2. Which decision is the difficulty a consequence of?
D-DEFAULTS-FW (S128) inherited archive values unchecked (K_Y 10), found only when G5.1 flew; D-KY is the fix. The wider
cost is D-IDENT-STOP (freeze ident, fly stage 5 first): every default change since re-opens G2 cells (S137 re-measured
rate-yaw). Accepted, since G2 re-fly is planned at freeze anyway.

## 3. What a fresh start would do differently
Fly every row once, coarse, with the existing scenarios before tuning anything (one batch of all four ready rows), and audit
each inherited default against its G2 cell before the first gate flight. Inherited constants are the failure source, not new code.

## 5. Gate items moved since RC133
G5 criteria written final (S134); G5.4 probe 9/9 PASS (S135, edge step 4.6-6.0 % < 10 %); A-46 closed; G5.1 tooling + probe
6/6 PASS at K_Y 20 (S137); D-F7-GROUND replaced D-STAGE-STALE/D-HANDOVER; EdgeState dropped. G2 rate-yaw cells re-measured
(GM 18.8/14.3 dB, PM 78/82). Nothing frozen; G1 unchanged.

## 6. Cut, merge, defer (STATE.md next actions)
- Merge action 3 into ONE batch: G5.2, G5.3, G5.5, G5.7, 3 seeds, one session, existing scenarios, probe status.
- Write passthrough_check / offb_vel_check self-tests only for the rows flown; move the self-test part of action 5 out of G7
  into that batch (the checkers are needed now), keep module harness/MC_INDI_ID_OK in G7.
- Action 4: build ONE shared event injector (maybe_landed, kill, EKF reset, RC/link/offboard loss) with a single G1.5 check,
  not one injector per row; order 5.6, 5.9, 5.11, 5.8; defer 5.10 (saturation) to share the G3 weak+sat cell.
- Defer: "log z-only flag", offline G2 todo until after G5 probes finish; keep the STOP list.
- Before the freeze: audit remaining archive defaults against G2 cells (one session, no flights).
Owner rules respected: no PID fallback or pass line, no thresholds touched, reuse runner/checkers, probes before freeze.
