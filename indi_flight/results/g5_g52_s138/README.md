# G5.2 position-mode stick steps (S138), result: 6/6 PASS

Exact test: `indi_flight/GATES.md` section 5b, bullet "G5.2 exact test (S138 ...)". Thresholds unchanged.

## Built
- Scenario `stick_pos_steps` (`bench/scenarios.py`): settle 3 s, zstep 2 s, zhold 6 s, xstep (cap 2.5 s), xhold 6 s, hold 3 s.
  Runner drops the x segments for `--stick-mode altctl`. Sticks from `stick_profile.pos_step_sample` (by segment name, no `--stick-pilot`).
- z step: throttle stick = inv_expo(1.0 / MPC_Z_VEL_MAX_UP 3) = 0.564 (raw 782). x step: pitch stick = inv_expo(3.0 / MPC_VEL_MANUAL 10) = 0.529
  (raw 529), expo 0.6 as `Sticks::getPitchExpo` with MAN_DEADZONE 0 (src/lib/sticks/Sticks.cpp, FlightTaskManualAcceleration; MPC_POS_MODE 4 default,
  stick sets acceleration scale and velocity target stick * MPC_VEL_MANUAL). `MPC_VEL_MANUAL` 10 (default) is now set explicitly in `STICK_PARAMS`.
- Checker `bench/g52_check.py`, self-test `bench/tests/test_g52_check.py` (known overshoot / settle values, failing overshoot and settle case,
  small-d invalid, wrong nav_state invalid; all 5 pass, `python3 bench/tests/test_g52_check.py`).
- Batch `run_batch.sh` (SEEDS / MODES env, resume by flight.ulg), `params.params` copied from g5_g51_ky20_s137 (K_Y 20 identified-gain config).

## Choice recorded: x step end
The runner has no live truth (only LOCAL_POSITION_NED, the estimator). The x step ends at 3.0 m of ESTIMATOR horizontal travel from the step start
or 2.5 s. In all 3 posctl runs the 2.5 s cap ended it (truth travel at release 2.31-2.32 m), so the estimator-vs-truth difference did not decide anything;
the actual travel d (4.2 m) includes the coast after release. Not a fixed-time substitute, a closer reading of the row than the fallback.

## Pre-test findings (no fix round needed)
Steps happen as specified on the log: nav_state 1 (altctl) / 2 (posctl) throughout; z edge raw 782 -> 500 after 2.0 s; x edge 529 -> 0 after 2.5 s;
d valid in all runs (z 1.98-2.04 m >= 1.0, x 4.17-4.20 m >= 2.0). Horizontal motion is along the vehicle heading (not NED north); the checker
uses the horizontal norm and projects on the step direction. Truth position 800 Hz.

## Results (`g52_summary.txt`, per-run `g52_check.json`)
| mode | seed | step | d [m] | overshoot [m] (<=0.3 z / 0.5 x) | settle [s] (<=4.0) | off-axis [m] | verdict |
|---|---|---|---|---|---|---|---|
| altctl | 1 | z | 1.98 | 0.011 | 1.79 | 0.03 | PASS |
| altctl | 2 | z | 2.00 | 0.001 | 2.67 | 0.02 | PASS |
| altctl | 3 | z | 1.99 | 0.011 | 1.87 | 0.03 | PASS |
| posctl | 1 | z / x | 2.04 / 4.18 | 0.010 / 0.044 | 1.95 / 1.95 | 0.05 / 0.03 | PASS |
| posctl | 2 | z / x | 2.04 / 4.20 | 0.007 / 0.039 | 2.97 / 2.13 | 0.06 / 0.05 | PASS |
| posctl | 3 | z / x | 2.02 / 4.17 | 0.026 / 0.063 | 1.19 / 1.88 | 0.04 / 0.06 | PASS |
No LOC in any run (tilt max 8 deg in posctl s1, min height far above 0.2 m).

## Unverified
- The x step is capped by time, not distance (3.0 m estimator travel never reached); "3.0 m of truth travel" itself did not occur (2.3 m at release).
- Single stick amplitude per axis, default MPC_ACC_HOR 3 / POS_MODE 4; no wind or gust. Wind was not part of the row.
