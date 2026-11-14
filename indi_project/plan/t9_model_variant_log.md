# T9 mismatch_inertia: per-run gz model variant log

Date: 2026-11-14.

## Step 1: where the model comes from (found)

- Inertia and mass: `Tools/simulation/gz/models/x500_base/model.sdf`, `base_link` `<inertial>`
  (mass 2.0, ixx = iyy = 0.0216667, izz = 0.04). Propeller links have their own tiny inertials (left alone).
- Motor time constants: `Tools/simulation/gz/models/x500/model.sdf`, `timeConstantUp` 0.0125 and
  `timeConstantDown` 0.025 in each of the 4 motor plugins (8 values). x500 includes `model://x500_base`.
- Spawn path: `ROMFS/px4fmu_common/init.d-posix/px4-rc.gzsim` spawns
  `file://${PX4_GZ_MODELS}/${MODEL_NAME}/model.sdf` (model name `x500`, instance name `x500_0`). So
  `GZ_SIM_RESOURCE_PATH` alone does NOT redirect the top-level model; `PX4_GZ_MODELS` must point at the variant
  dir. The nested `model://x500_base` include is resolved through `GZ_SIM_RESOURCE_PATH`, so the variant dir is
  also prepended there.
- Env is built in `Sim.load_env()` of `bench/run_scenario.py` (sources `build/px4_sitl_default/gz_env.sh`);
  gz is started by `Sim.start_gz()`, PX4 by `Sim.start_px4()`, both with `self.env`.

## Step 2: mechanism chosen

- New `bench/model_variant.py`: `build_variant(spec, out_dir, stock_models)` copies `x500` and `x500_base` to
  `<run out>/model_variant/` (model.sdf and model.config are real copies; meshes, materials, thumbnails are
  symlinks to the stock files), edits the copies with ElementTree, returns `(dir, record)`.
  Keys (all multiplicative scale factors): `ixx`, `iyy`, `izz`, `mass` (base_link only), `tau` (all 8 motor time
  constants; the code checks it finds exactly 8). Unknown keys raise.
- `scenarios.py`: scenario key `model_variant=dict(...)`; new scenario `mismatch_inertia`
  (T2 attitude steps identical to `step_roll`, `model_variant=dict(ixx=1.3, iyy=1.3)`).
- `run_scenario.py`: `Sim.apply_model_variant()` sets `PX4_GZ_MODELS=<variant dir>` and prepends it to
  `GZ_SIM_RESOURCE_PATH` before gz/PX4 start; `run.json["model_variant"]` holds scale, dir, original and new
  values. Also, for every scenario, after PX4 startup the runner saves `gz model -m x500_0` to
  `gz_model_info.txt` (loaded mass and inertia matrix) as evidence.
- H5 reuse: `model_variant=dict(ixx=0.8, iyy=0.8, izz=0.8, mass=1.15, tau=2.0)`. Open choice for H5: whether
  Izz is also scaled (spec says "inertia x0.8"; the keys allow it). Not run here.
- Stock models are never modified (variant is generated per run under the results dir).

## Step 3: verification

- T9 run (`NAME_TAG=t9`, pid_default, seed 1, speed 4): exit_status ok, rc 0.
- `gz_model_info.txt` of the T9 run: base_link inertial matrix 0.028167 / 0.028167 / 0.040000, mass 2.0
  (stock 0.021667 -> x1.3 = 0.028167). gz.log warnings quote the loaded file path
  `.../mismatch_inertia/pid_default/seed1_x4/model_variant/x500_base/model.sdf`.
- `run.json["model_variant"]`: original ixx = iyy = 0.021666..., new 0.028166...
- Unchanged scenario check: `step_roll` re-run (same settings, scratch results dir inside results/, deleted
  afterwards): no `model_variant` string in gz.log, no `model_variant` key in run.json, `gz_model_info.txt`
  inertia 0.021667. Stock model loaded.
- A first attempt with the results dir in the agent scratchpad outside the repo failed (container does not
  mount it; no gz.log produced). Not a code problem; results dirs must be under the repo.

## Step 4: run numbers (pid_default, seed 1, x4)

| metric | T9 inertia x1.3 | step_roll stock (this session) | reference r2/c00 step_roll |
|---|---|---|---|
| roll_rms_deg | 3.271 | 3.352 | 3.366 |
| roll rate rms (rad/s) | 0.0961 | 0.0862 | 0.0869 |
| rise 10-90 up (s) | 0.411 | 0.424 | 0.437 |
| rise down (s) | 0.426 | n/a | 0.429 |
| rise zero1 / zero2 (s) | 0.364 / 0.360 | 0.377 / n/a | 0.367 / 0.363 |
| overshoot zero2 (%) | 0.44 | n/a | 0.55 |

Observation: the expected slightly slower response with more inertia is NOT visible. Rise times and roll rms
are marginally smaller than the stock runs, and the stock-vs-stock difference (0.424 vs 0.437 s) is as large as
the T9 effect, so the attitude step response of the default PID is insensitive to this mismatch at this
amplitude (the attitude P loop with its rate limit dominates; the rate loop is much faster). The roll-rate rms is
about 10 % higher in T9, which is the only visible effect. Single seed, so the sign of the small differences is
not significant. The plant change itself is confirmed by gz (inertia matrix), so this is a property of the
controller, not of the mechanism.

## Unverified

- `mass` and `tau` keys of `model_variant` are implemented and the tau count check is coded, but no run used
  them (H5 not run). Not exercised.
- Multi-seed significance of the T9 effect.
