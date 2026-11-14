# Actuator identification, Gazebo x500 (s2)

Script: `indi_project/bench/identify_actuator.py` (numpy + pyulog). Raw outputs are appended below as each step finishes.

## Method

- Reference: `actuator_motors.control[i]` (normalised, [0, 1]) is scaled by PX4 MixingOutput to the SIM_GZ_EC_MIN/MAX range of the output function and published unchanged by gz_bridge as the gz rotor velocity reference: `omega_ref = 150 + c * (1000 - 150)` rad/s (MIN/MAX read from the log parameters, x500 defaults 150/1000; FUNCn = 100 + n so motor i is esc[i]). `rpm_ref = omega_ref * 60 / (2 pi)`. This mapping is taken from the code, not fitted; it is confirmed by the data: hover c = 0.728 gives 7344 rpm, and the median measured/reference gain in the fit is 1.00. rotorVelocitySlowdownSim (10) is already inside `esc_status.esc_rpm`.
- Plant model: `x[j+1] = x[j] + (1 - exp(-h/tau)) (u(t_j - d) - x[j])`, `tau = tau_up` if the delayed reference is above the state, else `tau_down`, which is exactly the gz-sim `FirstOrderFilter` (checked in `indi_project/research/raw/gz_sim8/MulticopterMotorModel.cc`; the filter uses the physics `dt`, 4 ms). The SDF values in every log's `model_variant/x500/model.sdf` are 0.0125 s up / 0.025 s down.
- The esc_status samples cannot be used with a fixed-dt recursion: they are logged at an irregular 1-12 ms spacing and most are stale repeats of the previous value (38 % in the true-speed log, 86 % in the v2 eRPM logs). A first version of the fit that treated every logged sample as a 4 ms step gave tau about 20 % too short (10 / 20 ms) and a 4-5 times larger residual; this was an artefact of the stale samples (a stale sample behaves like a random one-frame jitter). The final fit therefore simulates 0.1 s blocks on a 1 ms grid with a held reference (gz applies the last command), restarts each block from a fresh sample, and scores only fresh (value-changing) samples.
- Fit: least squares over (tau_up, tau_down, d): per delay a log-spaced 14 x 14 grid over 3-120 ms plus two local refinements; delay on a 1 ms grid from -4 to +16 ms (negative would mean a sample stamped before the command it reflects). Only airborne samples (`vehicle_land_detected.landed` false) with reference above 30 % of 1000 rad/s over the whole block. Per log and motor, then pooled over all motors and logs (pooled delay searched only within +-2 ms of the per-motor median, for run time).
- Confidence: the pooled cost is re-evaluated with the taus scaled by 0.8 / 1.2 (up, down, both) and with up and down swapped, delay kept. Cost increase = relative RMS increase.

## Result

| data | tau_up [ms] median over motors/logs (pooled) | tau_down [ms] | delay vs actuator_motors timestamp | RMS [rpm] fit / SDF taus |
|---|---|---|---|---|
| (a) true rotor speed, 1 log x 4 motors | 12.4 (12.40) | 25.0 (24.76) | 0 ms | 1.2 / 1.3 |
| (b1) eRPM, rate_step_roll, 3 seeds x 4 motors | 12.2 (12.18) | 25.2 (25.20) | 1 ms (0.6 ms by parabola) | 18.8 / 19.0 |
| (b2) eRPM, step_roll, 3 seeds x 4 motors | 12.2 (11.75) | 25.2 (24.76) | 1 ms (0.6 ms by parabola) | 13.2 / 13.6 |
| SDF `timeConstantUp/Down` | 12.5 | 25.0 | | |

- The identified time constants agree with the SDF values (0.0125 s up, 0.025 s down) within about 1-3 % on the true rotor speed and within the motor-to-motor scatter on the eRPM logs. In (a) the per-motor values are 12.2-12.4 / 24.8-25.2 ms, and the SDF-tau residual (1.28 rpm pooled) is practically the same as the fitted one (1.26 rpm). The data therefore confirm the SDF values; they do not call for different ones.
- Excitation of the up/down split: good. Scaling the taus by +-20 % raises the pooled cost by 380-660 % on the true speed and by 30-110 % on the eRPM data (tau_up alone: +31 to +61 % in the eRPM logs, the weaker of the two); swapping up and down costs +560 to +2700 %. Both taus are well constrained, tau_up a little less in the eRPM logs (per-motor tau_up 10.8-13.3 ms in step_roll; seed 2 and 3 motors 1-2 are the outliers at 10.8-11.3 ms).
- Delay: 0.0 ms in (a) (parabola on the delay profile: -0.07 ms), i.e. the rotor speed responds to the command in the same 4 ms physics step (the filter output is written to the joint in the step that receives the command; the logged state is the one after that step). The pure delay between `actuator_motors` and the true rotor speed is therefore about zero in this setup, apart from the ZOH of the 250 Hz command.
- Extra delay of the eRPM telemetry relative to (a): about +0.6 to +1 ms (profiles at fixed SDF taus, 1 ms grid: minimum at 1 ms for both eRPM sets and 0 ms for (a); parabolic minima 0.63 and 0.59 ms vs -0.07 ms). **This is not the expected one 250 Hz frame (4 ms).** Not explained and not verified against the bridge. Possible causes: (1) the esc_status callbacks in the v2 logs come at an irregular 1-11 ms spacing (mean 5 ms) with a 1 ms physics step in that world (`world/default.sdf`: max_step_size 0.001), so one callback of latency is shorter than 4 ms for part of the samples; (2) 86 % of the eRPM samples repeat the previous value (14.3 rpm quantisation plus drops) and the fit scores only the samples where the value changed, which biases the timing estimate towards a smaller delay. A direct check would need the telemetry callback rate and a log with no quantisation or drops; not done.
- Poor fits and caveats: (1) the eRPM residuals (13-20 rpm) are 10-15 times larger than the true-speed ones (1.2 rpm). The 14.3 rpm quantisation alone gives about 4 rpm, the rest is timing uncertainty of the telemetry and the stale-sample selection; the fitted taus are nevertheless consistent with (a). (2) (a) is a single log (step_roll_pid_seed1, 250 Hz IMU, 4 ms physics step); the eRPM data are two manoeuvres x 3 seeds with a 1 ms physics step; all use the same PID controller near hover (airborne, reference above 30 % of max), so behaviour below 30 % of max or at the limits is not identified. (3) A first fit that treated every logged sample as a regular 4 ms step gave 10 / 20 ms; this was a bias from the stale samples (see Method), which is why the block / 1 ms-grid scheme is used. (4) Delay resolution is 1 ms; tau resolution is limited by the grid refinement (about 0.2 ms). (5) The pooled-fit delay is searched only within +-2 ms of the per-motor median.

Reproduce: `python3 indi_project/bench/identify_actuator.py --md indi_project/results/s2_ident_act.md --label "<label>" <flight.ulg ...>` (the md is appended to; the three runs below used the default 0.1 s block and 30 % reference threshold). The delay profile at the SDF taus was computed with a throw-away script using `rms_grid` and `delayed_ref` of the same module.

## Raw outputs

### (a) true rotor speed (SIM_GZ_ESC_FB=1, 250 Hz IMU), step_roll_pid_seed1

| log | motor | blocks | tau_up [ms] | tau_down [ms] | delay [ms] | RMS [rpm] | RMS SDF taus [rpm] (best d) |
|---|---|---|---|---|---|---|---|
| s2_escfb_check/step_roll_pid_seed1 | 0 | 408 | 12.4 | 24.8 | 0 | 1.2 | 1.2 (d=0) |
| s2_escfb_check/step_roll_pid_seed1 | 1 | 406 | 12.4 | 24.8 | 0 | 1.5 | 1.6 (d=0) |
| s2_escfb_check/step_roll_pid_seed1 | 2 | 408 | 12.2 | 25.2 | 0 | 1.2 | 1.4 (d=0) |
| s2_escfb_check/step_roll_pid_seed1 | 3 | 406 | 12.4 | 25.2 | 0 | 0.9 | 0.8 (d=0) |

Median over motors/logs: tau_up 12.4 ms, tau_down 25.0 ms, delay 0.0 ms, RMS 1.2 rpm, RMS with SDF taus 1.3 rpm.

Pooled over all motors/logs (1628 blocks of 0.10 s): tau_up 12.40 ms, tau_down 24.76 ms, delay 0 ms, RMS 1.26 rpm; SDF taus RMS 1.28 rpm (best delay 0 ms).

Cost increase of the pooled fit when the taus are perturbed (delay kept): tu x0.8 +409%, tu x1.2 +379%, td x0.8 +520%, td x1.2 +398%, both x0.8 +659%, both x1.2 +542%, swap up/down +2727%.
Median of the per-motor fits: tu x0.8 +485%, tu x1.2 +406%, td x0.8 +584%, td x1.2 +498%, both x0.8 +708%, both x1.2 +604%, swap up/down +2820%.

### (b1) eRPM telemetry, rate_step_roll/pid_default seeds 1-3

| log | motor | blocks | tau_up [ms] | tau_down [ms] | delay [ms] | RMS [rpm] | RMS SDF taus [rpm] (best d) |
|---|---|---|---|---|---|---|---|
| s2_tuning/ref/rate_step_roll/pid_default/seed1_x4 | 0 | 182 | 12.4 | 25.7 | 1 | 16.7 | 16.9 (d=1) |
| s2_tuning/ref/rate_step_roll/pid_default/seed1_x4 | 1 | 185 | 12.4 | 24.8 | 1 | 19.8 | 19.9 (d=1) |
| s2_tuning/ref/rate_step_roll/pid_default/seed1_x4 | 2 | 172 | 12.4 | 25.2 | 1 | 18.2 | 18.3 (d=1) |
| s2_tuning/ref/rate_step_roll/pid_default/seed1_x4 | 3 | 180 | 12.2 | 25.2 | 1 | 16.9 | 17.4 (d=1) |
| s2_tuning/ref/rate_step_roll/pid_default/seed2_x4 | 0 | 179 | 12.6 | 24.8 | 1 | 19.0 | 19.0 (d=1) |
| s2_tuning/ref/rate_step_roll/pid_default/seed2_x4 | 1 | 182 | 12.2 | 25.2 | 1 | 19.6 | 20.1 (d=1) |
| s2_tuning/ref/rate_step_roll/pid_default/seed2_x4 | 2 | 178 | 12.2 | 25.7 | 1 | 16.7 | 17.5 (d=1) |
| s2_tuning/ref/rate_step_roll/pid_default/seed2_x4 | 3 | 186 | 12.2 | 24.3 | 1 | 20.3 | 20.5 (d=1) |
| s2_tuning/ref/rate_step_roll/pid_default/seed3_x4 | 0 | 185 | 12.4 | 26.1 | 0 | 22.9 | 23.7 (d=0) |
| s2_tuning/ref/rate_step_roll/pid_default/seed3_x4 | 1 | 178 | 12.2 | 24.8 | 1 | 18.6 | 19.1 (d=1) |
| s2_tuning/ref/rate_step_roll/pid_default/seed3_x4 | 2 | 194 | 12.2 | 24.8 | 1 | 18.5 | 18.8 (d=1) |
| s2_tuning/ref/rate_step_roll/pid_default/seed3_x4 | 3 | 187 | 12.2 | 26.1 | 0 | 22.4 | 23.4 (d=0) |

Median over motors/logs: tau_up 12.2 ms, tau_down 25.2 ms, delay 1.0 ms, RMS 18.8 rpm, RMS with SDF taus 19.0 rpm.

Pooled over all motors/logs (2188 blocks of 0.10 s): tau_up 12.18 ms, tau_down 25.20 ms, delay 1 ms, RMS 19.77 rpm; SDF taus RMS 20.02 rpm (best delay 1 ms).

Cost increase of the pooled fit when the taus are perturbed (delay kept): tu x0.8 +61%, tu x1.2 +49%, td x0.8 +93%, td x1.2 +80%, both x0.8 +111%, both x1.2 +91%, swap up/down +683%.
Median of the per-motor fits: tu x0.8 +64%, tu x1.2 +56%, td x0.8 +106%, td x1.2 +78%, both x0.8 +124%, both x1.2 +93%, swap up/down +728%.

### (b2) eRPM telemetry, step_roll/pid_default seeds 1-3

| log | motor | blocks | tau_up [ms] | tau_down [ms] | delay [ms] | RMS [rpm] | RMS SDF taus [rpm] (best d) |
|---|---|---|---|---|---|---|---|
| s2_tuning/ref/step_roll/pid_default/seed1_x4 | 0 | 174 | 12.2 | 26.6 | -1 | 11.8 | 12.6 (d=0) |
| s2_tuning/ref/step_roll/pid_default/seed1_x4 | 1 | 165 | 12.8 | 25.7 | 0 | 12.1 | 12.3 (d=0) |
| s2_tuning/ref/step_roll/pid_default/seed1_x4 | 2 | 172 | 12.6 | 25.2 | 0 | 12.6 | 12.7 (d=0) |
| s2_tuning/ref/step_roll/pid_default/seed1_x4 | 3 | 184 | 12.0 | 26.6 | -1 | 11.3 | 12.3 (d=0) |
| s2_tuning/ref/step_roll/pid_default/seed2_x4 | 0 | 167 | 12.2 | 24.8 | 1 | 13.3 | 13.4 (d=1) |
| s2_tuning/ref/step_roll/pid_default/seed2_x4 | 1 | 171 | 11.1 | 23.9 | 1 | 13.4 | 15.2 (d=1) |
| s2_tuning/ref/step_roll/pid_default/seed2_x4 | 2 | 178 | 11.3 | 24.3 | 1 | 13.4 | 14.5 (d=1) |
| s2_tuning/ref/step_roll/pid_default/seed2_x4 | 3 | 182 | 12.2 | 24.8 | 1 | 13.5 | 13.6 (d=1) |
| s2_tuning/ref/step_roll/pid_default/seed3_x4 | 0 | 163 | 13.3 | 26.1 | 0 | 13.6 | 14.2 (d=1) |
| s2_tuning/ref/step_roll/pid_default/seed3_x4 | 1 | 162 | 10.9 | 25.2 | 1 | 13.2 | 14.4 (d=1) |
| s2_tuning/ref/step_roll/pid_default/seed3_x4 | 2 | 170 | 10.8 | 24.8 | 1 | 13.1 | 14.4 (d=1) |
| s2_tuning/ref/step_roll/pid_default/seed3_x4 | 3 | 178 | 12.2 | 25.2 | 1 | 13.5 | 13.6 (d=1) |

Median over motors/logs: tau_up 12.2 ms, tau_down 25.2 ms, delay 1.0 ms, RMS 13.2 rpm, RMS with SDF taus 13.6 rpm.

Pooled over all motors/logs (2066 blocks of 0.10 s): tau_up 11.75 ms, tau_down 24.76 ms, delay 1 ms, RMS 13.67 rpm; SDF taus RMS 14.12 rpm (best delay 1 ms).

Cost increase of the pooled fit when the taus are perturbed (delay kept): tu x0.8 +38%, tu x1.2 +31%, td x0.8 +83%, td x1.2 +61%, both x0.8 +96%, both x1.2 +70%, swap up/down +563%.
Median of the per-motor fits: tu x0.8 +40%, tu x1.2 +32%, td x0.8 +85%, td x1.2 +66%, both x0.8 +100%, both x1.2 +82%, swap up/down +586%.
