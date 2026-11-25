# ALIGN_S227: key 1 / key 2 aligned on G3 items 2, 5, 6 (D-G3-KEYS-S227). No flights, not committed.
Tests: all in bench/tests/test_g3_align_s227.py (new, 3 tests). Fail-before = same file run against HEAD versions of both scorers.

1. Key 1 item 2 position limit cycle, bench/g3_checks.py (evaluate: new kwarg hold_win ~:338; use ~:388; main() passes it ~:531)
   - hold_win = [hold t, hold t + dur] from windows_from_run_json()["hold"] (run.json `hold` event). Windows: 3 x 10 s from
     max(airborne start, hold start) to min(airborne end, hold end). Without hold_win (old --t0/--t1) behaviour is unchanged.
   - Test test_key1_position_limit_cycle_windows_start_at_hold: 0.8 m p2p sine through a 30 s hold -> sustained, 3 windows;
     only the last 2 hold windows oscillate -> not sustained.
   - Before: TypeError (evaluate has no hold_win). The old window rule (one window from the last 10 s) is shown by RECONCILE_S227,
     not re-measured here. After: pass.
2. Key 2 item 6, bench/g3_checks_key2.py rate_hold (~:321)
   - pass = every axis RMS (p, q, r) <= 5 deg/s; vector RMS kept as rate_rms_dps (reported only), axis_rms_dps as before.
   - Test test_key2_item6_gates_per_axis: 4 dps constant on each axis (vector 6.98, axes 4.03) must pass; 6 dps on one axis must fail.
   - Before: FAIL (pass False on the 4/4/4 case, vector 6.98 > 5). After: pass.
3. Key 2 item 5, attitude (stick) mode, bench/g3_checks_key2.py recovery (~:294-299)
   - Reference tilt = commanded q_d at the same time (last q_d sample at or before each time), in both modes; the 2 s pre-event
     median is removed. No q_d in the log -> reference missing -> fails closed (the existing valid < 0.5 branch). Written from the
     decision text, not copied from key 1.
   - Test test_key2_item5_stick_reference_is_commanded_attitude: q_d steps to 10 deg at the event; vehicle follows -> pass;
     vehicle stays level -> fail.
   - Before: FAIL (follow case failed: 10 deg vs pre-event median never within 3 deg). After: pass.

Results after (venv /tmp/g3venv, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1): test_g3_checks_s226 10, test_g3_checks_key2_s226 15,
test_g3_checks_key2_q14_q15 4, test_g3_run 19, test_g3_align_s227 3: all passed; key 2 --self-test 17 PASS 0 FAIL.
Unverified: no real G3 log; key 2 stick-mode loads q_d from vehicle_attitude_setpoint (g3_checks_key2.py ~:393) and that
topic's presence in G3 stick logs was not checked. Key 1 position-limit-cycle window end at the hold end (not flight end) is my choice.
