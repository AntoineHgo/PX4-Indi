# Brief: outer-loop (acceleration) break injector in mc_indi_pos_control, written S82

Task T170, one `sonnet` agent (~$0.9, ~30 tool calls). Second key (haiku/sonnet, code to this spec) in a later session.

## Goal and what it serves
G2 needs measured margins at the INDI acceleration/velocity loop break, and D-GAP (`DECISIONS.md` D-GAP, S71
amendment item 3) has an overturn test that needs "velocity-break PM at tb = 1.0 s and tb/3". No outer-loop injector
exists (`results/stage3_s77_400/velbreak_search.md`, read it first: it lists the publish points and what is missing).

## Specification (mirror D-G2-BREAK / D-G2-INJ, `DECISIONS.md:191-215`, and the rate code in
`src/modules/mc_indi_rate_control/McIndiRateControl.cpp` inject block, ~lines 231-242)
1. Parameters in `mc_indi_pos_control` params yaml: `MC_INDI_PINJ_AX` (0 off, 1 x, 2 y, 3 z, NED acceleration
   axis), `_AMP` (m/s^2 per sine component), `_TP`, `_FMIN`, `_FMAX`, `_NP`. Names <= 16 chars, follow
   `.github/instructions/*.instructions.md` that match the paths. Off by default; bench-only wording in the docs.
2. Break point: the module's commanded acceleration c (the INDI law's output, before conversion to thrust vector /
   attitude). u = c + d replaces c everywhere downstream AND in every state the law feeds back (previous command,
   blend/D-GAP state input, anything that plays the role of "previous setpoint"), so every feedback path closes
   through u. Find those states by reading `src/lib/indi_accel_control/`; list them in NOTES.md with file:line.
   If the structure makes a single clean break impossible, stop and write why (do not invent a second break).
3. Excitation: Schroeder multisine identical to the rate module's (reuse its generator if it is a shared function;
   if it is module-local, copy it and say so in NOTES.md). Clock = module cycle timestamp; origin = first cycle with
   AX set, armed and not landed; d = 0 outside [0, NP*Tp] and when landed. With AX = 0, d is not computed and
   exact zero is added.
4. Log c, d, u (3-vectors or the axis value, your choice, stated) in `indi_pos_status` (msg change in `msg/`), one
   sample per cycle; check the runner logs `indi_pos_status` at interval 0 (`bench/run_scenario.py` LOG_TOPICS).
5. Unit test for the injector (d = 0 when AX = 0; multisine content on the bins), checked to fail once when broken.
6. `bench/pinj_csv.py`: extract the window (t, c, d, u for the axis) from a ulog, mirroring `bench/m3a_csv.py`; and
   a margin estimate L = -G_cd/G_ud with the existing `bench/margins_est.py` functions (reuse, do not rewrite).

## Done
Code builds in Docker (`indi_project/docker/run.sh`, see how `bench/` flights build px4_sitl), unit tests pass,
`make format` clean on changed C/C++. Pre-test: ONE hover flight on `--model quad5in` with the INDI stack
(`MC_INDI_EN 1`, `MC_INDI_POS_EN 1`, `CA_R_W_MAX 2700`, z axis, amplitude small enough that |d| stays under
~1 m/s^2 peak; pick Tp/NP so the run fits a 600 s wall timeout) using a hover scenario of `bench/scenarios.py` and
the runner's `--params` file. Report: injection applied (d non-zero only in window), coherence per bin, PM/GM
estimate at the 0 dB crossing. Output dir `results/stage5_s82_velbreak/` with NOTES.md (write as you go),
metrics/csv, run.json, README.md.

## Constraints
Do not modify `mc_pos_control`, `mc_rate_control`, `mc_att_control`, `control_allocator`, the control-allocation
library or commander (O-11 zero diff). Do not touch `indi_project/`. Docker only, wall-clock timeout on every run,
at most one flight running at a time from you (the orchestrator flies other runs). Do not commit; leave the diff for
the orchestrator. Return a 10-line summary with anything unverified flagged.
