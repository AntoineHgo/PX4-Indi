# Bench port plan (indi_project/bench to indi_flight)
Scope: 131 files under `indi_project/bench/`. Purposes come from script headers only; bodies unread (UNVERIFIED). R = `indi_project/review/external_review_s59_notes/`, M = `indi_project/review/external_review_s59.md`. "none named" means the review names no defect, not that the script is clean.

## 1 and 2. Inventory with review defects
| path (under bench/) | lines | purpose | cat | review defects named (file:line) |
|---|---|---|---|---|
| `run_scenario.py` | 622 | SITL runner for one scenario (gz lockstep, MAVLink setpoints, params, sag, motor fault) | runner | R/sim_review.md:14 (setpoint and param timing jitter), :19 (sag as wall-paced staircase) |
| `scenarios.py` | 168 | scenario table, sim-second durations | scenario | none named (R/report_audit.md:42,48 fault the report, not the script) |
| `metrics.py` | 384 | per-run metrics from ULog and run.json | metric | M:51 (trajectory error vs 5 Hz held reference, :309-317, verified); M:73; M:390 (never cross-checked) |
| `disturbance.py` | 225 | wrench injector T6, T7, H2, H3 | injector | R/sim_review.md:6 (payload weight only), :7 (com_shift INVALIDATES, world-frame torque), :8 (gust uses world wind), :13 (async wrench, may sum) |
| `model_variant.py` | 112 | model variants (mass, inertia, tau, imu_rate) | injector | R/sim_review.md:34 (mass scales base_link only), :36 (imu_rate confounded with physics step) |
| `tune.py` | 369 | tuning driver, one cost J, PID and INDI spaces | other | none named |
| `make_figures.py` | 442 | regenerates report figures from data | other | none named |
| `summarize_seeds.py` | 99 | mean/std over seeds, two controllers | analysis | none named |
| `compare_runs.py` | 33 | metrics.json side-by-side table | analysis | none named |
| `regress_compare.py` | 61 | old vs new binary regression table | analysis | none named |
| `s2_verdict.py` | 144 | v2 verdict on held-out set V | analysis | none named (M:298 rule: recompute metrics independently) |
| `accel_gain.py` | 28 | accel-to-torque gain per band vs 59 Hz GT | ident | M:428 wrong (30-80 Hz band above GT Nyquist; report 8.10 rests on it) |
| `identify_g1.py` | 104 | G1 and actuator time constant | ident | M:424 suspect; R/ident_review.md:3 (ZOH 286 Hz onto 250 Hz, fs=250 assumed) |
| `identify_g2.py` | 107 | yaw G2 | ident | M:426 suspect (stale rpm interpolation, 1 kHz filter on 250 Hz chain) |
| `ident_gt.py` | 249 | G_T and k_cmd from hover | ident | M:425 suspect (fit through origin, no excitation) |
| `identify_actuator.py` | 194 | gz motor first-order lag | ident | M:429 sound |
| `ident_s8_delay.py` | 57 | a_f vs t_f lag | ident | M:427 suspect (integer lags, logged cycle index) |
| `omega2_torque_check.py` | 86 | eRPM torque vs INDI actuator model | ident | none named (UNVERIFIED: not in review) |
| `erpm_torque_resid.py` | 28 | eRPM torque vs 12.5 ms model, per band | analysis | none named |
| `gt_accel_bands.py` | 21 | GT roll accel spectrum 0-29.5 Hz | analysis | none named |
| `gt_lag.py` | 71 | GT vs PX4 estimate timing | analysis | M:429 sound |
| `check_sync.py` | 104 | INDI filter synchronisation check | analysis | M:429 sound |
| `effort_axes.py` | 26 | per-axis hover effort | analysis | none named |
| `hover_cause.py` | 45 | hover causal test, measured torque on/off | analysis | none named |
| `hover_effort_split.py` | 48 | hover effort per mode and band | analysis | none named |
| `indi_terms.py` | 21 | nu and a_f term split in hover | analysis | none named |
| `yaw_step_effort.py` | 86 | control activity around yaw steps | analysis | none named |
| `pid_hover_mode.py` | 40 | 2-4 Hz roll-rate RMS per flight | analysis | none named |
| `pid_hover_scan.py` | 199 | pid hover mode log scan | analysis | none named |
| `glitch_scan.py` | 64 | estimator glitch detection | analysis | none named |
| `vib_check.py` | 44 | IMU vibration spectrum and effort | analysis | none named |
| `watchdog_replay.py` | 264 | offline replay of watchdog trips | analysis | none named |
| `s8_track_diag.py` | 132 | trajectory tracking diagnosis | analysis | none named (UNVERIFIED: may share M:51 held reference) |
| `s8b_activation_check.py` | 32 | INDI POS activation summary | analysis | none named |
| `tilt_diag.py` | 139 | tilt diagnosis helper | analysis | none named |
| `v3_hover_effort.py` | 47 | v3 hover effort vs pid_tuned | analysis | none named |
| `run_batch.sh` | 86 | host batch driver, one container per run | runner | none named |
| `smoke_gz.sh` | 56 | in-container lockstep smoke | runner | none named |
| `s2_*.sh` (14) | 214 total | stage-2 campaigns (tuning, held-out V, seen set) | scenario | none named |
| `s8*.sh` (22) | 455 total | stage-8 campaigns (O set, GNSS, checks) | scenario | none named (R/agent_mgmt.md:34 spot-check only) |
| `v3_*.sh`, `vprime*.sh` (7) | 179 total | v3 screens, V' held-out set | scenario | none named |
| `hover_cause_test.sh`, `pid_hover_mode_test.sh` | 24, 26 | hover causal tests | scenario | none named |
| `scenarios.md` | 299 | frozen benchmark spec | scenario | M:287 (W1/W2 changed to tilt RMS, no amendment); M:111 (set O arms B, C never flown) |
| `sim_fidelity.md`, `RUNNER_NOTES.md` | 31, 46 | fidelity note, runner progress log | other | none named |
| `params/` (33), `__pycache__/` (12 .pyc) | n/a | parameter sets; generated bytecode | runner, skip | M:113 (`indi_v3.params` uses removed keys and duplicate keys) |

## 3. Stage 1 port list
- **1a runner, scenarios, metrics (first):** `run_scenario.py`, `scenarios.py`, `run_batch.sh`, `smoke_gz.sh`, `params/` (drop removed keys), `scenarios.md`. Fix with the port: `metrics.py` trajectory reference (M:51), sag staircase and setpoint timing (R/sim_review.md:14,19).
- **1b injectors (after the sim_review fixes):** `disturbance.py` (air-relative drag, body-frame com_shift torque, payload-inertia decision), `model_variant.py` (consistent inertia scale, decouple imu_rate from physics step).
- **2 identification (later):** `identify_actuator.py`, `check_sync.py`, `gt_lag.py` (sound); the other ident scripts only after rewrite (M:424-427).

## 4. Skip list
- `accel_gain.py`: wrong (M:428); rewrite, do not port.
- Campaign shell scripts (`s2_*`, `s8*`, `v3_*`, `vprime*`, two hover tests): frozen dated matrices; keep in the archive and cite by name.
- `tilt_diag.py`, `s8b_activation_check.py`, `pid_hover_scan.py`: one-session diagnostics. `__pycache__/`: generated. `make_figures.py`: defer until the report port.

## 5. Open items
- UNVERIFIED: script bodies unread; the review names no defect for "none named" rows, which is not a clearance.
- Keyword grep: "5 Hz" only at M:49-52 (bench) and R/sim_review.md:29 (GZBridge, not bench); "decimat" no hits; "wall" at R/sim_review.md:14,19.
- Run-to-run non-determinism (R/sim_review.md:14-15) affects every runner-based script; not tested by the review.
