T190 impl log (S90)
- read note s1-3,6,7, review, module code; wrote IndiInjectionStep.{hpp,cpp} (call-site step), edited McIndiRateControl.{cpp,hpp}, CMakeLists.txt, params yaml (INJ_PT, INJ_RAMP), msg/IndiRateStatus.msg (3 fields), IndiInjectionStepTest.cpp
- amended note: appended section 8 to attitude_break_s86.md (both MAJORs, accepted/rejected MINORs)
- tests: `indi_project/docker/run.sh ... 'make tests TESTFILTER=IndiInjection'` -> 2/2 suites pass (IndiInjection, IndiInjectionStep: 5 tests). First run failed on a test-side float rounding (x-sp vs d), fixed in the test.
- BREAK 1: law call changed to indi.update(rates, rates_sp, ...) (un-injected y) -> RateSetpointBreakFeedsLawTheInjectedSetpoint FAILED (1 of 2 suites). Restored (diff vs backup empty).
- BREAK 2: injection computed after indi.update (law saw y) -> same test FAILED. Restored.
- re-run after restore: 100% pass (2/2).
- full `make px4_sitl_default` in docker: built OK (module compiles, 1457/1457), linked bin/px4. No SITL flight run.
- astyle (Tools/astyle/fix_code_style.sh in docker) on 5 changed C++ files: Unchanged.
- bench: attitude_break_check.py + tests/test_attitude_break_check.py: 6/6 ok (good log passes; law-fed-y fails rate_sp_dot and response checks; fault in window fails; yaw SKIP). Host python3 -I.
- zero diff on mc_rate_control, mc_att_control, mc_pos_control, control_allocator, commander, control_allocation lib.
NOT DONE: no SITL flight, no bit-identical AX=0 log diff against the old build, attitude_break_check.py not run on a real ulog (field names rates_sp_*[i] from the msg are an assumption of pyulog naming), no ratesp_csv.py extractor, no docs/params doc.
