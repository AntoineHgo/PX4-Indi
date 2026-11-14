# Appendix A Reproducing the results

Commands run from the repository root (`PX4-Indi/`) unless stated otherwise. Project files are under `indi_project/`.

## A.1 Requirements

- **Docker** runs everything that builds or simulates: the image, the SITL firmware and the batch runs. The image is built from `indi_project/docker/Dockerfile` (Ubuntu 24.04, PX4 build dependencies, Gazebo Harmonic, MAVSDK, pytest, scipy) and is tagged `px4-indi-sim`.
- **bash** on the host runs the wrapper scripts (`docker/build.sh`, `docker/run.sh`, `bench/run_batch.sh`).
- The figure step (A.6) is the one place that needs host Python packages: `make_figures.py` needs numpy, matplotlib and pyulog. `summarize_seeds.py` uses only the standard library.

## A.2 Build the image and the firmware

Build the image (uses the host user's uid and gid, so files written into the bind-mounted repository stay owned by the user):

```
indi_project/docker/build.sh
```

Build the SITL firmware inside the image:

```
indi_project/docker/run.sh -n build -t 3000 'make px4_sitl_default'
```

This command is the one recorded in `indi_project/plan/integration_log.md`; it is not wrapped in a script (`docker/run.sh` options `-n` container name, `-t` timeout in seconds). It produces `build/px4_sitl_default`, the directory `bench/run_scenario.py` uses. Nothing is flashed to hardware.

## A.3 Run one scenario for one controller and seed

```
indi_project/docker/run.sh -n step1 -t 600 -N -- python3 indi_project/bench/run_scenario.py \
    --scenario step_roll --controller pid_default --seed 1 --speed 4 \
    --out indi_project/results/runs/step_roll/pid_default/seed1_x4
```

- `-N` gives the run its own loopback-only network namespace; `-t` is the wall-clock timeout in seconds.
- `--scenario` takes a key of `bench/scenarios.py` (for example `hover`, `step_roll`, `gust_x`). `--controller` is `pid_default` or `indi_tuned`. `--seed` (default 1) seeds the Gazebo sensor noise. `--speed` (default 1.0) is the simulation speed factor. `--params FILE` applies `NAME VALUE` lines before arming. `--out` is required.
- Output in `--out`: `flight.ulg` (the newest ULog of the run), `run.json` (scenario window, seeds and event records), `px4.log`, `gz.log` and `runner.log`.
- `run_scenario.py` does not write `metrics.json`. Create it with:

```
python3 indi_project/bench/metrics.py <out>/flight.ulg
```

  This writes `<out>/metrics.json`, reading `<out>/run.json` for the evaluation window.

## A.4 Run a batch over seeds

```
SCENARIOS="step_roll" CONTROLLERS="pid_default" SEEDS="1 2 3 4 5 6 7 8 9 10" \
SPEEDS="4" TIMEOUT=600 JOBS=4 indi_project/bench/run_batch.sh
```

Environment variables, with their defaults: `SCENARIOS` ("step_roll hover"), `CONTROLLERS` ("pid_default"), `SEEDS` ("1"), `SPEEDS` ("1 4"), `TIMEOUT` (600 s per run), `JOBS` (1 run at a time), `PARAMS_FILE` (overlay file, absolute path), `RESULTS_DIR` (default `indi_project/results/runs`), `FLAT_LAYOUT=1` (drops the controller directory), `NAME_TAG` (suffix for container names).

- Output: `indi_project/results/runs/<scenario>/<controller>/seed<N>[_x<speed>]/`, with the A.3 files plus `metrics.json`, which the batch writes itself.
- **Speed rule.** Attitude and rate scenarios (`mode` "attitude" in `bench/scenarios.py`) run at speed 4; position scenarios (`mode` "position", such as `hover` and the trajectory scenarios) run at speed 1. This is decision D-speed in `indi_project/STATE.md`: hover position RMS differs between speeds (0.027 m vs 0.064 m), attitude and rate metrics do not. The script does not apply the rule, and its default is `SPEEDS="1 4"`, so set `SPEEDS` per batch.
- **Controller overlay.** `bench/params/<controller>.params` is applied automatically if it exists. There is no `indi_tuned.params`; the frozen INDI candidate is set with `PARAMS_FILE`, which applies to every controller in that call. Run `indi_tuned` in its own call:

```
PARAMS_FILE="$PWD/indi_project/results/tuning/indi/r4f/c00/params" CONTROLLERS=indi_tuned \
SCENARIOS="step_roll" SEEDS="1 2 3 4 5 6 7 8 9 10" SPEEDS="4" indi_project/bench/run_batch.sh
```

  The frozen candidate is `results/tuning/indi/r4f/c00/params` (`NAME VALUE` lines; `DECISIONS.md`, D-freeze). Every `indi_tuned` run records this path and the applied values in its `run.json` (`params_file`, `params_applied`), which is the check that a run used the frozen set. The JSON files in `bench/params/` are tuning-space centres for `bench/tune.py`, not overlays.
- **Parallel batches.** Container names are `px4-indi-<scenario>-<seed><NAME_TAG>`, so give each concurrent batch its own `NAME_TAG`. Each run has its own network namespace, so port clashes do not occur, and each run has its own working directory.
- `run_batch.sh` does not skip finished runs. Re-running a batch re-flies and overwrites its output.

## A.5 Summaries and statistics

```
python3 indi_project/bench/summarize_seeds.py indi_project/results/runs step_roll \
    --a pid_default --b indi_tuned
```

The first argument is the runs directory, followed by one or more scenarios. `--a` (default `pid_default`) and `--b` (default `indi_tuned`) choose the two controllers. For each scenario the script prints a markdown table of mean ± standard deviation over seeds per metric, the ratio mean(b)/mean(a), the number of paired seeds where b is lower, the median improvement, and the exact two-sided Wilcoxon signed-rank p-value on the paired differences (the acceptance test in `bench/scenarios.md`, section 6).

## A.6 Figures

From the repository root, with plain `python3` (not `python3 -I`, because matplotlib and pyulog live in the user site-packages):

```
python3 indi_project/bench/make_figures.py
```

The script reads `results/runs/` and the reference tables in `indi_project/results/*.md`, and writes four PNGs at 150 dpi into `indi_project/report/figures/`: `fig_attitude_ratio.png`, `fig_effort_ratio.png`, `fig_act_tc_sweep.png` and `fig_rate_timeseries.png`. It prints the plotted numbers and flags any difference above 2 % from the reference tables as `DISCREPANCY`. Figure ratios are medians of per-seed paired ratios, so they can differ from the ratios of means in the tables (`report/figures/README.md`). The reference tables are committed under `indi_project/results/`.

## A.7 Known gaps

- The trajectory tables and the H4 table were produced by inline scripts that are not yet in `bench/`. Their numbers cannot be regenerated from the repository until those scripts are added.
- Seeding is partial. `--seed` controls the Gazebo sensor noise (`gz sim --seed`). The baro simulation in the PX4 SITL sensor module (`SensorBaroSim`) calls `srand(1234)` and is not seed-controlled. `run.json` records both values (`noise_seed`).
- The SITL firmware build command in A.2 is recorded in a log, not wrapped in a script.
