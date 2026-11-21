# G5.5 D-OFFB-POSVEL firmware: MC_INDI_XY_P / MC_INDI_XY_VP (S176)
Diff (src/modules/mc_indi_pos_control/, 3 files, +26/-4): mc_indi_pos_control_params.yaml (+22, two params, defaults 1.9 / 3.6 1/s, ranges 0..10 / 0..20),
McIndiPosControl.hpp (2 param declarations swapped MPC_XY_P -> MC_INDI_XY_P, MPC_XY_VEL_P_ACC -> MC_INDI_XY_VP), McIndiPosControl.cpp (2 lines, setPositionGains/setVelocityGains x,y).
z, I, D gains unchanged. grep: no other reader of MPC_XY_P / MPC_XY_VEL_P_ACC in the module. Zero diff outside the module not touched by this work.
Format: Tools/astyle/check_code_style.sh on .cpp and .hpp in Docker, rc 0 both.
Build: `make px4_sitl_default` in Docker, BUILD_RC 0 (build.log).
Tests: `make tests TESTFILTER=Indi` in Docker, 9/9 pass (tests.log; includes IndiPosInjection, IndiStageMode, accel-control and rate tests). No test covers the new wiring; the flight is the check.
Flight: fly_fwdef.sh = fly_gx1.sh with --out indi_o1_s1_fwdef, params_gx1.params (no MC_INDI_XY_* nor MPC_XY gain override), rc 0.
Scored: g55_check.py --json + an.py (indi_o1_s1_fwdef.check_an.txt).
| run | horiz RMS | vert RMS | verdict |
|---|---|---|---|
| gx1 (MPC 0.95/1.8) | 0.587 m | 0.035 | FAIL |
| fwdef (MC_INDI_XY defaults) | 0.297 m | 0.038 | PASS |
| gx2 probe (MPC 1.9/3.6) | 0.289 m | - | PASS |
Also: max_h 0.477 m, tilt max 43.6 deg, no line above 2 Hz (rate peaks 0.67-0.79 Hz), motors 0.112-0.187.
Params in ulog: MPC_XY_P 0.95 / MPC_XY_VEL_P_ACC 1.8 are logged as non-default; MC_INDI_XY_P/VP are default so they appear only in the
default-parameter records (value bytes 1.9 / 3.6 seen by raw grep; pyulog initial_parameters does not list defaults). RMS 0.297 vs 0.587 proves wiring.
Unverified: single seed, o1 only; 0.297 vs 0.289 difference is run-to-run (different firmware build), not separated.
