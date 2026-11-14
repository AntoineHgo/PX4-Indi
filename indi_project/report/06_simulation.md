# 6. Simulation environment and its limits

Every number in chapters 7 and 8 was produced in one simulator: PX4 software-in-the-loop (SITL) with the Gazebo Harmonic `gz_x500` quadrotor, run headless inside a container. This chapter describes that environment, the extensions added to it so that the disturbance and plant-change scenarios could be flown, the frozen benchmark that runs on it, and the ways in which the simulator is easier on the INDI controller than a real vehicle would be. Decision identifiers (D-speed and so on) refer to `indi_project/DECISIONS.md`. Facts about the simulated vehicle come from `indi_project/bench/sim_fidelity.md`. Where the project data do not support a statement, the text says so and lists it as a limitation.

## 6.1 Toolchain and reproducibility

### 6.1.1 Container

All builds and flights run in the Docker image `px4-indi-sim`, defined in `indi_project/docker/Dockerfile`. It starts from Ubuntu 24.04 and runs the repository's own `Tools/setup/ubuntu.sh --no-nuttx`, so the PX4 build dependencies, Gazebo Harmonic, MAVSDK and the Python test requirements come from the same script that PX4 developers use. The stock `Tools/setup/Dockerfile` has no Gazebo (`--no-sim-tools`), hence the dedicated image. It adds a software OpenGL driver and `xvfb` for a headless Gazebo server, `procps` and `scipy`. The gz-sim version in the image is 8.15 (`DECISIONS.md`, D-dist).

`indi_project/docker/run.sh` is the single entry point. It runs one command as the host user with the repository mounted at its own path, `~/.ccache` shared, no TTY, no privileged options, no published ports and a wall-clock timeout (default 3600 s). With `-N` the container gets a private network namespace with only loopback. The benchmark runner works in this mode: Gazebo, PX4 and the MAVLink link between the runner and PX4 all live inside it (`indi_project/bench/RUNNER_NOTES.md`, step 2).

### 6.1.2 One run

`indi_project/bench/run_scenario.py` flies one scenario for one controller and one seed (`--scenario`, `--controller`, `--seed`, `--speed`, `--params`, `--out`, `--instance`). It sets `HEADLESS=1`, `PX4_SIM_MODEL=gz_x500` and `PX4_SIM_SPEED_FACTOR` from `--speed`, and starts the Gazebo server itself (`gz sim -r -s --seed N`) before PX4, because the PX4 start script attaches to an already running world. The runner talks to PX4 with pymavlink, and setpoint timing follows `time_boot_ms` (PX4 simulation time), so scenario timing does not depend on the speed factor.

Each run uses a fresh PX4 working directory under its output folder. The shared build rootfs would keep `parameters.bson` between runs; a fresh directory means every run starts from the airframe defaults and parallel runs are safe. The logger profile is raised (`SDLOG_PROFILE=17`) so that rates, attitude and motors are logged at full rate. The record `run.json` stores scenario, controller, seed, speed factor and the extension parameters applied.

PX4 and Gazebo run in lockstep (`DECISIONS.md` D-hover-noise; `bench/sim_fidelity.md`). The project does not configure this; it is the stock SITL behaviour. `boards/px4/sitl/sitl.cmake` enables the lockstep scheduler for every SITL build except replay, and the Gazebo bridge (`src/modules/simulation/gz_bridge/GZBridge.cpp`, `clockCallback`) sets the PX4 monotonic clock from the Gazebo `/world/<name>/clock` topic on every message, through `px4_clock_settime`, which advances the lockstep scheduler (`platforms/posix/src/px4/common/drv_hrt.cpp`). PX4 time therefore advances only when the simulator steps.

### 6.1.3 Seeds

The seed has three effects. It seeds the Gazebo noise generator (`gz sim --seed N`), from which the IMU, magnetometer and barometer noise are drawn. It jitters the disturbance profile: gust onset time uniform within +-0.5 s and wind direction within +-10 deg (`indi_project/bench/scenarios.md` section 3.3). The same seed list is used for every controller (paired design). Tuning evaluations use 3 seeds (2 in round 1), the final validation 10.

Two things are not seeded. The barometer simulation inside PX4 calls `srand(1234)` with a fixed value that cannot be changed without a firmware change (`RUNNER_NOTES.md`, step 1). The trajectory start phase is not randomised either (`scenarios.md`, change log, session 15). Nor does the seed make a run exactly repeatable (6.5).

### 6.1.4 Speed factor and the D-speed finding

Running at real time (factor 1) is slow, so the speed factor was checked before the benchmark (D-speed, session 4, `indi_project/results/speedcheck_pid_default.md`). On `pid_default`, seeds 1 to 3, at factor 1 and factor 4, the attitude-step and rate-step metrics (rate RMS, attitude RMS, rise time, overshoot, motor effort) agreed within the seed-to-seed spread. Hover position RMS did not: 0.027 m (range 0.021 to 0.033) at factor 1 against 0.064 m (0.038 to 0.104) at factor 4.

The decision was to run attitude and rate scenarios at factor 4 and every scenario whose metric is a position (hover, trajectory tracking, gust position deviation) at factor 1. Factor 1 everywhere would cost four times the CPU; factor 4 everywhere was rejected because it changes position-hold results. The cause was left open (candidates: MAVLink setpoint timing at factor 4, EKF and sensor timing). The check covered `pid_default` only, so agreement for the tuned PID and INDI at factor 4 is untested (`report/07_tuning.md`).

## 6.2 The gz_x500 vehicle model

Table 6.1 lists what the stock model contains, read in session 17 from the model files (`indi_project/bench/sim_fidelity.md`). The right-hand column is the gap to a real vehicle, as stated in that file.

| Item | gz_x500 value | Source file | Gap to a real vehicle |
|---|---|---|---|
| Motor dynamics | first order, time constant 0.0125 s up, 0.025 s down | `Tools/simulation/gz/models/x500/model.sdf` | no ESC delay, no voltage sag |
| Thrust and moment constants | k_f = 8.54858e-6, k_m/k_f = 0.016 | same | allocator assumes `CA_ROTOR*_KM` 0.05 |
| Rotor speed feedback | none measured; `esc_rpm` echoes the command | chapter 4, `plan/px4_analysis_verification.md` | INDI uses its onboard motor model |
| IMU rate | 250 Hz | `Tools/simulation/gz/models/x500_base/model.sdf` | real IMUs run at 1 to 8 kHz with anti-aliasing |
| Gyro noise | white Gaussian, std 8.7e-4 rad/s (0.05 deg/s) per axis, no bias, no drift | same | no vibration, no bias instability |
| Accelerometer noise | white Gaussian, std 0.00637 m/s^2 (x, y), 0.00686 (z), no bias | same | no vibration-induced noise |
| Barometer, magnetometer | baro 50 Hz, std 3 Pa; mag 100 Hz, std 3e-7 T | same | |

*Table 6.1: gz_x500 model values and gaps (`bench/sim_fidelity.md`).*

### 6.2.1 What the INDI controller depends on

The controller of chapter 5 uses three quantities that are properties of the simulated plant, and the model supplies each in an idealised form.

1. **Angular acceleration.** It is obtained by differentiating the gyro, filtered in the sensors module. The gyro in the model is white, bias-free and vibration-free. Differentiation amplifies exactly the high-frequency content that this model leaves out.
2. **Actuator state.** The controller does not read rotor speed. In gz the `esc_rpm` message only echoes the command, so there is nothing to feed back, and INDI uses its own first-order motor model with time constant `MC_INDI_ACT_TC` (chapter 5; tuned value 0.01142 s in `DECISIONS.md` D-freeze). The plant itself is first order with 0.0125 s up and 0.025 s down. Controller model and plant have the same structure, which is the favourable case for actuator compensation (assessment, not tested).
3. **Control effectiveness.** The gain G1 (241, 241 and 7.4 for roll, pitch and yaw in D-freeze) is a property of this vehicle. They were fitted in-loop from flight data of the first INDI flights, regressing filtered angular acceleration on the filtered torque increment (`results/sync_check_v0.md`, roll/pitch 237/245 averaged to 241, R^2 0.95; yaw 7.4), and stored in `bench/params/indi_v1.params`.

The thrust and moment constants contain one deliberate inconsistency that both controllers inherit. The model has k_m/k_f = 0.016 while the PX4 allocator assumes `CA_ROTOR*_KM` = 0.05 (airframe `4001_gz_x500`), a model error of about a factor of 3 in yaw moment (`sim_fidelity.md`). It is the same for PID and INDI.

## 6.3 Simulator extensions

The stock model has no wind, no payload change, no per-motor degradation and no way to change inertia per run. Four extensions were added, each in the harness and none in the model files; `Tools/simulation/gz/models` is never modified. Following `scenarios.md` section 3, each controller experiences the same change and disturbance with the same seeds.

### 6.3.1 Gusts and payload (`bench/disturbance.py`)

`indi_project/bench/disturbance.py` runs inside the container next to the runner. It loads Gazebo's `ApplyLinkWrench` system at runtime through the world service, so no world or model file is edited (D-dist, session 10). It then publishes a one-step wrench on the `base_link` of the x500 at every Gazebo clock message. The profile is a function of Gazebo simulation time, so it does not depend on the speed factor. The runner writes the onset (PX4 time) to `disturbance_trigger.json`, and the applied wrench is logged to `disturbance.csv`.

Four profiles are implemented.

- **gust_x (T6).** A base wind of 3 m/s along +x ramped in 2 s and held for 10 s, then a 1-cosine gust of +6 m/s over 1 s (peak 9 m/s), then 15 s of hold. Wind is modelled as quasi-steady drag, F = 0.5 rho C_d A v|v|, with rho = 1.225 kg/m^3 and C_d A = 0.06 m^2, applied 5 cm above the centre of mass. C_d A and the centre of pressure height are assumptions of the project (`plan/disturbance_spec.md`, as referenced in the source), not measured values.
- **gust_diag (H2).** The same shape with a 4 m/s base wind towards 45 deg and a gust of 8 m/s towards 120 deg lasting 0.6 s, angles measured from gz world +x towards +y.
- **payload_add (T7).** A downward force of 25 % of the vehicle weight (mass 2.0 kg plus four rotor links, g = 9.8 m/s^2) held for the scenario window. The mass and inertia of the plant are not changed.
- **com_shift (H3).** A downward force of 15 % of the weight whose line of action is 5 cm along +y from the centre of mass, with the lever arm fixed in the world frame. This is a level-hover approximation that is valid while the vehicle holds its spawn yaw and stays near level (`scenarios.md`, change log).

### 6.3.2 Motor loss

Motor loss (T8 `motor_loss_0`, H4 `motor_loss_2`) is applied by the runner, not by the injector (`bench/run_scenario.py`, `bench/scenarios.py`). At the start of the fault segment the runner reads `SIM_GZ_EC_MIN` and `SIM_GZ_EC_MAX` of the chosen motor channel and sets both to the square root of the thrust scale times their original value. Rotor speed is MIN + (MAX - MIN) c for command c, and gz thrust is proportional to speed squared, so the thrust of that motor is the chosen fraction of nominal at every command. T8 uses motor 0 at 0.7, H4 motor 2 at 0.6. The fault changes the thrust constant only. The PX4 control allocator is not aware of the fault: `SIM_GZ_EC_MIN`/`SIM_GZ_EC_MAX` are read only by the gz bridge output mapping (`src/modules/simulation/gz_bridge/GZMixingInterfaceESC.cpp`), downstream of `control_allocator`, whose effectiveness matrix is unchanged. Both controllers therefore face an unannounced loss of effectiveness.

### 6.3.3 Plant variants (`bench/model_variant.py`)

Mismatch scenarios need a different plant, not a different disturbance. `indi_project/bench/model_variant.py` builds a per-run copy of the `x500` and `x500_base` models in the run folder, with the multiplicative scales `ixx`, `iyy`, `izz` (base link inertia), `mass` (base link only, propeller link masses unchanged) and `tau` (motor time constants up and down, all four rotors). The runner points `PX4_GZ_MODELS` at the copy. T9 uses Ixx and Iyy x1.3. H5 uses inertia x0.8 on all three axes, mass x1.15 (2.3 kg as reported by gz) and motor time constants x2, i.e. 0.025 s up and 0.05 s down (D-h5, session 15). The controllers are not told about any of these changes.

## 6.4 Scenarios and metrics

The benchmark is specified in `indi_project/bench/scenarios.md`, frozen on 2026-11-13 (session 3) before any INDI code existed. Later changes were allowed only to repair a harness defect, are logged at the end of that file and apply to both controllers. All scenarios start from a 5 m hover in offboard mode. Three controllers are compared: `pid_default` (PX4 airframe defaults), `pid_tuned` and `indi`, the last two tuned on the tuning set with the same procedure, budget and cost function.

| Set | Scenarios |
|---|---|
| Tuning (T) | T1 `hover`; T2 `step_roll`, `step_pitch`; T3 `step_yaw`; T4 `rate_step_roll`; T5 `traj_lemniscate`; T6 `gust_x`; T7 `payload_add`; T8 `motor_loss_0`; T9 `mismatch_inertia` |
| Held-out (H) | H1 `traj_circle_fast`; H2 `gust_diag`; H3 `com_shift`; H4 `motor_loss_2`; H5 `mismatch_combined`; H6 `step_diag` |

*Table 6.2: scenario sets (`bench/scenarios.md` sections 3.1 and 3.2).*

Each H scenario varies the parameters of one T mechanism (H1 of T5, H2 of T6, H3 of T7, H4 of T8, H5 of T9, H6 of T2), so that tuning cannot memorise it. Held-out runs are made only for final validation and at most once per design iteration, without driving gain changes. Stage-1 tuning used T1 to T4 only, because T5 to T9 needed the extensions of 6.3 (change log, v1.1). The tuning cost is the mean, over tuning scenarios and seeds, of the primary metric divided by that of `pid_default` on the same scenario and seed, plus an effort penalty above a ratio of 1.25 and 10 per failed run.

Metrics are computed from the ULog alone by `indi_project/bench/metrics.py`, inside the window from offboard engagement to exit: rate and attitude error, step rise time, overshoot and settling, disturbance peak and recovery time, control effort (RMS of the motor-output derivative, and of the outputs about their mean), saturation time and a safety flag. A run with attitude error above 60 deg, ground contact or divergence fails, and failed runs are reported, never dropped. Before any tuning run, the step metric became RMS attitude error instead of IAE because `metrics.py` computes RMS (change log, v1.1).

Final comparisons are paired by seed (10 seeds) with a two-sided Wilcoxon signed-rank test per scenario at alpha = 0.05. INDI outperforms `pid_tuned` only if no run fails, it is significantly better by at least 10 % on at least 4 of the 6 H scenarios, it is not significantly worse by more than 10 % on any, and its hover effort is at most 1.5 times that of `pid_tuned`. The criteria were applied literally (D-accept). The outcome, given in chapter 8, is "INDI does not outperform PID".

Two held-out scenarios exceed what the airframe and default position controller allow, and were flown unchanged, since softening a held-out scenario after seeing a result would be selection after the fact (D-h5). H1 needs about 52 deg of tilt against `MPC_TILTMAX_AIR` of 45 deg, and in H4 both controllers crash (D-accept). Part of the benchmark outcome therefore reflects scenario severity, not rate-loop quality.

## 6.5 Fidelity limits and their effect on the conclusions

`scenarios.md` section 7 asked for a fidelity check before T6 to T9 and H were flown. The note was written in session 17, after the benchmark (`sim_fidelity.md`). It changes no result, but it was not available when the scenarios were designed.

**Sensor model.** The gyro and accelerometer are white, bias-free and vibration-free, sampled at 250 Hz against 1 to 8 kHz with anti-aliasing on real IMUs. INDI differentiates the gyro, so this favours INDI; the project's own assessment is that the disturbance-rejection margins measured here are likely optimistic for real flight (`sim_fidelity.md`, not tested). The hover-effort criterion is likewise evaluated on a clean signal.

**Actuators.** The plant is a first-order lag with no ESC delay and no voltage sag, and gz provides no rotor-speed feedback (`esc_rpm` echoes the command), so INDI relies on its own motor model. Its structure matches the plant, which probably helps INDI. The measured weakness under actuator mismatch (rate pulses 1.58 times worse in H5, D-accept) must be read with this in mind.

**Latency.** End-to-end sensor-to-actuator latency in SITL was not characterised; lockstep makes it one or two control cycles (`sim_fidelity.md`). No experiment in this project varies the delay, so the sensitivity of INDI to added transport delay (section 3.5) is not quantified here.

**Aerodynamics and disturbances.** Gusts and payload are external wrenches on a rigid body, with assumed drag coefficient, area and centre-of-pressure height (6.3.1). There is no rotor wake, ground effect or blade flapping (`sim_fidelity.md`). The payload and CoM scenarios apply a force and leave plant mass and inertia unchanged; only H5 changes them. `x500_base/model.sdf` contains no plugin at all, and `x500/model.sdf` adds only four `gz-sim-multicopter-motor-model-system` plugins and the `MotorFailurePlugin`, so there is no aerodynamic model beyond the rotor drag terms of the motor plugin. The moment-constant mismatch (k_m/k_f 0.016 in gz, 0.05 in the allocator) is common to both controllers.

**Run-to-run non-determinism (D-hovernoise).** Re-flying one seed gives hover position RMS up to about 2 times apart, while attitude and rate step metrics re-fly within about 2 % (D-hover-noise, session 9). The suspected cause is thread scheduling between PX4 and Gazebo under lockstep, which the seed does not control; this was not tested (`report/07_tuning.md`). In session 13 the hover term of the tuning cost was found to be dominated by sporadic vertical excursions, present for both controllers, with tight and equal horizontal RMS. The frozen cost was kept, J differences below about 0.1 are not treated as meaningful, and hover is reported across seeds with a horizontal and vertical split. The cause of the excursions is open, and whether they are related to the speed-factor effect of 6.1.4 was not tested.

**Effect on the conclusions.** Both controllers fly the same plant, noise, disturbances and seeds, so the comparison is fair, and the negative acceptance outcome is not weakened by simulator optimism: a noisier real gyro would, if anything, hurt INDI. The positive finding, INDI's disturbance-rejection gain, is the one most exposed to the idealised gyro and motor model and should be read as an upper bound. Differences in hover and position metrics cannot be resolved with the seeds used. Nothing here supports a claim about real flight; a hardware test would have to measure the noise floor and vibration, ESC and sensor latency and the true motor response, none of which was done.
