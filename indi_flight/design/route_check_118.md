# Route check 118 (S118, before D-G3-STICK-PILOT)
Inputs: STATE.md, RC113, DECISIONS.md:601-617 (D-G3-STICK-FACTORS, D-G3-STICK-PILOT), GATES.md G3/G5/G6, ANOMALIES.md, JOURNAL S113-S117.

## 1. Still on the shortest path?
Partly. RC113's stop rule worked: S116 ladder (e97d826b27, a7ac9375c0) and the S117 probe (bacee6eb8d) gave real signal:
position 45/45 ok, and every stick failure traced to the scenario, not the controller (PID controls fail identically).
Now the loop risk has moved to stick scenarios. G3 stick/acro coverage costs a pilot model plus self-test plus key (~1.5
sessions) to defend a failure class that is not a controller finding.
- Time-box D-G3-STICK-PILOT: 1 session, altitude PI on throttle in stabilized only. Acro levelling only if it falls out
  in the same session. If acro idx 0 still fails with PI+levelling on both INDI and PID, declare acro G3-unprobed and
  let G5 carry acro (D-G3-STICK-PILOT lists this alternative, DECISIONS.md:615).
- Drop for now: frozen-telemetry hook (no flown consumer; RC113 hook stop rule), G4 noise profiles, g3_checks.py and
  gate_g3.sh. All score a G3 whose sampler/definitions are still "tested and frozen" in the pre-test (GATES.md:251),
  and gate_g3.sh cannot be run as evidence before the stage-6 freeze anyway.
- Premature? Yes. G6 (GATES.md:373-383) needs G2/G3/G5 to pass from x2/x0.5 starts with identified parameters, so the
  G3 scoring script is needed only after stage 4 identification and defaults exist. Building it against hand-set
  parameters tests code that G6 will re-run with different inputs. A thin probe summariser (outcome counts by mode and
  corner, which P117 already has) is enough until then.
- Reorder: stage 4 (identification chain, defaults file, G4 minimal) and a base-A outer loop for every mode (G5 build)
  are the long poles and currently have zero flown evidence. STATE says "G5 build order (draft end)" is still "Later".
- Open item that blocks G3 o1 limits and G5: which outer loop `--controller indi` uses on o1 is UNVERIFIED (STATE.md
  stage 5 note). Cheap, check first.

## 2. Which decision is the difficulty a consequence of?
D-GATES-G3G8 (S94): G3 is a 300-run randomised campaign over every mode and scenario including manual-stick modes, so
open-loop pilot scenarios must be made valid before the first batch. Secondary: D-G3-STICK-FACTORS (981e94f79e)
patched this by dropping factors per mode, and D-G3-STICK-PILOT is the next patch on the same root. Compounding cause:
G3 and G5 both specify stick modes but no outer loop exists for altctl/posctl stick use, so the stick scenarios have
no closed-loop altitude (D-ALTCTL-Z, DECISIONS.md:550, covers only altctl climb rate).

## 3. Fresh start on this stage
Build stages in gate order: stage 4 defaults and identification first, then G5 modes (which gives altctl/posctl
closed-loop altitude), then G3 over position, altctl and posctl, where the pilot is the mode's own outer loop. Stabilized
and acro enter G3 only as short attitude-recovery scenarios (stick step then release, assert recovery to a level
attitude), which need no pilot model and have a clear pass criterion. No sampler or hook work before the identified
default file exists, because G6 re-runs G3 on it.

## 4. Recommendations (ordered, cost at ~$3 per session)
1. S118 (1 session, ~$3): D-G3-STICK-PILOT time-boxed as above, stabilized PI first, one re-fly of acro idx 0 for INDI+PID,
   one key. Same session: verify which outer loop `--controller indi` runs on o1 (grep, no flight, ~$0.2). Then
   freeze G3 stick probing; record unprobed axes in GATES.md.
2. S119-S121 (3 sessions, ~$9): stage 4: identification chain run from wrong starts on the hover/step data, defaults
   file, minimal G4 noise profile just enough for identification. Gives the first G6 evidence early (fail fast).
3. S122-S125 (4 sessions, ~$12): G5 build in the order of the draft (every mode base A), 3-seed rows as probes. Only
   afterwards, ~1-2 sessions (~$5): g3_checks.py, gate_g3.sh, frozen-telemetry hook, 300-run campaign on the frozen defaults.
Next route check: S122 (after stage 4 first G6 start).
