# S122 run validity check
Added: bench/run_validity.py `check_run(ulog, requested_params, controller, expected_rate_hz=800)`; wired in
bench/g3_run.py (`check_validity`, called in `finalize`): reads out/flight.ulg + out/g3_params.txt, stores
status["validity"] in g3_done.json, outcome "void" (returncode kept, done marker written) when invalid and the
outcome was ok/aborted. No ulog -> no validity key, behaviour unchanged.
Param compare: initial_parameters only (changed_parameters / first-arming not used). Rel tol 1e-4; missing = problem.
MC_RATE_CTL_TYPE is a boot alias mapped to MC_INDI_EN by run_scenario and is absent from the ulog: when absent it is
not compared; the MC_INDI_EN == 1 check covers it.
indi: MC_INDI_EN == 1, indi_rate_status median rate >= 0.8*800, indi_pos_status (topic of mc_indi_pos_control)
required if MC_INDI_POS_EN 1 requested. pid: no indi_rate_status samples, MC_INDI_EN != 1.
Tests (docker, host has no pytest): tests/test_run_validity.py (10) + test_g3_run.py (+2: MC_RATE_CTL_TYPE 1 in
build_run params; invalid -> void in finalize): 23 passed.
Mutation: replaced the param compare by `if False:` -> test_param_mismatch_invalid failed (22 pass, 1 fail); restored,
23 pass.
Real logs: s121 run_021 indi -> valid (EN 1, 66225 samples, 800.0 Hz). s118 run_021 "indi" -> INVALID (MC_INDI_EN 0,
no indi_rate_status). s118 pid_run021 pid (no requested params) -> valid.
Unverified: pos-module check only on fake logs (indi_pos_status name from McIndiPosControl.hpp); no live g3_run.
