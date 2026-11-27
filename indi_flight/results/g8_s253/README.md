# G8 report check (S253)

Command (repo root): `timeout 300 bash indi_flight/bench/gate_g8.sh > indi_flight/results/g8_s253/gate_g8_out.txt 2>&1`
Date: 2026-11-27. Exit code 0 (all 7 checks PASS). Read-only; nothing committed.

| check | result |
|---|---|
| 1 evidence paths exist | PASS |
| 2 G1 limits and G3 excluded corners listed | PASS |
| 3 bring-up checklist | PASS |
| 4 errata and history appendix | PASS |
| 5 docs/ko zh uk diff vs main empty | PASS |
| 6 user page in docs/en only | PASS |
| 7 markdown lint | PASS (n/a: no docs target) |

No FAIL.

Changed vs g8_s247: checks 1 and 2 were FAIL, now PASS. Check 1: the G8 row of GATE_STATUS.tsv
no longer has "-" as evidence. Check 2: report/*.md now contains the saturation-corner / excluded
corner and "beyond-range" wording. Checks 3-7 unchanged (PASS).

Caveat: check 2 is keyword based (presence of words, not correctness); check 5 compares to local main.
