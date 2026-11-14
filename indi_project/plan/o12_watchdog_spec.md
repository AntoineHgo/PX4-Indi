# Implementation spec: O-12 watchdog and staged screening (session 43)

Owner decision O-12 (`OWNER_GUIDANCE.md`). NOT to be applied while a validation batch is flying (every run calls
`bench/run_scenario.py`): start only after HELDOUT_V2_REFLY_DONE is in `results/s2_heldout_v2/run.log` and no
`px4-indi-*` container is up. Log: `plan/impl_log_o12.md`. Two separate benchmark-tooling commits (watchdog; staging).

## Part A: watchdog in `bench/run_scenario.py`

Checked in `Sim.run()` after every ATTITUDE tick (sim time), only once the vehicle is airborne in the scenario phase
(after takeoff completes, before the landing phase). ATTITUDE already arrives at 100 Hz; also keep roll/pitch and
the body rates from it in `pump()`.

| trip | threshold | why (to record in DECISIONS.md D-watchdog) |
|---|---|---|
| tilt | max(abs(roll), abs(pitch)) > 60 deg for >= 0.5 s sim | MPC_TILTMAX_AIR is 45 deg; the largest commanded tilt in any scenario is ~52 deg (H4, infeasible); 60 deg sustained is loss of control for both families |
| altitude | height (-z) < 0.3 m while airborne, or more than 3.0 m below the altitude setpoint for >= 1.0 s | position scenarios hold 2.5 m; the worst recorded excursions (D-hovernoise, motor loss) are well under 1 m |
| non-finite | NaN/inf in roll, pitch, yaw or body rates | controller fault |
| no ticks | no ATTITUDE for 10 s wall while px4 is alive | stalls (host suspend, D-v2-refly) should end fast, not after 900 s |

Motor saturation is not streamed over MAVLink today; it is not used online (saturation time stays an offline metric).

On a trip: stop advancing, record `meta["watchdog"] = {"reason", "t_sim_s", "value"}` in run.json, land/kill and stop
PX4 exactly as the existing RunError path does, keep the ULog, and exit non-zero so `run_batch.sh` and the s2 batch
scripts see a failure. `metrics.py` must still run on the ULog; the run counts as FAILED in every summary (never as
a dropped seed). Thresholds are module constants with a one-line comment each, overridable by `--watchdog off` for
diagnosis only (never in a batch).

Replay check (must be done before the commit): `bench/watchdog_replay.py` applies the same trips offline to
`vehicle_attitude` and `vehicle_local_position` of every `flight.ulg` under `results/` (PID and INDI, v1 and v2),
using the scenario phase window from run.json. Write the table of trips to `results/o12_watchdog_replay.md`. Expected:
trips only on runs already recorded as crashes/failures (H4 crashes 10/10 both families; r1 c12 failure). Any other
trip means a threshold is wrong: loosen it and say so.

## Part B: staged screening in `bench/tune.py` (and `run_batch.sh` if needed)

- New option `--stages` (default: one stage = today's behaviour). Stage 1: every candidate on 1 seed of a scenario
  subset given on the command line (the 2-3 most discriminating, chosen per round and recorded in its results file).
- After stage 1: drop a candidate that failed (watchdog or crash) or whose J > 1.3 x the best J so far (`--prune-ratio`,
  default 1.3); keep at most `--keep` (default 4) best.
- Stage 2: survivors on the full scenario set and seeds. Pruned candidates' remaining runs are never launched.
- The round summary lists pruned candidates with their stage-1 J and the reason. Say in report ch. 7 that staged
  pruning is used from the v3 screening on.
