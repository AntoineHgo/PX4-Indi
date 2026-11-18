# Route check 98 (S98 start, 2026-11-18)
Read: STATE, DECISIONS (headings, D-ALTCTL-Z, tail), ANOMALIES (head), JOURNAL tail, route_check_93, GATES (G2 cell table),
gates_g3_g8_final_s94 sec 1. No source code. Nothing flown. Gates: 1 of 8 passed (G1); G2 cells measured, no verdict; G3-G8 open.

## 1) Shortest path?
No. The coverage tests (T206, mutation tests of T205) are correct-for-safety but move no gate line, and the planned
2-3 flight ALTCTL/POSCTL thrust-gap pre-test is the first item that touches G5 (F-2, D-GAP), so it is on path only as a
pre-test, not as more tests. Last gate-moving RESULT: S92 (267 Hz attitude cell, G2 evidence). S94 moved gate TEXT
(G3-G8 final, a proposal, not yet pasted into GATES.md). Since S92: 6 sessions (S93-S98) with no measurement entering a
gate table: S93 model cross-check (RC93 said stop), S95-S97 D-GAP review/fix/key rounds (T194-T205), S97 ALTCTL decision.
RC93 asked for: G2 report S94 (done, per STATE), G3-G8 text + matrix S95, yaw cell + identification slice S96-S97. Yaw
cell and identification slice did not happen; the sim hooks (delay line, GNSS delay, drop seed, IMU noise scale) are
still MISSING after 33 sessions (S65 listed them as one simulator task). RC93 deadline "no G2 verdict by S96 -> owner
narrows G2" has passed without that step being taken or recorded.

## 2) Decision behind the difficulty
D-GAP (S70; opus r1 BLOCKING, amended S71) together with the owner rule "no PID fallback, all modes" (MEMORY) and
D-ALTCTL-Z (S97). D-GAP put gap compensation into the stock outer-loop integrator path, so every added mode (ALTCTL,
DESCEND) and every stale-input path needs its own gate test, and the module has no harness, so each fix produced a
second key finding (T199 BLOCKING, T202 2 MAJOR, T205 2 MAJOR coverage). Root: safety-critical logic split between lib
(testable) and module (compile-only). Secondary: Q4-A (G2 provisional) leaves G2 without a verdict.

## 3) Fresh start on this stage
Put the stage input derivation (want_indi, z-only, integrator reset, finite checks) in the lib as one pure function with
a single table-driven test, module is a thin caller; decide the harness question first (SITL evidence instead of a module
harness for G7, since SITL flights are needed for G5 anyway). Cap key rounds at one per change set (RC74 rule extended
to coverage). Fly the gap pre-test before writing mutation tests, because flights are the gate evidence.

## 4) Next three actions (S98 remainder and S99)
1. S98: finish T206 as already launched (sonnet, ~$0.6, running); take no further coverage tasks. Decide in DECISIONS:
   module harness NOT built, G7 uses SITL evidence; module-side residues (stale-input reset gate) go into G5 flights
   as check lines. Then paste the S94 G3-G8 text into GATES.md (~$0.5, text only).
2. S98/S99: the 2-3 flight pre-test (s5_gap085 in POSCTL, new stick altctl gap scenario, MC_INDI_EN=1 MC_AT_EN=1 start
   check), run by host, metric bench/s5_gap_check.py (~$1.0 incl. scenario edit). This both validates D-ALTCTL-Z and is the
   first G5 evidence.
3. S99: build the simulator hooks in the order of design/gates_g3_g8_final_s94.md sec 1: per-run drop seed (smallest),
   then the shared sim-time delay line (IMU/actuator + GNSS), then IMU noise scale; one sonnet task + G1.5 check each
   (~$1.5-2, may spill into S100). Also record the G2 verdict state: complete the per-axis rate table and state yaw and
   model-only as "not covered", or move yaw to stage 6 (owner note).
Drop: further lib/module coverage beyond T206, tooling second keys, anomaly chases (A-4, A-6, A-30, A-32, A-34-36
stay parked).
Defer to stage 7: module-level harness, the 4th-motor frozen-b MINOR, lagging mean_u-at-reset MINOR, DESCEND failsafe
tests, position-mode sag / weak-motor sim-time player injectors, kill/re-arm/RC-loss injectors until G5 flights run.
If hooks or the G2 verdict are not done by S101, ask the owner to narrow G2 (rate+z+xy+attitude).
