# Route check 93 (S93 end / S94 start, 2026-11-18)
Read: STATE, GATES (headers, G2 head), DECISIONS (headers), ANOMALIES (A-34..A-36), JOURNAL tail, route_check_89. Nothing flown.
Gates: 1 of 8 passed (G1). G2 open after 93 sessions; G3-G8 text still "NOT final" (S64, ~30 sessions old).

## 1) Shortest path?
Mostly no, only the last step. Attitude cells (S91/S92: roll 800/400/267 Hz, PM 56.6, GM 22) are real G2 evidence and done as RC89
asked. The S93 linear-model cross-check is not a gate item: PM already matched within 0.3 deg after T194/T195, and the GM residue
(A-36, 1.6-4.6 dB, model conservative) is the same parked family as A-34/A-35. It cost a session and two sub-agent keys and
changes no gate line. RC89 asked for the G2 report at S91; it is now two sessions late, and the runner is still unnamed in GATES.md.
G2 still lacks yaw, model-only/PID split and the report.

## 2) Decision behind the difficulty
Decision 3's cousin: Q4-A (G2 provisional until the stage-6 freeze) plus D-G2-BREAK/D-G2-PINJ (one injector and break per loop).
Every loop needs its own break, tool and independent model, so each cell spawns a model check and a key. The drift to model
refinement follows from "no PID fallback" needing a PID reference (model_vs_measured.md) to show INDI is not worse.

## 3) Fresh start
Fix G3-G8 text and the flight matrix first; name one runner and one config table; generate the G2 report from it; accept a
model as "conservative, bounded" without explaining every dB; do yaw once; start the identification procedure (Stage 3/4,
decision 3) in parallel since G6 depends on it and nothing exists yet.

## 4) Next three actions
1. S94: G2 report section from existing cells (rate, z, xy, attitude, A-36 caveat, "not covered": yaw, model-only). Name the
   runner in GATES.md. ~1 session (cap >= $1.5).
2. S95: finalize G3-G8/G5 text and the flight matrix (campaign design, 300 runs, mode/transition list); opus combined review
   launched first. ~1-2 sessions.
3. S96-S97: yaw G2 cell plus the first identification-procedure slice (G6 critical path). ~2 sessions.
Stop: further model-vs-measured work (A-36 stays parked, RC74 rule), tooling second keys, cosmetic re-flies, new NEXT lists.
If G2 has no verdict by S96, owner narrows G2 to rate+z+xy+attitude and moves yaw to stage 6.
