# Route check 221 (S221, 2026-11-24, supervisor trigger: GATE_STATUS.tsv unchanged 3 sessions)

Written by the orchestrator, not an agent: RC220 (design/route_check_220.md) is one session old and its answers
stand; this note only adds the cut the supervisor asks for.

1. Why GATE_STATUS did not move. S218-S220 executed the owner's Q31 route step B (factor restorations on draw 264).
   These are diagnostic probes; by design they produce no scored gate evidence. The result (INDI-specific LOC on
   saturation 0.351 + weak motor 0.709 only, PID survives) is the input of the next step.
2. What blocks the next gate verdict.
   - G3 (NOT PASSED): the re-fly campaign cannot pass while draw 264 is a reproducible INDI LOC. Next step is the
     owner's pre-approved escalation (2 investigators, then solver + reviewer, then owner question). Q30 tooling
     precedes the re-fly.
   - G6: item 7 chain must fly on the final firmware; a Q31 fix would invalidate it.
   - G7: (f) unit 9, (g), harness, dead path depend on whether firmware changes (RC208 cut).
   - G8: report chapters 3 (G3, G6) depend on the above; other drafting can continue.
3. Cut (written in STATE.md): G6 item 7 chain deferred until the Q31 route ends; saturation sweep only on an
   investigator's request; RC208 G7 cuts stand. Nothing else runs besides the escalation and G8 text.
4. Shortest path: run the escalation now; if the solver cannot remove the LOC in one fix probe, write the owner
   question in the same session rather than iterate (freeze discipline, one-session cause bound already used).
