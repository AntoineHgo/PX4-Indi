# Route check 241 (2026-11-26, orchestrator short form, session cap $1.15: no RC agent)

Trigger: GATE_STATUS.tsv unchanged for 4 sessions (supervisor).

1. Shortest path? Yes, if narrowed. The only open verdict reachable now is G3 on route B (GATES "Owner amendment
   S225"), the last route of Q32. The chain halted (fail-fast) at run 003 with two failing runs (002 item 4, 003
   item 2), both keys.
2. Decision behind the difficulty: D-RATE-BLD-2 / FREEZE-10 rate-loop gap remover (decision 2) under slow motors
   (tau x2.4-2.8): same 2 Hz pitch signature as S199 draw 245. Item 4 on 002 (heavy plant + 8.4 m/s gust) may be
   shared with PID (PID failed item 4 on draw 0 too, Q34 context).
3. Fresh start would: fly the PID reference of each failing draw before anything else (owner rule), then declare.
4. Blocker of the next verdict: PID reference of draws 2 and 3 + one INDI re-fly of draw 3 (task D2).
5. Gate items moved since RC239: G3 route B runs 0-3 scored, halt diagnosed (S240). No GATE_STATUS row change.
6. Cut: g3_chain.sh failing-list display fix and exclusion self-test (tooling, verdicts already right); all G6/G7/G8
   work stays cut until the G3 route B outcome. Acted on in STATE.
