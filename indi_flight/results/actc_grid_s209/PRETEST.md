# ACT_TC grid pre-test (S209)
Commands (repo root): `python3 indi_flight/bench/actc_grid.py --out indi_flight/results/actc_grid_s209 --cells pretest`
(`--list` shows the 30 cells, `--dry-run` the commands). Per cell: run.sh (px4-indi-sim) run_scenario hover quad5in v2 speed 4,
inj roll AX 1 (as pos0), ID_OK 0, `--model-variant tau_up=,tau_down=`, `--dly-act`; then ident_actc.py --t0 24 --t1 76 --rpm-max 25783 (2700 rad/s, not in the log; gain fits 1.000).
Third flight t1_a3d_d0f3 (marginal cell, flown to test the frames hook).

| cell | true up/down ms | est up/down/sym ms | est delay ms | sym/slow, sym/mean | flags |
|---|---|---|---|---|---|
| t1 a1 (0,0) | 33/33 | 33.6/32.4/33.0 | 1.8 | 1.00, 1.00 | none, PASS |
| t3 a3d (10,3) | 33/99 | 33.9/96.1/59.4 | 11.7 | 0.60, 0.90 | none, PASS |
| t1 a3d (0,3) extra | 11/33 | 11.2/32.4/20.2 | 1.7 | 0.61, 0.92 | none, PASS |

Checks: flies, lands, 82 s log: PASS. Injector: motor std 0.007-0.009 at 25-50 s (cmd 0.105-0.163 about 0.137): PASS.
actuator_motors 800 Hz, esc_status 800 Hz median but 4-8 % fewer samples (gaps up to 5 ms): PASS (aligner handles it).
Plant variant: model_variant SDF has timeConstantUp/Down 0.033/0.099 x4 and the fit recovers up/down within 3 %: PASS.
--dly-act 10: gz_bridge log releases at age 10.0 ms in the window, fit delay 11.7 vs 1.8 ms base (+9.9): PASS (the first
release applies 50 ms once, and 1-30 % of commands are skipped before t=40 s; "output calls irregular" message; harmless here).
**SIM_GZ_ERPM_LAT (frames): FAIL, not applied.** gz_bridge reads it only in the constructor (GZMixingInterfaceESC.hpp:66);
a --params file is set after boot (log "curr 0 -> new 3") and a docker `-e PX4_PARAM_` is dropped (run_scenario builds env from
gz_env.sh). Fit delay: 1.75 ms at 3 frames vs 1.82 at 0 (3 frames would add 3.75 ms). Only scenario `sim_params` works (v2_lat_*),
no CLI. Stopped as instructed; the driver still writes the line (documented in params_text). Same issue likely hits g3_run.py
tel_latency (params file): to verify, it would void the frames factor of earlier G3 runs.
Thresholds vs SITL residuals (4 motors/cell): norm residual 0.014-0.038 vs 0.35, se(ln tau) 0.001 vs 0.10, se delay 0.005 vs 1.5
samples: wide margins. Structure 0.076-0.080 (cell 1), 0.11-0.15 (cell 2) vs MAX_STRUCTURE 0.08: would wrongly FAIL; only saved
by the MIN_NORM_FOR_STRUCTURE 0.05 gate (norm 0.014-0.038, closest 0.038). Remark: structure is a quantisation/timing
artefact at tiny residual; tighter SITL cases (more noise, G4 vib) can pass norm 0.05 with structure above 0.08.
Wall time: flight 41 s + ident ~40 s = ~80 s per cell (28 cells ~ 37 min).
Remaining cells (27 left, skips done): `python3 indi_flight/bench/actc_grid.py --out indi_flight/results/actc_grid_s209`
Frames cells (15 of 30) are NOT valid until ERPM_LAT is applied at boot (owner decision: scenario sim_params shim).

## Frames fix
Driver now writes `<cell>/run_cell.py` (registers scenario hover_latN = hover + sim_params SIM_GZ_ERPM_LAT N, then runs the stock run_scenario.py). Old frames>0 folders kept as *_noframes, rows in GRID_noframes.tsv.
Re-fly t1_a3d_d0f3_s1: log param SIM_GZ_ERPM_LAT = 3 at start, no params-file line, but fitted delay 1.73 ms vs 1.82 (t1_a1_d0f0): rise about 0 ms, expected +3.75. STEP 3 FAILED, the 27-cell grid was NOT launched.
Cause not found (param value is 3 in the log; code path GZMixingInterfaceESC.cpp:262-265 reads as designed): next, compare esc_status instance 0 vs 1 (true rotor speed) lag, or run a v2_lat_att scenario. g3_run.py tel_latency: YES, params-file path (g3_run.py:143 params["SIM_GZ_ERPM_LAT"], written to --params; no sim_params or overrides), so G3 frames were probably not applied either.
