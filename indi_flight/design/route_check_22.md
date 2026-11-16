# Route check 22 (sonnet, 2026-11-16, session 22)
Read: STATE, DECISIONS, ANOMALIES, GATES G1, JOURNAL tail, route_check_10. No source, no archive.

## 1. Still on the shortest path to the gates?
No. 22 sessions in, G1 has not passed one item. Route check 10 (S11) said: run determinism, finalise GATES G1, build
the first injector, one agent on 3-4 related items. Since then: determinism ran (S13-S16) but G1.6(a) FAILED and was
carried forward; G1.5 (injectors, variants) is untouched; G1.3 second keys exist for trajectory, window and A-12 only;
G1.4 self-tests missing for 7 scripts. Sessions 17-21 (5 of 6 since the last good check) went to logger/topic
plumbing (A-10..A-16) and every closure opened a new anomaly (A-12 -> A-15 -> A-16; A-14 -> pair test). G1 items done
since S11: about one (g1.1 mostly). Stages 2-7 have zero sessions. The outer-loop design absorbed S12-S15 despite
route check 05/10 saying not to.

Which anomalies BLOCK a G1 verdict (only those that can change a G1.x pass/fail or make a later gate verdict wrong):
- A-15/A-16 (truth and controller topic completeness): block G1.1 only, and only because G1.1 has a "max gap < 3
  periods" rule. The data is already 800 Hz complete via `sim_ground_truth`. Close = switch g1.1/metrics to it (one
  sonnet task, already planned). A-16 is timestamp jitter by the log of S21 (counts ~ gyro count): bound it, do not hunt.
- A-13 (gyro gaps 7.5-10 ms): matters for G2 injection, not G1. PARK with a written bound (count, max gap per run).
- A-10 (esc_status 1.7 % lost): PARK; bounded, analyses resample by stamp. Re-open only when G2 reads rotor speed.
- A-14 (EKF height offset in first ~8 s after arm, intermittent, only without boot logging): does NOT block G1. Truth
  (not EKF) is the tracking reference (G1.2) and analysis windows are anchored after take-off. PARK with the rule:
  take-off/transient metrics use truth; the runner logs from boot (`--log-from-start`) as default, which removes the
  fault in 0/9 vs 3/6. Reopen if EKF-height-dependent behaviour (altitude hold, landing, G5) fails on a fresh seed.
  Do not spend another session on root cause. It is a SITL-start artefact until shown to occur with boot logging.
- A-12 closed. A-1..A-6, A-9: not G1 (stage 2/3/5 closing tests); A-2/A-7 are covered by G1.6.
BLOCKING G1 for real: G1.6(a) (mode instants 7.5-11 ms vs 2.5 ms limit, no gz lockstep), G1.5 (nothing built), G1.3
(metrics without second key), G1.4 (7 scripts without self-test), GATES G1 final commit. G1.6(a) is a gate-definition
question as much as a simulator one: either implement the remedy (scheduled in-PX4 mode switch) or change (a) to what
(c)/(d) already deliver, with a logged reason (allowed: "fix a defect in the test"; the cause is known and stated).

## 2. Which decision is the difficulty a consequence of?
Two, same family as route check 10. (i) F-4 fresh start plus the G1 wording "every metric two independent scripts,
every script self-tested, every topic at declared rate with no gap": a strict completeness rule over a free-running
gz/PX4 pair makes every plumbing artefact a gate failure. (ii) D-SIM-STEP (800 Hz world, IMU 800 Hz, S15): it pushed
the logger to 800 Hz, created the logger overwrite (A-10/A-15/A-16, A-13) and invalidated the 4 ms G1.6 set, so S16-S21
re-did determinism work. It was needed for G2 (400/800 Hz) but was taken in stage 1 before any G1 item passed.
Secondary: no lockstep (D-G1.6 accepted gz free-running) is the root of G1.6(a) and A-7.

## 3. A fresh start on this stage would
- Treat G1 as a bounded evidence contract: each topic gets "complete or bound written", not "zero gaps"; gaps below a
  stated fraction (e.g. 2 % of samples, no gap > 5 ms) are bounds, listed once in GATES, not anomalies.
- Decide lockstep (or scheduled in-PX4 mode switch) in S3, before determinism flights; then G1.6(a) is cheap.
- Run the 800 Hz world and logging profile once, in one session, with a full g1.1 check, before porting more scripts.
- Cap anomaly depth: an anomaly gets at most 2 sessions, then PARKED with bound + reopen trigger in ANOMALIES.
- Start stage 2 (linear margins, CPU only, no sim) in parallel from S4; it does not depend on G1.

## 4. Next five work items (one session each, ~$1.5)
1. Close A-15/A-16 for the gate: g1.1 and metrics.py read `sim_ground_truth` (sonnet) + haiku second key + A-16
   bound (timestamp vs timestamp_sample, one table). PARK A-10, A-13, A-14 with written reasons in ANOMALIES (orchestrator,
   5 calls). Make `--log-from-start` the runner default. Re-run g1.1 once: pass or write the bound.
2. G1.6(a) decision and fix: sonnet reads the runner path for mode switching; choose (a) in-PX4 scheduled switch at a
   sim time, or (b) restate (a) as "anchor window on the logged mode change" per (c)/(d) with D-entry. Prefer (a) only
   if <= 1 session; else (b). Then re-flight the 5-run speed-4 set (host bash, $0) and fill G1.6 spreads.
3. G1.3/G1.4 batch: second keys for effort, hover, settling, spectral metrics (one sonnet, 4 metrics together) plus
   self-tests of the 7 scripts (second sonnet next session if cut). Haiku re-runs the second keys.
4. G1.5 injectors, minimum set: payload/mass step and param step with logged applied time, sim-time (one injector
   family per session). Defer sag, GNSS delay, vibration until the gate that uses them (G2/G3) is being run.
5. Freeze GATES G1 (final), commit, write G1 verdict with the PARKED anomaly list as evidence limits. Same session:
   start stage 2 plan (item below).

Minimal G1 scope before stages 2/3 start in parallel: stage 2 (linear margins) needs no simulator and can start NOW,
in parallel, CPU only. Stage 3 (inner-loop code) needs only: item 1 (usable truth topic + g1.1 pass or bound), item 2
(determinism bound known: any verdict must exceed same-seed spread, rule d is already in force), and the metrics
with second keys for rate tracking and effort (part of 3). It does NOT need G1.5 sag/GNSS injectors nor the A-13/A-14
fixes. G2/G3 verdicts do need G1.5 (injectors) and G1 final. So: 1, 2 and the rate/effort part of 3 are the gate to
parallel work; items 4-5 can run alongside stage 2/3.

## Bluntness
Stop reading logs for causes of intermittent artefacts that do not change a verdict. Five sessions of plumbing
returned zero gate items; the next session that opens a new anomaly instead of closing one with a bound should be
cut. Do not touch outer-loop design (stage 5) before G1 is final.
