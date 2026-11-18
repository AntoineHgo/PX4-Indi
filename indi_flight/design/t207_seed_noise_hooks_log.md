# t207 seed/noise hooks log
Plan: 1 SIM_GZ_SEED, 2 SIM_GZ_IMU_NSC, 3 runner keys, 4 build, 5 F1/F2 check, 6 summary.
Steps 1,2 edits done (module.yaml, GZMixingInterfaceESC.hpp, GZBridge.hpp/.cpp). Noise added before vibration; std::mt19937 own generator (no math::generate_wgn).
Step 3 runner keys --sim-seed/--imu-noise-scale added (env PX4_PARAM_*, meta sim_seed/imu_noise_scale). Build running via run.sh 'make px4_sitl_default' (log in scratchpad build.log).
Step 4 build rc=0 (0 errors). Next: flights F1/F2 -> indi_flight/results/t207_hooks/.
Step 5 flights F1,F2 rc=0 (results/t207_hooks/F*/run/flight.ulg). Analysis next.

## Final
Files changed: src/modules/simulation/gz_bridge/{module.yaml,GZMixingInterfaceESC.hpp,GZBridge.hpp,GZBridge.cpp}, indi_flight/bench/run_scenario.py (--sim-seed, --imu-noise-scale; run.json keys sim_seed, imu_noise_scale; env PX4_PARAM_SIM_GZ_SEED/IMU_NSC, v2 only). Analysis script results/t207_hooks/an.py.
Build: indi_project/docker/run.sh 'make px4_sitl_default' rc=0, 0 errors. Format check (astyle) NOT run.
Flights: scenario hover, indi_s98, quad5in, gap.params, --sim v2, --erpm-drop 0.1; F1 seed 1 scale 3, F2 seed 2 scale 1; both rc=0 (results/t207_hooks/F1, F2).
(a) dropout fraction (esc_errorcount increments per frame): F1 0.102-0.105 per motor, F2 0.103-0.105. First drop indices motor 0: F1 [1,7,23,25,32,...], F2 [0,3,5,14,22,...]: differ. Verdict SIM_GZ_SEED: OK. Seed 0 path unchanged by construction (state 0x12345678), not re-flown.
(b) gyro white noise (2nd-difference estimator, sensor_gyro 800 Hz, window 50-90 % of log): F1 x/y/z 2.61e-3 / 2.61e-3 / 2.64e-3; F2 8.69e-4 / 8.81e-4 / 8.72e-4 (SDF 8.73e-4). Ratio 3.0 on every axis. Raw std includes control motion (F1 6.2e-3, F2 5.2e-3 on x), so use the high-passed estimate. Verdict SIM_GZ_IMU_NSC gyro: OK.
Noise is added BEFORE the vibration term (vibration off in these flights).
Unverified: accel noise scaling not measured (same code path, sigmas 6.37e-3/6.37e-3/6.86e-3); seed 0 + scale>1 determinism not re-run; make format not run; the noise RNG is std::mt19937 (math::generate_wgn is not used).
