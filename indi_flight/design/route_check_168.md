# Route check 168 (written for S168)

Read: STATE.md, ANOMALIES.md (open rows), GATES headings + G3 (265-322) + G4 (323-364), JOURNAL tail, route_check_163.md,
DECISIONS D-NOISE-PROF / D-FREEZE-6 headers. Not read: result READMEs, the S168 flight/key2 outputs (in flight).

## 1. Still on the shortest path?
Yes, but narrowly. G4 is the next gate in the agreed order (G2 -> G4 -> G3) and R20/R4 are defined on true rotor speed
(GATES G4), so the hook is required, not optional. Cost so far is 2 sessions (S166 metric, S167 hook). It stays on path
only if S168 closes it: one flight, key2 of the hook, then the 27-run pre-test. Do not extend the hook (no more signals).

## 2. Decision behind the difficulty
D-FREEZE-6 / D-DEFAULTS-FW: INDI flies the eRPM telemetry model (SIM_GZ_ESC_FB=2), the only model in which the gate's
"true rotor speed" is not logged. The gate text (G4 metrics) was written before that choice was tied to the logger.
Not a design error; a gate-text/sim-truth gap found late (S166) because the pre-look used a proxy.

## 3. Fresh start on this stage
Same freeze. Differences: check at the G4 metric-writing step that each gate signal exists in the log under the flown
ESC model, before writing the metric script (one 5-min flight would have shown the gap); write the G3 checker and the
G4 runner together with the freeze, since both are needed by gates and neither depends on results.

## 4. Re-open?
No decision. Optional owner note: if true rpm cannot be verified cheaply, G4 R20 could be stated on telemetry rpm with
the truth check as a reported cross-check; do not re-open unless S168a fails twice.

## 5. Gate items moved since RC163
- G2: outer cells keyed (S164, 22/24 within 3 deg/1 dB), plateau rule over 67/67 cells (66 literal, 1 -> Q13), outer and
  rate/yaw model x-check done (A-50, A-51 bounded), 267 Hz reported cells flown (S165). G2 closed except Q13 and 267 Hz keys.
- G4: metric script written (self-test + break-check, UNKEYED), pre-look proxy R20 0.09 %, C20 0.0015, clip 0 (typical,
  hover; a pre-look only, not gate evidence); truth hook committed, UNVERIFIED.
- G3, G5, G6-G8: unchanged. No new G5 chase (good).

## 6. Drop or simplify (no threshold weakened)
1. G4: verify hook with the single hover flight, then skip a separate key2-of-hook brief if the flight shows instance 1
   differs from instance 0 and tracks commanded-rpm shape; keep key2 of g4_metrics.py (gate requires second key). [G4 R20/R4]
2. G4: fly the 27 runs serially as one chain script; no per-profile sessions; tabulate with g4_metrics.py only. [G4 all]
3. G4 cruise row at the stated 1.5x limit only once per profile (seeds still 3); acro row only if the stick model is
   already in the runner, else mark it as pending Q to owner, do not build quantisation now. [G4 acro]
4. G3 minimum to start the 20-run pre-test: (a) bench/g3_checks.py with items 1, 2, 3, 6 (LOC, oscillation, steady
   state, rate RMS) and items 4/5 as simple window metrics from metrics.py; (b) a 15-line chain script (the gate_g3.sh
   `pretest` branch only) looping g3_sample.py -> g3_run.py -> g3_checks.py; (c) the frozen-telemetry hook, because the
   pre-test must fly every injector at its extreme (G1.5), a 20 % factor. Verify whether added-delay and GNSS-latency hooks
   (marked MISSING in the table) exist; if not, they are also required for the pre-test.
5. G3 defer until after the pre-test: `gate_g3.sh campaign` wrapper, second key of g3_checks.py (needed before the
   campaign counts, not before the pre-test), PID on 60 seeds (reported only), per-factor sensitivity tables. [G3 reported rows]
6. Drop the G4 profile "harsh" vibration beyond the three D-NOISE-PROF values: no new profile search. [G4]
7. STATE: remove the S166/S167 detail once S168 results exist; the deferred line lists items already scheduled. [housekeeping]

## Next 3 sessions
- S168: hover flight FB=2, instance 1 check, key2 of g4_metrics.py on instance 1; format hook code; launch G4 27-run chain.
- S169: G4 results scored + keyed; write g3_checks.py and pretest chain, frozen-telemetry hook.
- S170: G3 20-run pre-test; freeze sampler/checks; then campaign launch (~2.1 h wall, one host slot).
