# Second key, commit 09515cd8ae (S113)

No BLOCKING, no MAJOR.

1. disturbance.py. fn is either PROFILES gust_x or the lambda (t, af_, vel=None, ...) at :279. The lambda forwards vel as
   the 6th positional of gust_x, which is correct. fn(tp, af, vel=pv.vel) works for both with and without --wind-*.
   Other profiles call fn(tp, af) and are unaffected. Frame and sign are right: rel = w*(cos, sin) - v, and -vz for z,
   with world-frame velocity from the pose finite difference (same frame as the wind). vel_none counts ticks without
   velocity. The Pose/Pose_V import ahead of Node is not testable offline.
2. g3_sample.py. Rejection redraw is uniform on the valid set (kept draws are uniform, redraws are uniform on the cube
   restricted to the valid set), deterministic (stream seeded from u via digest_int and repr). One sx, sy, sz feeds isc
   (g1_ctrl_mult) and inertia_scale (plant overrides). No other use of lin(u["ix"]) is left. Nominal diag matches
   model.sdf. The 1e-3 margin is far above the r6 rounding (5e-7).
3. metrics/g3_run. Normal run: 40 tests pass, status "ok". No consumer of g3_done.json exists in bench/ besides g3_run.py
   skip logic; the aborted marker is only read there.
Mutations (copies, all caught): no-redraw fails 2 sample tests; metrics abort branch off fails test_metrics aborted test;
classify aborted->incomplete fails test_g3_run aborted test.
MINOR: disturbance main() mutation (vel=pv.vel -> positional) is not caught; no test covers main (needs gz).
MINOR g3_run.py:classify: returncode 0 returns "ok" even if run.json says exit_status failed; metrics.py aborted test is
only "window missing", so a failed run with a complete window counts ok in metrics and aborted in g3_run only if rc!=0.
MINOR: aborted metrics.json has no "window" key; a11_effort_rate.py:57 and g1_checks.py:102 would KeyError on it (G1 tools).
