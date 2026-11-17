# Route check 69 (sonnet, S69 start, 2026-11-18)
Read: STATE, DECISIONS (headings, D-G1.6, D-SIM-STEP), ANOMALIES, JOURNAL tail 40, route_check_64, GATES headings. No code or results read, nothing flown.

## 1) Still on the shortest path to G1-G8?
No. 0/8 gates passed after 68 sessions. Route check 64 ranked: S65 stage-5 slice 2 (thrust-gap hover, one velocity/accel mode),
S66 bench fix + first outer-loop disturbance flights + combined review. Reality S65-S68: hooks check, bench coding, A-31 (a real
2x wrench bug, worth fixing), then A-30 -> A-32 determinism chase for three sessions. Slice 2 was NEXT (1) in S65, S66, S67, S68
and still has not started. Stage 5 holds every remaining mode and has had no flight since S60 (9 sessions).
NOT on the path:
- A-32 bisect over 71c194ff26..HEAD, and the S69 host-CPU-load test of it. A-32 itself says spread is below 1/2 of the gate margin
  (rise 11.5 ms, worst settle 368 vs limit 450); D-G1.6 defines determinism as a bounded absolute spread against gate thresholds,
  not bit-exactness. A bounded 10 ms spread blocks no gate.
- A-30 (same-seed outlier) and A-4 (speed 1 vs 4): useful hygiene, no gate needs them before stage 5 has anything to measure.
- A-9, A-1, A-3, A-7 triage, errata, same-seed spread on PID / v2 / eRPM-lost variants (T147-T150): all inner-loop or bench hygiene.
- Third and fourth G2-STEP re-flies (S64 400 Hz, S68 clean-HEAD): the gate already passes 9/9 with margin.
On path: slice 2, G3-G8 first tests, the combined stage-3 + stage-5 review.

## 2) Which decision is the difficulty a consequence of?
D-G1.6 (S13) with D-SCHED (S23) and D-SIM-STEP (S15): determinism was accepted as "bounded spread", not lockstep, on a free-running
gz + wall-clock PX4 pair at speed 4, 800 Hz physics. That leaves a spread floor that moves with host load, build and scheduling,
so every re-measure can "regress" it (A-7 parked, A-17, A-30, A-32 are one family). The gate text is fine; the failure is
treating a spread number moving 0.8 -> 11.5 ms as a defect instead of checking it against the D-G1.6 threshold first. Second layer:
D-S5-SLICE deferring the thrust-gap/mode work (same as route check 64), so nothing pulls sessions toward stage 5.

## 3) What a fresh start on this stage would do differently
- Fix the spread budget once: put a per-gate "spread allowance" in GATES.md (e.g. 1/2 margin) and treat any measurement under it as
  noise; open an anomaly only when it is crossed.
- Run the determinism check as a standing CI-style script on a quiet host (one command, 5 runs, exit code), not as a research thread.
- Build stage 5 modes thin and early (position, velocity, acceleration, acro, offboard) and only then polish inner loop.
- Cap anomaly chases: 1 session per anomaly, then park with a bound. Route check 64 said this for the inner loop; it was applied to
  nothing else.

## Recommendations (next 3 sessions, in order)
1. S69 (today): finish the host-load test as one bounded run (<= 1 hour). If parallel load explains it, write the quiet-host
   rule in GATES.md G1.6 and park A-32 with that bound; if not, still park it with the 1/2-margin bound and open the bisect only
   as a background task that never blocks a session. Unblocks: every other task, by closing the determinism thread.
2. S70: stage-5 slice 2: thrust-gap hover (MC_INDI_W_MAX 2700) + one velocity/acceleration mode, T123 deviations, haiku second key,
   flown with the A-31-fixed disturbance profiles. Unblocks: G5 evidence, A-6 ablation, the first outer-loop disturbance result.
3. S71: second mode slice (position stick, then acro/offboard stream 2 vs 10 Hz) plus the combined sonnet review of the stage-3
   safety diff and stage-5 slices. Unblocks: first G3-G8 tests running against the written text and the freeze path for stage 3.
Rule: no new anomaly work in S70-S71 unless a gate test fails.
