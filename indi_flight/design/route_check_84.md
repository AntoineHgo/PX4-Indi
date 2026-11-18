# Route check 84 (S84 start, 2026-11-18)
Read: STATE, GATES (G2, G2-STEP, G3-G8 draft headers), DECISIONS (D-GAP, D-G2-PINJ, D-RATE-BLD, D-outer-arch by title/summary),
ANOMALIES, JOURNAL tail S79-S83, route_check_79, MISSION gates and order of work. No code opened, nothing flown. Gates 0/8 after 83 sessions.

## 1) Still on the shortest path?
Partly. The injector and stick slices are on path for G2 (outer loops) and G5 (stick modes), but the route is long: 83 sessions,
all gates open, and STATE still calls the stage "3 (inner loop)" while work is stage 5. Nothing has been written as a gate PASS.
- Soonest closable: G2. Rate loops are measured and pass at 800 and 400 Hz (PM 68-70, GM 13-16 dB, DM 43-51 ms). Velocity/position
  break with the accel loop closed is measured (z PM 57-59 deg, S82-S83). Missing for G2: stage-output accel-loop break, attitude
  break with the new setpoint path, xy and yaw, the 267 Hz reported run, model-only vs `--sim v2` configs, worst-of-2-seeds, second key,
  and the "one command per item" runner (GATES.md says "to be named when the runner exists"). Blockers: those runs, not a design question.
- G1 is frozen but "not passed until Q2-Q4"; the owner answered Q2-Q4 in S50, so closing it is a bookkeeping step nobody has done
  (confirm G1.7 provenance lines, write PASS). That is the cheapest gate and has been idle for 33 sessions.
- G3-G8 are drafts (NOT final, S64). G5 (stick metric, thrust-gap, outer-loop hover) cannot start passing before its text is final.
- Drift risk: each session ends with a new "NEXT" list while evidence items (second keys, re-flies of 33 Hz rows) consume the budget.
  S83 spent a session on a stick re-fly caused by a README overclaim and on a D-GAP overturn test that came out "not met" (good news).

## 2) Which decision is the difficulty a consequence of?
Decision 2 (measured actuator state fed back, no PID fallback), now for the outer loop: D-GAP (blend of measured collective,
tb 1.0 s) and its sibling D-RATE-BLD. Each loop needs its own break point, injector, model and second key (D-G2-BREAK, D-G2-INJ,
D-G2-PINJ), so G2 is five to six separate campaigns. Compounded by D-outer-arch A + A18 flatness (more paths to cut) and the
sim-time/determinism requirements (G1.6) that make every flight expensive to trust.

## 3) Fresh start on this stage
- Build one generic loop-break injector (rate, stage input, stage output, attitude) driven by one config table and one runner
  command, instead of one injector per session with a separate brief and second key each time.
- Write G3-G8 final text and the flight matrix first, so stage-5 slices are chosen by gate coverage, not by the last open item.
- Treat model cross-check as advisory until G2 passes (as RC79 already said); no PM/f_c anomaly rows without a failing gate test.
- Fly stick modes on the 50 Hz grid from the first run, with the README claiming only what a table of rows supports.

## 4) Ranked recommendation, S84-S86 (about $3 each)
1. S84 (no agent, ~$0.5): close G1 bookkeeping in GATES.md/STATE.md if Q2-Q4 evidence holds (owner answers exist); finalise the G2 table
   skeleton in GATES.md listing every (loop, break, rate, config) cell with status; mark cells already measured (rate roll/pitch/yaw
   800/400, z velbreak). Then one sonnet agent (30 calls): stage-OUTPUT accel-loop break (extend MC_INDI_PINJ_* in
   mc_indi_pos_control, files: DECISIONS.md D-G2-PINJ, bench/pinj_csv.py, new brief_accbreak_s84.md), flights in the same session, second key next.
2. S85: finish G2 outer cells: xy velbreak and position break, accel-loop break at 800/400, attitude break with setpoint path; write the
   single runner (e.g. bench/g2_run.sh) and run worst-of-2-seeds. Haiku second keys in the same session, not the next.
3. S86: G2 report and PASS/FAIL decision on 800/400, 267 reported run; in parallel finalise G5 text (stick metric vs
   vehicle_local_position_setpoint, with sched anchor for stick mode) in GATES.md. Combined opus review (e) of the stage-3 safety diff and
   stage-5 slice goes after the G2 report, as one task (about $1.5), not before.
Defer: A-4, A-6, A-34, A-35, A-30, A-32 (no gate failure triggers them), A-6 only when G5 runs.

## 5) Route check 79 recommendations
1. MC_INDI_ACT_BLD 1.0 default committed, D-RATE-BLD ACCEPTED, A-34/A-35 parked: yes (a94d5c181a, S79).
2. D-GAP outer-loop injector: yes, as D-G2-PINJ (S82) at the stage INPUT; flights and second key done S83. Partial for G2: stage-output
   break still missing.
3. Runner RC/manual stick-path stub and PVA slice (ZSINE_O6): stick stub yes (S82-S83); PVA slice no; combined opus review (e) no (pushed again).
4. Rule "no new inner-loop item without a failing gate test": largely yes (S80-S83 stayed outer/stick); the S83 stick re-fly was an
   evidence defect, not an anomaly chase.
