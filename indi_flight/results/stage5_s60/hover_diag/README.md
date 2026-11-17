# S60 diagnostic hover, stage-5 hover slice + stage-condition instrument

Build: `indi_project/docker/run.sh -n s60bld -t 1500 -- make px4_sitl_default` (rc 0, HEAD = instrument commit)
Flight: `indi_project/docker/run.sh -n s60diag -t 420 -- python3 indi_flight/bench/run_scenario.py --scenario hover --controller indi_s60 --model quad5in --seed 1 --speed 4 --params indi_flight/results/stage5_s60/hover_diag/hover.params --out indi_flight/results/stage5_s60/hover_diag/run` (rc 0)

Findings (log `run/flight.ulg`, logged messages + takeoff_status):
- mc_indi_pos_control ran (its reports are in the log; mc_pos_control fallback not used).
- Stage ACTIVE (cond 0x5f) from 34.04 s (take-off state 5 at 34.02 s) to 97.95 s (landing, state 3 at 98.62 s); bypass
  during RAMPUP and landing as designed (A3/A8).
- Telemetry bit 0x20 never set: hover.params has no MC_INDI_W_MAX, so measured thrust is off and the stage runs on the
  modelled actuator state. The thrust-gap flight must set MC_INDI_W_MAX (and the rate loop's measured path) or it
  does not test lesson 9.
- Pre-flight, the attitude-freshness bit flickers (0x1c/0x1e): `now >= _q_time` fails when the attitude sample is newer
  than the cycle's `now`. Harmless on the ground; in flight it would drop the stage to bypass for a cycle. Fix: accept
  a sample newer than now (age clamp at 0).
- Residual check (`/tmp/s60_ident.py`-style: published |thrust| vs stock mapping ht|g-a_ref|/g) is ~1e-4 for BOTH
  chains in a gap-free hover (scale ht/g = 0.014): it cannot tell INDI from stock here. The thrust-gap flight is the
  discriminating test.
