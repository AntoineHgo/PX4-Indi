# K111 fixes (S111), log

F-1 done: bench/run_scenario.py gained pure fault_apply(cum_scale, ents, nom_all) and erpm_loss_split(dur, t_on, t_len, motor);
call sites use them (same outputs). New bench/tests/test_run_scenario_hooks.py (3 tests), passes.
Break-checks (temp copy in scratchpad bc1, all run), failing lines:
- motor ^1: FAIL test_split_durations_and_bitmask ... ('loss', 5.0, 0)
- wrong post duration (dur - t_on): FAIL test_split_durations_and_bitmask ... ('post', 17.0, None)
- *= -> =: FAIL test_fault_weak_motor_times_saturation {0: 0.81, 1: 0.81}; FAIL test_fault_incremental_and_rounding
- sqrt removed: FAIL test_fault_weak_motor_times_saturation {0: {'MIN': 52, 'MAX': 518}, ...}
F-3 done (UNVERIFIED in a live gz run, syntax only): disturbance.py counts vel-None ticks and the first valid velocity sim time,
writes disturbance_summary.json (gust_x only; at first valid vel, at profile end, at exit) and the disturbance.log exit line;
run_scenario.py merges it into run.json["disturbance"]["injector"] after cleanup.
F-5 done: g3_sample.py timeline note now says main-segment (traj/stick) anchor; wind dir_deg frame documented (gz world, ENU, air moves TO).
Harness: audited every tests/*.py; all already exit non-zero on failure (asserts, or fails counter + sys.exit). Verified by breaking
one check in test_hole_report.py (rc 1) and test_applied_timing.py (rc 1) in a temp copy. t184_probe*.py are scratch probes with no checks.
No test file changed besides the new one. Loop over tests/*.py prints nothing.
