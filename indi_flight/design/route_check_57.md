# Route check 57 (sonnet, 2026-11-17, session 57)
Read: MISSION (Gates, Order of work), STATE, DECISIONS (headings, overturn lines), ANOMALIES, JOURNAL tail (S49-S56), route_check_53. No source read, nothing flown.

## a) Still on the shortest path?
Partly, and the margin is drifting off it. Evidence: after 57 sessions 0 of 8 gates are passed (STATE Status); stage 5 (outer
loop, every mode, the largest work) has no code; stages 4, 6, 7 are open. Since route check 53 (S53) four sessions went to
roll/pitch/yaw rate-loop margins, mostly yaw: A-27 -> D-YAW-INV note, model (UNKEYED then keyed), opus review ($0.7), code,
second key, two M3a flights, an HF read (STATE S54-S56). That was a real defect (yaw law extrapolated t_f, a dt-dependent
gain), so it was on path once. The current sub-items are not:
- 267/250 Hz roll flight: "reported only" in MISSION G2, and S56 flew an invalid set (TP 10 not integer samples), now a second
  re-fly (B-S57a). A reported-only rate buys no pass condition. DEFER.
- Measured-rotor path at every rate, and a full table at every rate and axis: G2 is validated on the frozen final pair in
  stage 6 (MISSION "Stage 6"). Any rate-loop number measured now is void if stage 5 or stage 4 changes the rate loop (it has
  twice: A-23/G1 derive, D-YAW-INV). Finishing the table now is polish; one representative (roll 800 + 400, yaw 800, done)
  is enough to protect the design.
- Stage-3 items note opus review ($1.1): items 1-3 were already parked in S53. Keep parked.
- Hole reporter (G1 evidence limit 1): only needed at the --gate batch.
Time that moves no gate: the 267 Hz re-fly, GM reads at bins beyond the band, A-24/A-26-type residue, repeated 2-seed
confirmations of values already inside G2 with 6-40 dB to spare (yaw PM 88, roll PM 84), notes reviewed ahead of code.
On path and not started: attitude/velocity/position break notes (route check 53 rec. 3, still NOT done, 4 sessions later),
which are also the part of G2 that depends on stage 5 and that no later stage can skip.

## b) Which decision is the difficulty a consequence of?
D-RATE-LEAD (S48) plus D-YAW-INV (S54): the rate law keeps the stock cascade (MC_ROLL_P 8, K_R ~ 0.7 x motor bandwidth) and
repairs margin inside the INDI law with an identified-tau-dependent lead and a G2-dependent yaw inversion. Each repair adds a
parameter whose tolerance must be measured (ACT_TC one-sided [x1, x2], G2_Y x0.5-2, lead on yaw x105). Under it: decisions 3/4
(derive every physical parameter) landed after stage 2 began (route checks 45, 49). Process cause: the margin table is being
measured as each law revision lands (revisions: S44, S47, S52, S56), so every number so far has been superseded or is
provisional under Q4-A. Gate-style evidence taken before the law is frozen is re-bought each time.

## c) Fresh start on stage 3
- Derive G1, G2_Y, tau_c from the airframe first (D-G1-DERIVE, D-G2Y-DERIVE, S52 ACT_TC data) and write the law once,
  with the actuator lag and the yaw spin-up consistent in the inversion (D-YAW-INV from day one), not as a later fix.
- Test in a host-side linear model + parametrised closed-loop unit plant (MISSION stage 3 text) and fly one roll and one yaw
  M3a as sanity checks; no per-rate flown table until frozen.
- Write all loop break notes (rate, attitude, velocity, position) together with stage 5's architecture, because the outer
  loop shapes the inner break set (S41 lesson: model must contain every loop the break closes around).
- Land the stage-3 safety items (landed trim, start-up, timeout, frozen telemetry; MISSION stage 3 list) as code with unit
  tests, reviewed once at the diff; these gate G5 and G7, the margins do not.

## d) Recommendations (each ~ one $3 session)
1. S58, stop the rate-loop table: record roll 800/400 and yaw 800 as the G2 rate-loop evidence for now, drop the 267 Hz re-fly
   and measured-rotor path to stage 6 (note in GATES.md G2 and STATE). Use the session to write the attitude, velocity and
   position break notes (host, sonnet, ~$0.7) plus haiku second key; the linear models extended with MPC gains (A-26 closing
   test). Closes: route check 53 rec. 3, A-26, GATES G2 loops list, first draft of stage 5 interfaces.
2. S59, stage-3 safety package: code items 1, 2, 4-5 of `design/stage3_items_note.md` (landed trim, start-up exclusion,
   setpoint timeout, frozen telemetry; item 3 thrust decay dropped) with unit tests and break-checks, opus review of the DIFF
   once (~$1.1). Closes: MISSION stage 3 item list, parts of G5 and G7, the unreviewed-note debt.
3. S60, start stage 5 code: smallest end-to-end slice, the architecture-A position/velocity/acceleration loop in hover
   (D-outer-arch, `design/flatness_r2.md` increment deferred) with the thrust-gap test from stage 2 (hover thrust scale 0.85,
   predicted 0.37 m) as the first flight, then A-6 signal substitution. Closes: the stage-5 start, the thrust-gap item, a
   real G3/G5 path; every later stage-3 change then retests against a real outer loop.

## Verdict on "finish the G2 table at every rate now vs stage 6"
Defer. G2 is a pass test on the frozen pair; margins re-measured at every law change are discarded. Keep one flown anchor per
axis plus the validated model for the rest, flag 267/250 Hz and measured-rotor as stage-6 items in GATES.md.
