## G8 verdict (S257, 2026-11-27): PASSED, with the listed limits (draft, not inserted)
Evidence: `bench/gate_g8.sh`, output `results/g8_s257/gate_g8_out.txt`, 7/7 checks PASS.
- (a) Every gate section has an existing evidence path: PASS, gate_g8.sh check 1; report chapters 01-04, 06, A, g2_margins.
- (b) G1 evidence limits and G3 excluded corners listed: PASS, check 2; `report/04_limits.md` 4.1 (G3), 4.2 (G6).
- (c) Hardware bring-up checklist present: PASS, check 3; `report/06_bringup_checklist.md` (6.7 Unverified lists the open B3-B8 items).
- (d) Errata and history appendix: PASS, check 4; `report/A_history_errata.md`.
- (e) `git diff main -- docs/ko docs/zh docs/uk` empty: PASS, check 5.
- (f) User page in `docs/en` only: PASS, check 6; `docs/en/config_mc/indi_control.md`, links resolve, tables aligned.
- (g) Markdown lint: not applicable, check 7 (no docs make target; prettier not installed offline, manual check done).
Limits:
- Unverified claims: 47 listed (01: 11, 02: 7, 03: 10, 04: 6, 06: 7, A: 5, g2_margins: 1), each marked "Unverified" or
  `[open: ...]` in the chapter text; checked one by one only for 20 (S254, S255), the rest marked in one pass per RC256.
- R1 "refuse to arm without eRPM" is not enforced in firmware (QUESTIONS.md Q36): pending owner Q36, option A
  recommended (reword R1 to "eRPM telemetry required for the validated configuration; without it the modelled actuator
  state runs, not validated"); the bring-up checklist checks telemetry before first flight.
- G3 is NOT PASSED (report 03_validation.md 3.3 with data, 04_limits.md 4.1 limits and corners) and G6 is NOT PASSED
  (03_validation.md 3.6, 04_limits.md 4.2; item 7 un-identified start 6/58 failures, 10 start runs not flown).
- All evidence is simulation only (04_limits.md 4.5); no hardware flight.
Proposed verdict: G8 PASSED with the limits above.
