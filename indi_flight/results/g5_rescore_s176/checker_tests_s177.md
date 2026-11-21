# Checker self-tests, S177 (key2 MINOR findings 1 and 2)
- g511: tests/test_g511_check.py::test_check_run_subtracts_p95 runs check_run end to end (load patched, synthetic flight): no-event steps 0.8 deg, event 1.5 deg -> p95 0.8, excess 0.7, verdict PASS, legacy FAIL.
- g510: g510_check.py gets tilt_limit_from_params() (the former inline MPC_TILTMAX_AIR read, same logic); main() now prints WARNING and records out["tilt_limit_warning"] when the param is missing (fallback still 20 deg).
- tests/test_g510_check.py: non-default 45 -> limit 45+margin and used by analyse (48 deg passes); change before SAT wins; missing -> None limit, warning, 48 deg fails at default 20.
- Break checks: `excess = tilt` (no p95) -> g511 test fails (excess 1.5, verdict FAIL); param read forced to None -> g510 test fails; both restored.
- No threshold, scoring rule or verdict logic changed; firmware, GATES.md, STATE.md, indi_project untouched; not committed.
- Command: cd indi_flight/bench && python3 tests/test_g510_check.py && python3 tests/test_g511_check.py  (no pytest on host; both pass).
