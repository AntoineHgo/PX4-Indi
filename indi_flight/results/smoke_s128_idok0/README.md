# S128 SITL smoke flight: hover, INDI, quad5in, seed 1

## Command
Attempt 1 (as specified) exited at startup with `--controller indi needs MC_RATE_CTL_TYPE 1 in the params file`
(the tracked defaults file does not set it). Attempt 2 (completed) used a copy of the params file with
`MC_RATE_CTL_TYPE 1` appended (`smoke_params.params` in this dir); the tracked file was not changed.

    timeout 900 indi_project/docker/run.sh -n s128smoke -t 420 -- python3 indi_flight/bench/run_scenario.py --scenario hover --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --params indi_flight/results/smoke_s128_idok0/smoke_params.params --out indi_flight/results/smoke_s128_idok0

## Result
- Exit code 0, no runner output, metrics.json status "ok", no warnings.
- px4.log: "Disarmed by landing" (normal end). Preflight warnings only: no GCS connection, no heading reference.
- Files: flight.ulg, metrics.json, run.json, px4.log, gz.log, gz_model_info.txt, sends.csv, smoke_params.params.

## Parameters (from flight.ulg initial_parameters)
- MC_INDI_ID_OK 0
- MC_INDI_K_R 20.0
- MC_INDI_G1_R 1757.0
- MC_INDI_W_MAX 2700.0

## Hover quality (vehicle_local_position_groundtruth, window 55.02-85.02 s ULog time, 30 s)
- z mean -4.985 m (NED, about 4.98 m altitude), z std 0.0149 m
- max |x - mean x| 0.049 m, max |y - mean y| 0.058 m
- max body rate (vehicle_angular_velocity, norm) 0.028 rad/s
