# Questions to the owner

No open question (S50). Q1-Q4 closed, archived in JOURNAL.md.

## N1 (2026-11-17, owner note written between S60 and S61): off-loop work, step criterion, bench defects. Not blocking.

Act on this entry first in S61, before the S61 plan in STATE.md (item B changes its order). Then mark it closed and
move it to JOURNAL.md.

**A. What happened while the orchestrator was stopped (08:37-18:20).** Three owner commits, not yet in STATE.md:
- d48766751a: `run_scenario.py` started `disturbance.py` without `--model`, so the injector always pushed on `x500_0`;
  on quad5in every disturbance scenario applied no wrench. Fixed (`--model <model>_0`). New scenario `torque_steps`
  (2 s body-torque steps: roll 100, pitch 100, yaw 30 mN m, position hold). No earlier `indi_flight/results` run used a
  disturbance scenario on quad5in (checked), so no committed result is invalidated.
- 002b4d2df0: a relative `--out` made the injector resolve its trigger file under itself and apply nothing, silently.
  The runner now makes `--out` absolute.
- 018e37683e: ad hoc INDI vs PID comparison, `results/indi_vs_pid/` (quad5in, sim v2, 800 Hz, seed 1, speed 4, same
  attitude P and stock position loop, `indi.params` = S59 hover.params, K_R/K_P/K_Y default). NOT gate-bearing: one seed,
  dirty tree (injector fix uncommitted at flight time). Findings (`metrics.md`):
  - roll/pitch 15 deg steps: INDI overshoot 13.8 / 12.6 % (PID 0 %), 2 % settle 659 / 664 ms (PID 380 / 389 ms),
    rate-tracking RMS 14.5 deg/s (PID 9.3); rise time equal (~180 ms).
  - yaw 45 deg step: INDI overshoot 3.4 % (PID 0.2), settle 1303 ms (PID 1233), rise 476 ms (PID 660).
  - torque steps: INDI rejects better, yaw markedly (peak 4.8 deg vs 14.5), roll/pitch peak ~10 % lower.
  The overshoot is not explained yet: D-RATE-LEAD found PM 29 deg at the torque break without the lead, but this
  comparison flew with MC_INDI_LEAD 1 (M3a PM 59-87 deg). The M3a break does not show the attitude step response:
  find the mechanism (rate setpoint lag, attitude P on a slower inner loop, ...) before choosing the fix.

**B. Owner decision: attitude step criterion, fixed before the thrust-gap work.**
1. Confirm first. Re-fly step_roll, step_pitch, step_yaw with INDI and PID on at least 2 more seeds (gate-bearing if
   G1.7 allows: clean tree, binary rebuilt at HEAD; use `results/indi_vs_pid/fly.sh` as the command template). If the
   INDI overshoot/settle gap holds on >= 2 seeds, go to 2; if it does not, record why seed 1 differed and resume S61.
2. Write an attitude step criterion into GATES.md (the inner-loop gate, before its first test): ABSOLUTE thresholds
   (overshoot, 2 % settle time, per axis) derived from the PID reference numbers measured in step 1 and justified in
   DECISIONS.md. F-5 stands: no gate is a ratio to PID; PID only informs the threshold values. Owner's starting point:
   roll/pitch overshoot <= 5 %, settle no more than ~10 % above PID's measured value; tighten or justify a change.
3. Fix the default INDI tuning to pass it BEFORE the S61 thrust-gap flights. The fix is yours to choose (attitude P
   under INDI, K_R and lead limits, reference model, ...) within F-1 and F-3: generic, robust defaults, no per-airframe
   hand tuning, margins (G2) not traded away. Check the fix keeps the torque-step rejection of item A.

**C. Bench defects to fix (found by the owner, not fixed).**
- `bench/run_scenario.py:285` queries `gz model -m x500_0`: `gz_model_info.txt` is empty on every quad5in run. Use
  `<model>_0`.
- `bench/disturbance.py`: `payload_add` and `com_shift` size their force from `X500_MASS_KG`, `gust_x`/`gust_diag` use
  the x500 drag area `CD_A`. On quad5in these disturbances are mis-sized. Take mass and drag from the flown model.
  `torque_steps` is not affected. Give each profile its G1.5 check before its first campaign (GATES.md G1.5 row).
- The S61 thrust-gap flights use `motor_fault` / `thrust_sag` (SIM_GZ_* params), which are not affected by the injector
  bug, but every scenario using them is attitude-mode (`_ATT`). A hover on the stage-5 slice with a thrust gap needs a
  new scenario.

**D. Untracked results.** About 283 files (~39 MB, `results/` of S10-S32: metrics.json, run.json, csv, sched.txt, ...)
were never committed. Leave them as they are: do not commit, move or delete them. From now on, at the end of the
session that produced a run, commit its metrics and run metadata (metrics.json, run.json, README) as MISSION.md says;
raw logs stay untracked. `git status` should show no untracked file you created.
