# Tuning driver spec (`bench/tune.py`), session 7

Serves the fairness rule of `bench/scenarios.md` sec. 2 and 5: `pid_tuned` and
`indi` are tuned by the same procedure, the same number of evaluations, the
same cost J, on the tuning set only. One script, two parameter spaces.

## Command

```
python3 bench/tune.py --family {pid,indi} --n-candidates 24 --seeds 1 2 \
    --jobs 6 --sampler-seed 0 [--base-params bench/params/indi_v1.params] \
    [--round-name r1] [--center CANDIDATE_JSON] [--span-factor 2.0]
```

## Behaviour

1. Candidates: Latin hypercube in log-space, `n` points, generated with numpy
   `default_rng(sampler_seed)`. Each parameter ranges over
   `[center / span, center * span]`. Candidate 0 is always the center itself.
   Centers: PX4 defaults read from the parameter YAML/C files for `pid`
   (verify the values in `src/modules/mc_rate_control/*.yaml` and
   `src/modules/mc_att_control/*.yaml`, and any gz_x500 airframe override
   under `ROMFS/px4fmu_common/init.d-posix/airframes/`), or `--center`.
2. Spaces (log-uniform):
   - `pid`: MC_ROLLRATE_P, MC_ROLLRATE_I, MC_ROLLRATE_D, MC_PITCHRATE_P,
     MC_PITCHRATE_I, MC_PITCHRATE_D, MC_YAWRATE_P, MC_YAWRATE_I, MC_ROLL_P,
     MC_PITCH_P, MC_YAW_P (11 dims).
   - `indi`: MC_INDI_K_R, MC_INDI_K_P, MC_INDI_K_Y, MC_INDI_ACT_TC,
     MC_ROLL_P, MC_PITCH_P, MC_YAW_P (7 dims). G1 is fixed from
     identification (base params file), not tuned.
   PID gets more dims than INDI; that is inherent to the controllers and
   is recorded, the evaluation budget stays equal.
3. For each candidate write `results/tuning/<family>/<round>/c<NN>/params`
   (base params file lines first, then the candidate's lines, format
   `NAME VALUE`, same as `bench/params/*.params`), then run each scenario
   x seed through `bench/run_scenario.py` + `bench/metrics.py` exactly as
   `bench/run_batch.sh` `run_one` does (reuse it: e.g. call run_batch.sh
   with a controller label and a params path, add a `PARAMS_FILE` env
   override to run_batch.sh if needed, keeping its default behaviour
   unchanged). Run outputs go under
   `results/tuning/<family>/<round>/c<NN>/<scenario>/seed<S>[_x4]/`.
   Up to `--jobs` containers in parallel. Skip runs whose metrics.json
   already exists (resumable after a kill).
4. Scenarios and primary metric (metrics.json keys):
   - `hover`, speed 1: `position.rms_3d_m`
   - `step_roll`, speed 4: `attitude_tracking.roll_rms_deg`
   - `step_pitch`, speed 4: `attitude_tracking.pitch_rms_deg`
   - `step_yaw`, speed 4: `attitude_tracking.yaw_rms_deg`
   - `rate_step_roll`, speed 4: `rate_tracking.roll_rms_rad_s`
   Effort metric: `effort.motor_rate_rms_per_s`.
5. Reference: `pid_default` (no params overlay) on the same scenario, seed
   and speed, under `results/runs/<scenario>/pid_default/seed<S>[_x4]/`.
   Run it first if missing (same machinery).
6. Cost: J = mean over (scenario, seed) of primary/primary_ref, plus
   0.2 x (effort_ratio - 1) for each (scenario, seed) where effort_ratio =
   effort/effort_ref > 1.25 (penalty averaged the same way), plus 10 for a
   failed run (no ULog, runner rc != 0, or missing metric). Write
   `results/tuning/<family>/<round>/summary.csv` (one row per candidate:
   params, J, per-scenario ratios, failures) after every candidate, and
   print the best 5 at the end.
7. Every container gets a timeout (600 s), stale `px4-indi-*` containers of
   the same name are removed first (as run_batch.sh does). Never touch the
   container `peaceful_bhabha`.

## Done when

`python3 bench/tune.py --family indi --n-candidates 2 --seeds 1 --jobs 2
--scenarios step_roll --round-name smoke --base-params
bench/params/indi_v0.params` runs end to end (add `--scenarios` to restrict
the list, default all five) and writes summary.csv with finite J; same with
`--family pid`. `--dry-run` prints candidates without flying.
