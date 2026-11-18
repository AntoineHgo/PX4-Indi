# S113 fixes (G3 pre-test faults 1, 2, 4b)

## Fault 1: wind drag not air-relative (bench/disturbance.py)
- Cause: reproduced inside Docker with `gz sim -s -r sim/worlds/default.sdf` + the real disturbance.py: `msg.pose` raised
  `TypeError: No message class registered for 'gz.msgs.Pose'` in the pose callback. The topic type is gz.msgs.Pose_V (checked with
  `gz topic -i`). Pose_V was imported late (after Node() creation); a small standalone subscriber worked, the runner order did not.
- Fix: import gz.msgs10.pose_pb2 and pose_v_pb2 with the other message imports at the top of main(), before Node().
- Second bug found while verifying: when no --wind-* flag is given, `fn(tp, af, pv.vel)` passed the velocity as `steady`
  (TypeError at `c_drag * w`). Now `fn(tp, af, vel=pv.vel)` (works for gust_x and the wind lambda). vel_none accounting untouched.
- Verified (real gz, ground_plane as model, quad5in airframe, 28 s profile, no wind flags): vel_none_ticks 0 of 22401 updates,
  first valid velocity at sim 18.0 s (the onset). Before the fix: error on every callback. Probe outputs: results/g3_pretest_s112/fix_s113_probe/o3a.
- UNVERIFIED: a full PX4 flight with a moving vehicle (velocity values are not checked, only delivery); the run with explicit
  --wind-steady/--wind-peak flags (second probe run did not complete; same call path through the lambda's `vel` keyword, not exercised).
  No host unit test (no gz python module on the host).

## Fault 2: invalid inertia draws (bench/g3_sample.py)
- Nominal base_link diag (sim/models/quad5in_base/model.sdf): 1.022, 1.122, 1.944 e-3. Valid = each moment < sum of other two (1e-3 margin).
- Fix: keep independent linear draws; if the triple is invalid, REJECT-RESAMPLE the triple uniformly in [0.7,1.3]^3 from a stream
  seeded by sha256 of the original ix/iy/iz coordinates (pure function of u, deterministic per seed). Chosen over projection/clipping
  because clipping piles ~1/3 of draws onto the boundary. Cost: exact LHS strata for ixx/iyy/izz no longer hold (the
  stratification test no longer asserts them for those three axes; replaced by a coverage test). Corner pins (all 1.0 / 1.3) are valid and unchanged.
- Coverage, 300 draws each, seeds 1/2/3 (0 invalid): ixx [0.702,1.300] [0.700,1.300] [0.705,1.300]; iyy [0.704,1.300] [0.706,1.300] [0.700,1.300];
  izz [0.701,1.300] [0.702,1.300] [0.701,1.300]; every axis fills all 10 deciles.
- Tests: test_inertia_always_physical_and_covers_range, test_inertia_validity_check_rejects_old_failure. Both fail with the fix bypassed (checked).
- Note: draws change vs S112 for ~1/3 of runs (only inertia and the derived g1_ctrl_mult of those runs).

## Fault 4b: aborted runs
- metrics.py compute(): run.json with a window start but no end (or no window and failed) now returns `status: "aborted"` plus an
  `aborted` block (reason, exit_status, error, watchdog) and a warning; no metric blocks. Normal runs get `status: "ok"`. No formula touched.
  Old behaviour (TypeError at metrics.py:531) confirmed by stashing the fix. Test: test_aborted_run_reports_status_not_crash.
- g3_run.py: new classify()/finalize(). An aborted run (returncode != 0 and run.json exit_status failed) writes g3_done.json with
  outcome "aborted" (+ error, watchdog, metrics_status), sets g3_outcome in run.json, and is not retried. Timeout / no run.json =
  outcome "incomplete" -> g3_failed.json, no done marker (retried, as before). Tests: test_aborted_run_gets_done_marker_and_outcome,
  test_ok_and_incomplete_outcomes.
- UNVERIFIED: end-to-end on a real aborted flight (unit tests only). run_scenario.py runs metrics.py as a subprocess, so metrics.json now
  carries status aborted and the driver no longer prints METRICS FAILED for these (not flown).

## Tests
`python3 -m pytest` (venv with pytest+numpy; host python lacks pytest): test_g3_sample, test_metrics, test_g3_run, test_disturbance_k110: 40 passed.
