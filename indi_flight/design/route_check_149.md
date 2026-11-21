# Route check 149 (written for S149)

Read: STATE.md, ANOMALIES.md (no open G5 entry; A-48 closed, A18 not listed), route_check_143.md, JOURNAL tail 5,
GATES 5b, DECISIONS D-outer-arch, D-F7-GROUND, D-A18-SOURCE. Not read: result READMEs (taken from STATE).

## 1. Still on the shortest path?
Mostly yes since RC143: the lag chase stopped as told, and S144-S148 built and keyed the injector and scored
G5.8/G5.9/G5.10. But S148 spent a session on A-48 (injector artefact) and the G5.10 number got worse (2.15 -> 2.7 m)
for a reason not yet known. Four failing items remain and three of them (G5.9a, G5.8 3 m/s, G5.10 text Q9) wait on
owner answers, not on code. The shortest path is to stop designing and get Q8/Q9 answered while fixing only G5.10.

## 2. Which decision is the difficulty a consequence of?
- G5.5 o1/o2: D-outer-arch base A (stock PositionControl produces a_c; A18 FF cannot fix it, drag probe rejected).
- G5.10 alt loss: D-F7-GROUND/D-outer-arch too: the INDI stage sits behind the stock z loop and stock thrust
  limiting; saturation handling is "stock setpoint chain + INDI increment", no explicit saturation law.
- G5.9a / G5.8 3 m/s: not a design decision; gate text vs stock commander and a metric undefined at 3 m/s (Q8).

## 3. Fresh start on this stage
Same base A, but (a) write the sim set-up check (GNSS delay, atomic fault injection, injector keying) before any gate
probe: three sessions (S139-S143 GNSS, S148 per-motor sets) went to set-up faults; (b) write each gate row with a
physics-achievable limit (alt loss from thrust deficit x time, 20 deg tilt) and have the owner approve it first;
(c) test PID baseline alongside INDI per row so unreachable limits show at once (PID alt 3.22 m, abort >3 m).

## 5. Gate items moved since RC143
G5.8 hover PASS 3/3; G5.8 3 m/s entry PASS, excursion FAIL by definition (Q8 add. 3); G5.9 b/c/d PASS 3/3;
G5.9a FAIL 3/3 (3.75-10 ms stock commander, Q8 add. 2); G5.10 probed: alt 2.15 (S147, injector artefact) -> 2.67-2.74 m
(S148, atomic) FAIL, tilt 45.3 deg = MPC_TILTMAX_AIR no LOC, back 3.3-3.5 s PASS; injector keyed S144. Unchanged:
G5.1-G5.4, G5.7 (probe PASS), G5.5 (o1-o4/o7 FAIL, o5/o6/offb PASS), G5.6/G5.11 (Q8 gaps). G2-G4, G6-G8 unchanged.

## 6. Drop or simplify (ranked)
1. Drop PID comparison runs for G5.10 beyond the one aborted number already held (PID abort >3 m is enough).
2. Drop G5.8 3 m/s 3-seed flying until Q8 add. 3 (i) is answered; do not define the metric ourselves.
3. Drop the runner trap fix and MC_INDI_EN alias work; just note --controller pid_default caveat in the README.
4. Drop STATE items 0b/0c prose (history is in JOURNAL) to free room; keep one line per gate row.

## Recommendation: G5.10 cause search vs re-opening saturation law
Run the single cause-search session now, but offline first (existing S148 logs, no flight): split alt loss into
(thrust deficit x duration at saturation) versus z-loop response, and explain the S147 -> S148 growth (the S147 gradual
per-motor faults were gentler, so 2.7 m is probably the true value, not a regression). If the loss matches the thrust
deficit physics (PID is worse, 3.2 m+), the 2.0 m limit is a gate-text problem: put it in Q9 with the numbers. Only if
the log shows the INDI/z loop leaving recoverable altitude (collective not at max, mean_u/gap remover limiting) re-open
saturation handling as a decision. Re-opening now without that split would repeat the G5.5 pattern.

## Next 2 sessions
- S149 (G5.10): action 0 this route check committed; key2 of THR_SC change + g510_check; offline alt-loss split; file
  Q9 a/b with numbers (alt 2.67-2.74 vs 2.0, tilt cap 45 deg vs 20 deg). Stop at one session either way.
- S150 (G5.9a/G5.8): if Q8/Q9 answered, apply the answers and score G5.8 3 m/s 3 seeds and G5.10; if not, take G5.6/G5.11
  probes and the pre-freeze review split (STATE 4c) for the stage-3 safety diff. No G5.5 chase before the freeze re-fly.
