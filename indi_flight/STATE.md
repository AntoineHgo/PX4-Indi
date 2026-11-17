# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 3 (inner loop) opened S49; stage 2 (analysis tools, margins) from S36, provisional under Q4-A; stage 1 frozen S36 (G1 FINAL). Started S1 (2026-11-15). Stage 0 done. Session 3: ref airframe model done.
- Gates: G1 open | G2 open | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open. G1 FROZEN with evidence limits (GATES.md G1 FINAL), not passed until Q2-Q4 answered.
- Blocker: none. S50: owner answered Q2 (A amended), Q3 (A), Q4 (A + G1.7 provenance); GATES.md updated, provisional mark lifted; QUESTIONS.md empty. Q1 closed: A confirmed by owner; flatness A18 reviewed (r5 BLOCKING), answered in
  `design/flatness_r2.md` (S15): optional increment after base A. Outer-loop study finished; stage 5 = base A.
- S36: G1 FINAL written in GATES.md (frozen with 5 evidence limits, provisional under Q4-A, not marked passed);
  stage 2 started provisionally; opus review T73 r1 BLOCKING (gyro break misses INDI's model and rotor-speed
  paths) answered by D-G2-BREAK (M3a torque-setpoint break) and note section 7; r2 CLOSED.
## Next actions (in order)
S44-S67 history: JOURNAL.md. Agent ledger: LEDGER.md. Lessons proposed: LESSONS_PROPOSED.md (agent cost calibrations: read before sizing a brief).
NEXT (S65), per route check 64 (inner loop time-boxed: 1 session per law change from now on):
   (1) stage-5 slice 2: thrust-gap hover in position mode (NEW scenario, N1 C3; MC_INDI_W_MAX 2700) + one
   velocity/acceleration mode (altitude or position stick) + T123 deviations A3/A5/reset; haiku second key.
   (2) Bench defect N1 C2 (disturbance.py payload_add/com_shift/gust sized for x500): take mass/drag from the flown
   model, G1.5 check per profile. (3) Check the 'NOT FOUND' hooks of the draft (loop delay, GNSS latency, vibration)
   against stage-1 sim work before building. (4) G2-STEP 400 Hz reported run DONE S64 (9/9 within limits, A-30 seed spread parked).
   (5) attitude-break margin with the new setpoint path (G2) when the G2 table is resumed.
   Later: G5 build order (draft end), combined opus review of stage-3 safety diff + stage-5 slice before any freeze.
   S65-S68 session notes: JOURNAL.md (S69 entry).
   S69 (launch 20261118-000439, cap $3): route check 69 filed (stop anomaly chasing). A-32 PARKED: host load, not a
   regression (seq 1.5 ms = S32, 5-parallel 11 ms); G1.6 = sequential runs (GATES note s69). A-30 PARKED (INDI seq
   rise <= 4.3 ms). N2 closed; Q5 addendum 6 (move to JOURNAL at S70 unless owner objects). Slice-2 plan written.
   NEXT S70 (per route check 69): stage-5 slice 2 from `design/slice2_plan_s69.md` (brief, haiku fact check and HTE note
   at its end): one sonnet implementation agent (2 position-mode thrust-gap scenarios via motor_fault motors list,
   params with MC_INDI_W_MAX, truth-altitude metric + self-test, 3-flight pre-test), haiku second key on the metric;
   flights SEQUENTIAL when a same-seed or step claim is made. Then T123 deviations A3/A5/reset (McIndiPosControl.cpp
   :147/:161/:205). Runner has NO RC/manual_control path: needed for G5 stick modes (slice 3). S71: 2nd mode slice
   + combined opus review of stage-3 safety diff + stage-5 slices. Then hooks (loop delay, GNSS sample delay, per-run
   drop seed, IMU noise scale). Next route check: S74.
   S70 (launch 20261118-001644, cap $3): Q5 closed. T156 done (`results/stage5_s70/README.md`): INDI outer loop
   keeps the thrust gap, z 0.31 m (HTE on) / 0.37 m (frozen) at 4x0.85, 0.19 m at 1 motor 0.8; stock 0.01 m. A11
   confirmed. D-GAP PROPOSED in DECISIONS.md: rate-loop complementary blend on the measured collective.
   NEXT S71: (1) opus review of D-GAP, brief ready `design/dgap_review_brief_s70.md` (~$1.1, launch first); (2) sonnet: implement
   blend in McIndiPosControl/lib + unit test that fails without it + T123 item 1 (reset on setFilter); fly gap085 /
   loss08 INDI, sequential; (3) PVA mode slice (ZSINE_O6). (4) s5_gap_check: apply the run.json->ulog time offset (second key, README). Single-flight results: same-seed spread not measured.
   S71 (launch 20261118-003022, cap $3): T158 opus D-GAP r1 = BLOCKING (edge semantics; rate-loop blend SNAPS b to the
   gap when landed/off/telemetry invalid, indi_rate_control.cpp:336-345, against A16). D-GAP amended in DECISIONS.md
   (freeze rules, anti-windup, coll_model path, new overturn on HF mode, tb window 0.3-2.5 s, tests). Time-offset
   hypothesis + closing test in results/stage5_s70/README.md.
   T159 sonnet r2 (design/dgap_review_r2.md) OPEN on wording (recovery, overturn 'no tb passes', test tolerances);
   fixed in DECISIONS.md -> D-GAP ACCEPTED for implementation.
   NEXT S72: (1) launch sonnet with `design/dgap_impl_brief_s71.md` (code + 8 unit tests with break checks +
   gap085_indi_htoff/loss08_indi sequential, |dz| < 0.06 m) -> results/stage5_s72/README.md; haiku second key on dz;
   I read the firmware diff and run the tests; (3) the rate-loop snap-vs-freeze question goes into the
   combined opus review of the stage-3 safety diff + stage-5 slices; (4) PVA mode slice (ZSINE_O6).
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|

## Open problems
- Review notes folder (`indi_project/review/external_review_s59_notes/`) not read in full at stage 0 (budget);
  open per item: `sim_review.md` for simulator work, `module_parity.md` for stage 3/5, `test_review.md` for stage 3,
  `ident_review.md` for stage 4, `remetric.py`/`hover.py` for the errata.

- S38 GM jump explained (T80, `results/stage2_s38/gm_jump_check.md`): INDI measured Tb 0 phase grazes -180 deg on a
  plateau 12-27 Hz; at 800 Hz it crosses at 11.9 Hz (21.1 dB), at 400 Hz only at 27 Hz (34.8 dB) though |L| at 11.9 Hz
  is -22 dB. Model GM is phase-shape sensitive there: in S41 compare measured |L| over the plateau, and report GM
  together with the minimum |L|^-1 where phase is within 10 deg of -180 (decide in GATES.md before the first G2 test).
- Unmodelled in margins_models.py (T78 UNVERIFIED list): AlphaFilter coefficient formula, LPF2p coefficients from
  memory, gz/ESC latency 0, measured path = eta x motor state, yaw, attitude loop; 267 Hz analytic only.
