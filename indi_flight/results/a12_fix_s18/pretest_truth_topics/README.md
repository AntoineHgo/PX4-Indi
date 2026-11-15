# T38 pre-test (S19): truth topics after the A-12 fix

One PID hover, quad5in, seed 1, speed 4, rate 800 Hz, 1.25 ms world, inside Docker (`indi_project/docker/run.sh -n pre_s19_truth -t 300 -- python3 indi_flight/bench/run_scenario.py --scenario hover --controller pid_default --model quad5in --seed 1 --speed 4 --rate-hz 800 --out indi_flight/results/a12_fix_s18/pretest_truth_topics/hover`). rc 0, 40 s wall, metrics.json written, no warnings.

- Truth topics (ULog): vehicle_attitude_groundtruth, vehicle_angular_velocity_groundtruth, vehicle_local_position_groundtruth all 800.0 Hz median, max gap 3.8 ms, inside the gyro span (`truth_check.md`, from `bench/check_truth_s18.py`). A-12 fix confirmed for attitude and rate truth.
- `g1_1.txt` (`bench/gate_g1.sh g1.1`): gyro, angular velocity, actuator_motors, torque setpoint pass (max gap 2.5 ms, no A-13 gap in this flight); esc_status max gap 3.8 ms = limit -> FAIL (A-10); vehicle_local_position 88.9 Hz vs 125 (open). Verdict FAIL on those two rows only. g1_checks.py does not yet list attitude/rate truth rows: add them.
- New: EKF-truth z residual up to 2.22 m in the first ~8 s after arm (take-off), < 0.025 m in the 55-85 s hover window, 0.10 m max in the S18 flight -> A-14.
- Caution: `check_truth_s18.py` writes its report to the fixed path `results/a12_fix_s18/second_key.md` (overwrote the T37 file; restored with git). Fix: output path argument.
