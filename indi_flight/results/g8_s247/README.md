# G8 report check (S247)

Command (repo root): `bash indi_flight/bench/gate_g8.sh | tee indi_flight/results/g8_s247/gate_g8_out.txt`
Output: `gate_g8_out.txt`. Exit 1 (checks 1 and 2 FAIL). Read-only; report content not changed.

| check | result | what a FAIL needs |
|---|---|---|
| 1 evidence paths | FAIL | G8 row of GATE_STATUS.tsv has "-" as evidence: it needs a path (e.g. the results dir of the G8 run and this output). All other rows resolve. |
| 2 G1 limits, G3 excluded corners | FAIL | G1 limits 1-5 are found (03_validation.md). Missing: the G3 excluded corner (saturation-corner draws, 2.0 x hover with a weak motor on, GATES.md Route B) and the "class (b) beyond-range physics" statement. 04_limits.md has draw 264 but not as the stated excluded corner. |
| 3 bring-up checklist | PASS | report/06_bringup_checklist.md exists |
| 4 errata and history | PASS | report/A_history_errata.md and results/errata.md exist |
| 5 translations | PASS | `git diff --stat main -- docs/ko docs/zh docs/uk` empty |
| 6 page in docs/en only | PASS | docs/en/config_mc/indi_control.md exists; no non-image indi file elsewhere in docs/ |
| 7 markdown lint | PASS (n/a) | no docs/lint make target (only `msg_docs`, a generator) |

Detection notes: check 2 is keyword based (`holes`, `Commander tick`, `A-14`, `A-19`, `SENS_BAR_AUTOCAL`,
`saturation-corner|excluded corner`, `beyond-range`), so it proves presence of the words, not correctness.
Check 1 treats a bare filename after a path in parentheses as living in the previous sibling's subdirectory
(G5 `G58_KEY2.md`). Check 5 compares the working tree to local `main`, not origin/main.
