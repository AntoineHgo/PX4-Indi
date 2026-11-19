# S128 MC_INDI_ACT_TC comparison: SITL hover and step_roll, INDI, quad5in, seed 1

## Params
Both files are copies of `indi_flight/results/smoke_s128_idok0/smoke_params.params` with `MC_INDI_ID_OK 1` set.
- `a050.params`: `MC_INDI_ACT_TC 0.05`
- `a033.params`: `MC_INDI_ACT_TC 0.033`

Each run's ULog confirms the values (`initial_parameters`): ACT_TC 0.05 / 0.033, ID_OK 1 / 1.

## Commands
Hover (run in parallel):

    timeout 900 indi_project/docker/run.sh -n s128tc050 -t 420 -- python3 indi_flight/bench/run_scenario.py --scenario hover --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --params indi_flight/results/act_tc_s128/a050.params --out indi_flight/results/act_tc_s128/a050
    timeout 900 indi_project/docker/run.sh -n s128tc033 -t 420 -- python3 indi_flight/bench/run_scenario.py --scenario hover --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --params indi_flight/results/act_tc_s128/a033.params --out indi_flight/results/act_tc_s128/a033

Step (run in parallel; scenario `step_roll` from the `--scenario` choices, attitude mode, 15 deg roll steps):

    timeout 900 indi_project/docker/run.sh -n s128tcstep050 -t 420 -- python3 indi_flight/bench/run_scenario.py --scenario step_roll --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --params indi_flight/results/act_tc_s128/a050.params --out indi_flight/results/act_tc_s128/a050_step_roll
    timeout 900 indi_project/docker/run.sh -n s128tcstep033 -t 420 -- python3 indi_flight/bench/run_scenario.py --scenario step_roll --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --params indi_flight/results/act_tc_s128/a033.params --out indi_flight/results/act_tc_s128/a033_step_roll

Analysis (`/tmp/claude-analysis/ar.py`, outside the repo, run inside the wrapper):

    indi_project/docker/run.sh -n s128q050 -t 120 -- python3 -c "$(cat /tmp/claude-analysis/ar.py)" indi_flight/results/act_tc_s128/a050/flight.ulg

## Method
- Exit code: wrapper exit (`exit=` lines in `a*.exit` files); metrics.json `status`.
- Times: raw ULog timestamps (`t_us * 1e-6`), as `bench/metrics.py`. Takeoff = first ground-truth NED z < -1 m (about 35 s in these runs).
- Body rates: `vehicle_angular_velocity`, from takeoff to log end. RMS per axis, max of the norm.
- Motor activity: RMS of the sample-to-sample first difference of `actuator_motors.control[0..3]`, from takeoff to log end (normalized units per sample, not per second).
- Hover quality: `vehicle_local_position_groundtruth` over the metrics.json window 55.02-85.02 s, as in `smoke_s128_idok0/README.md`.
- Roll-rate PSD: uniform resample (800 Hz), Hann window, amplitude spectrum, peak above 5 Hz, from takeoff to log end.

## Results

| Metric | hover a050 | hover a033 | step_roll a050 | step_roll a033 |
|---|---|---|---|---|
| Exit code | 0 | 0 | 0 | 0 |
| metrics.json status | ok | ok | ok | ok |
| MC_INDI_ACT_TC (ULog) | 0.05 | 0.033 | 0.05 | 0.033 |
| MC_INDI_ID_OK (ULog) | 1 | 1 | 1 | 1 |
| Body rate RMS roll / pitch / yaw (rad/s) | 0.0050 / 0.0043 / 0.0008 | 0.0054 / 0.0054 / 0.0011 | 0.1586 / 0.0098 / 0.0038 | 0.1618 / 0.0050 / 0.0028 |
| Body rate max norm (rad/s) | 0.0336 | 0.0262 | 1.4027 | 1.4662 |
| Motor diff RMS c0 / c1 / c2 / c3 | 0.00048 / 0.00049 / 0.00049 / 0.00057 | 0.00048 / 0.00048 / 0.00048 / 0.00045 | 0.00092 / 0.00086 / 0.00084 / 0.00080 | 0.00068 / 0.00068 / 0.00069 / 0.00069 |
| Ground-truth z mean (m, NED) | -4.963 | -4.981 | -3.841 | -3.835 |
| Ground-truth z std (m) | 0.0184 | 0.0199 | 1.892 | 1.899 |
| Max abs x deviation (m) | 0.037 | 0.048 | 11.088 | 11.075 |
| Max abs y deviation (m) | 0.046 | 0.042 | 0.114 | 0.087 |
| Roll rate PSD peak above 5 Hz (Hz, rad/s) | 5.43, 1.1e-4 | 5.54, 1.0e-4 | 5.25, 1.09e-2 | 5.24, 9.4e-3 |

## Notes and caveats
- Hover z/xy stats use the 55.02-85.02 s window. For step_roll, that window runs past the scenario (metrics.json window ends at 69.04 s), so the step z std and xy deviations include post-scenario drift and are not hover-quality numbers. The 11 m x deviation is the step maneuver's lateral drift.
- Step body rates and PSD cover the whole post-takeoff log, not just the step segments. The step PSD peak (about 0.01 rad/s at 5.2 Hz) is about 100 times the hover peak; it is not checked against a per-segment or step-edge analysis, so it is not evidence of a sustained oscillation.
- One seed per configuration. Differences are not statistically tested.

## Comparison
In hover, ACT_TC 0.05 and 0.033 are indistinguishable (roll rate RMS 0.0050 vs 0.0054 rad/s, z std 0.018 vs 0.020 m). In the 15 deg roll step, ACT_TC 0.033 gave about 20-25% lower motor-command first-difference RMS (0.00068-0.00069 vs 0.00080-0.00092) with body-rate RMS within about 2% (roll 0.162 vs 0.159 rad/s).
