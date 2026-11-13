# impl log: bench/tune.py (session 7)

- Step 1: read spec, run_batch.sh, runner notes. Defaults verified in yaml (no gz_x500 airframe override of MC_* params):
  rate P/I/D roll,pitch 0.15/0.2/0.003, yaw rate P/I 0.2/0.1, MC_ROLL_P/PITCH_P 4.0, MC_YAW_P 2.8,
  INDI K_R/K_P 20, K_Y 10, ACT_TC 0.02. MC_YAW_P max is 5 (span 2 would exceed): tune.py clamps to yaml min/max.
- Step 2: run_batch.sh got env overrides PARAMS_FILE, RESULTS_DIR, FLAT_LAYOUT, NAME_TAG (all unset = old behaviour).
- Step 3: wrote tune.py; dry-run OK both families. Starting smoke runs (indi then pid).
- Step 4: smoke OK. indi J: c00 1.0446, c01 0.8761; pid J: c00 1.0164 (center, vs ref=1.0 -> run-to-run noise ~1.6%), c01 1.0503. No failures.
