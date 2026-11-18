# Route check 113 (S113, before the next G3 fix session)
Inputs: STATE.md, RC108, JOURNAL S109-S112, results/g3_pretest_s112/README.md, GATES.md G3/G5 text, D-G3-SAMPLER, D-GATES-G3G8.

## 1. Still on the shortest path? Hook-building loop?
Partly yes, partly a loop. RC108 said G3/G5 batches before the stage-6 freeze are PROBES. Since then four sessions (S109-S112)
produced sampler, driver, overrides, two keys and a pre-test, and the cumulative flown G3 evidence about the controller is
three flights, two of them lemniscate. That is a loop in the sense RC108 warned about: each session closes the previous key's
findings and the next pre-test finds new set-up faults (wind pose class, inertia triangle, eRPM timing, abort metrics). The
cause is that every hook is validated by a new multi-hook flight instead of one flight per hook, and the sampler drew the
corner (stress slot idx 18, mass x1.3 plus weak motor plus saturation) in the first test.
It is still on the path (G3 needs a randomised runner), but only if S113-S114 end it. The fixes are real defects (inertia
violating the triangle inequality is a 1/3 sampler bug), so they are not wasted. Hooks with no consumer is on the STOP list;
the not-yet-checked items (--sched-anchor, set_param between sub-runs, weak+sat) are not emitted by any draw and should be
dropped from scope rather than built.

## 2. Which decision is the difficulty a consequence of?
D-GATES-G3G8 (S94) fixed G3 as a 300-run randomised campaign with all axes drawn together (wind drawn in every run,
independent per-axis inertia, corners C1-C5), and D-G3-SAMPLER (S108) chose independent uniform per-axis inertia and wind in
every run. Together they make every run a multi-factor draw, so any failure is un-attributable and every hook must be right
before the first flight gives information. Secondary: D-G7-HARNESS deferral meant no per-hook harness existed.

## 3. Fresh start on this stage
One factor at a time first: a fixed list of about 8 single-factor runs (mass x1.3, inertia x1.3 isotropic, sag 0.7, wind 5,
one eRPM loss, one weak motor), each on one scenario, each flown once, before any random campaign. Sample inertia as a
physically valid tensor (scale the principal moments with a shared factor plus a bounded anisotropy that preserves the
triangle inequality). Draw plans must be independent of n (K: campaign(seed, n) draws depend on n, S112 set-up note 2). Let the
runner accept a start/stop index. Randomised mixing comes only after every single-factor run is clean.

## 4. stick_zsine_o6 with mass x1.3: finding or set-up fault?
Do not classify it as a set-up fault yet, and do not classify it as a result yet. Facts: seeds 8 and 14 (both mass 1.3, valid
inertia, no gz error) lost altitude 5 m to 3.7 m in 1 s with u falling 0.173 to 0.11, before the settle/stick segment at
55.5 s and before any hook; the control (mass 1.04) flew. Falling thrust command while descending is the wrong sign for a
working z loop at heavy mass, so candidates are: (a) controller: thrust model or hover-thrust estimate (MPC_THR_HOVER or
the INDI thrust scale) wrong by 30 % mass, the outer loop reading the sag/ramp as above-target, or an altitude-mode z-only
INDI stage (D-ALTCTL-Z) integrating wrongly; (b) set-up: mass applied in the sim without the matching inertia/thrust
mapping, a sag ramp started in the draw, or the stick scenario starting a z profile earlier than assumed. Also the same draw
had a weak motor and saturation in the planned corner; the README says those seeds had weak motor and saturation drawn, so
(c) saturation applied from t0 (not at a hook time) is a third candidate and is the cheapest explanation: available thrust
2.0 x hover of the drawn mass applies before any timed hook.
Classification: "G3 probe, UNATTRIBUTED, blocks the stick scenario at mass 1.3" in ANOMALIES.md until the test below runs.
Single discriminating test: scenario stick_zsine_o6, mass x1.3 only (override mass, nominal inertia, no wind, no sag, no
saturation, no motor fault, no eRPM loss), one flight at speed 1, same seed as seed14/18, 60 s. Read: descent reproduces
means controller/thrust-model finding (then repeat once at mass x1.15 to see if linear, and compare lemniscate at 1.3);
no descent means one of the removed factors (most likely saturation from t0) is the cause and it is a sampler/hook issue.

## 5. Recommendations S113-S117
1. S113: fix the three real sampler/runner defects in one session (valid inertia tensor; draw independent of n and a start
   index in g3_run.py; aborted-run metrics), one key at most (second key only if code changed in a safety path), and fly the
   single test of section 4 in the same session. Drop the --sched-anchor and set_param-latency checks.
2. S114-S115: single-factor ladder (about 8 runs, one flight each, order: mass 1.3, inertia isotropic 1.3, sag 0.7, wind 5,
   eRPM loss, weak motor, saturation, GNSS mismatch) on stick_zsine_o6 and o1_lemniscate. Record each as a probe result. Any
   controller finding becomes an ANOMALIES row with a closing test, not a hook task.
3. S116-S117: first mixed G3 probe batch of at least 60 runs on the cleaned runner (as RC108 planned S110), then G5 mode
   batch. Report failure counts by factor; no gate evidence before the stage-6 freeze.
Stop rule: if after S115 any single-factor run still fails for a set-up reason, or if S116 needs a new hook before the first
60-run batch, stop building hooks, declare the remaining axes unprobed in GATES.md, and fly the batch with the factors that
work. No session after S113 may add a hook without a flown consumer in the same session. Next route check: S118.
