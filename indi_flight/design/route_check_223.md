# Route check 223 (2026-11-24, supervisor trigger: GATE_STATUS unchanged 5 sessions)

Short check by the orchestrator; RC221 (independent, two sessions ago) is still current, so no new agent was paid
for (budget goes to the blocker).

1. Shortest path? Yes, if work stays on G3 item 1. G1/G2/G4/G5 PASSED, G3 NOT PASSED (draw 264 LOC), G6/G7/G8 wait
   on whether G3 forces a firmware change.
2. Decision behind the difficulty: decision 2 for the rate loop (D-RATE-BLD, blend tb 1.0 s). Investigators A/B and
   falsifier probes S222 show the LOC is missing integral action against a weak-motor trim that grows with
   collective; tb 0.15 s or model-only remove LOC.
3. Fresh start would: treat the blend time constant as the first fix candidate (a parameter, no new code, F-9), and
   only build a per-motor command-map correction if tb alone cannot pass LOC and item 2 with margin.
4. Blocker of the next verdict: a decision-2 fix that removes LOC on joint and draw 264 without an INDI-only item 2
   failure. Open sub-question: the item 2 (2 Hz) detections on joint start at 21-29 s, before the fault, and PID
   key 1 shows them too: they may belong to the scenario, not to the fix.
5. Gate items moved since RC221: none in GATE_STATUS; G3 item 1 cause shown on logs (S221-S222).
6. Cut: G6 item 7 chain, all G7 clean-up, G8 drafting until the fix is decided (STATE "CUT"). Acted on.
