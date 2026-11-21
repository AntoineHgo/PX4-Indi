# RESCORE V2: G3 item 2 = p, q, r, position only (chatter is G4)

## Change
- GATES.md line 304: item 2 = "No sustained oscillation on p, q, r and on position, whole flight". Motor command chatter is a G4 criterion (GATES G4 "Additional" ~361, Q14 A ~553).
- bench/g3_checks.py (key1): `item2_oscillation.pass` = not any sustained in p, q, r, position. `command_chatter` is still computed and reported inside `item2_oscillation` unchanged; new top-level `g4_command_chatter_sustained` (bool; None if never airborne). Docstring updated.
- bench/g3_checks_key2.py (key2): its `item2_oscillation.pass` already excluded chatter, but its top-level `pass` also ANDed `chatter.pass` (a second G3 failure on a G4 criterion). Top-level `pass` is now items 1-3 only. `chatter` block unchanged (its `pass` = no chatter); new top-level `g4_command_chatter_sustained` = not chatter.pass. Docstring updated.
- Chatter detectors untouched.

## Callers checked (none loses the chatter flag)
- bench/g3_score.sh, g3_score_docker.sh: run g3_checks.py and store the JSON; nothing parses item 2 chatter. No edit.
- bench/a55_key1_all.sh: prints every key containing "chat" or starting with "item"; key1 now additionally shows g4_command_chatter_sustained, key2 shows chatter + the new boolean. No edit.
- bench/g4_chatter_skip_key1.py / g4_chatter_skip_key2.py: import only the detectors (line_detector, K.chatter), do not read item 2 or `pass`. No edit.
- gate_g4.sh, g4_metrics*.py, g510/g5 checkers: no reference to g3_checks outputs. No script relied on chatter inside item-2 pass, so none was switched to the boolean.

## Tests (scipy 1.18 from a scratch PYTHONPATH install; pytest absent, test functions called directly)
- bench/tests/test_g3_checks.py (key1): chatter60 and chat_hirms now expect item 2 PASS, G3 pass, `g4_command_chatter_sustained` True; new `rate2hz` (8 deg/s at 2 Hz on p) expects item 2 FAIL, flag False. Self-test PASS, --break-check PASS (all cases caught).
- bench/g3_checks_key2.py --self-test (key2, in-file): added chatter-only (70 Hz) -> item 2 pass, flag True, G3 pass; clean -> flag False; 15 deg/s 2 Hz on p -> item 2 fails. All PASS.
- Also pass: test_g3_excursion_s186, test_g3_excursion_key2 (6), test_g3_checks_key2_q14_q15 (4 functions), test_g4_chatter_skip_key1, test_g4_chatter_skip_key2 (its FAIL lines are the intended broken-skip demonstration, final line OK).

## Re-score (key1 args from key1/args.txt, outputs in rescore_v2/key1 and rescore_v2/key2)
Key1 item 2 changed from fail to pass in 11 runs (000, 001, 002, 005, 006, 009, 010, 014, 015, 018, 019): chatter-only. Key1 overall changed F->P in 8 runs (000, 001, 006, 010, 014, 015, 018, 019); 002, 005, 009 stay F on item 3. Key2 verdicts are numerically identical to the old key2/ files (float noise ~1e-12 only); its overall stays F everywhere because key2 item 3 fails everywhere.

Table order K1/K2, P = pass, F = fail. Chatter Y = sustained (G4 report only).

| run | item1 K1/K2 | item2 K1/K2 (axes K1 / K2) | item3 K1/K2 (failing) | chatter G4 K1/K2 | overall K1/K2 | agree |
|---|---|---|---|---|---|---|
| run_000 | P/P | P/P (- / -) | P/F (- / horiz 3.08) | Y/Y | P/F | NO |
| run_001 | P/P | P/P (- / -) | P/F (- / horiz 3.12) | Y/Y | P/F | NO |
| run_002 | P/P | P/F (- / q) | F/F (horiz 0.69 / horiz 3.73) | Y/Y | F/F | NO |
| run_003 | P/P | F/F (p,q,r / p,q,r) | F/F (horiz 0.45,alt -0.27 / horiz 3.23) | n/n | F/F | yes |
| run_004 | P/P | P/P (- / -) | P/F (- / alt -0.25) | n/n | P/F | NO |
| run_005 | P/P | P/P (- / -) | F/F (horiz 0.60 / horiz 3.65) | Y/Y | F/F | yes |
| run_006 | P/P | P/P (- / -) | P/F (- / horiz 3.04) | Y/Y | P/F | NO |
| run_007 | P/P | F/F (p,q,r / p,q,r) | F/F (alt -0.10 / horiz 3.06) | n/n | F/F | yes |
| run_008 | P/P | F/F (q / q) | P/F (- / horiz 2.73) | Y/Y | F/F | NO |
| run_009 | P/P | P/P (- / -) | F/F (horiz 0.34 / horiz 3.33) | Y/Y | F/F | yes |
| run_010 | P/P | P/P (- / -) | P/F (- / alt -0.61) | Y/Y | P/F | NO |
| run_011 | P/P | P/P (- / -) | P/F (- / horiz 2.91) | n/n | P/F | NO |
| run_012 | P/P | P/P (- / -) | P/F (- / horiz 2.87) | n/n | P/F | NO |
| run_013 | P/P | F/F (p,q,r / p,q,r) | P/F (- / horiz 2.52) | Y/Y | F/F | NO |
| run_014 | P/P | P/P (- / -) | P/F (- / horiz 3.07) | Y/Y | P/F | NO |
| run_015 | P/P | P/P (- / -) | P/F (- / horiz 3.08) | Y/Y | P/F | NO |
| run_016 | P/P | P/P (- / -) | P/F (- / alt -0.45) | n/n | P/F | NO |
| run_017 | F/F | F/F (p,q,r / p,q,r) | F/F (horiz 0.48,alt -0.22 / horiz 3.38) | Y/Y | F/F | yes |
| run_017_pid_s185 | P/P | F/F (p,q / p,q) | P/F (- / horiz 2.77) | n/n | F/F | NO |
| run_018 | P/P | P/P (- / -) | P/F (- / horiz 2.58) | Y/Y | P/F | NO |
| run_019 | P/P | P/P (- / -) | P/F (- / horiz 3.06) | Y/Y | P/F | NO |

Key agreement on items 1, 2, 3 and overall: 5/21 runs. Disagreements: ['run_000', 'run_001', 'run_002', 'run_004', 'run_006', 'run_008', 'run_010', 'run_011', 'run_012', 'run_013', 'run_014', 'run_015', 'run_016', 'run_017_pid_s185', 'run_018', 'run_019']

## Notes on the disagreements
- Item 1 agrees on all 21. Item 2 agrees on 20/21; run_002: key2 flags q, key1 does not (not caused by this change; key2 item 2 was already chatter-free).
- Item 3 disagrees on 16 runs because key2 does not take the key1 args: it uses its own window (last 10 s of the hold, from run.json) and its own reference (median position in the first second of the hold). It reports horizontal RMS 2.5-3.7 m, i.e. the hold-start reference is not the setpoint; key1 uses the --t0/--t1 3 s window with the setpoint median reference. Pre-existing and unchanged; it needs an owner decision before key2 item 3 is comparable. Overall disagreement follows from item 3 (and run_002 item 2).
- Chatter flag agrees K1/K2 on all 21 runs.
