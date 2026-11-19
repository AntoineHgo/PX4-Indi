# K128 review: D-DEFAULTS-FW (S128) code against spec

Verdict: no BLOCKING. 1 MAJOR (test coverage of the wiring), 3 MINOR.

## Findings
- MAJOR, McIndiRateControl.cpp:98 / indi_rate_control_test.cpp:2255: the new test covers only the pure function indiEffectiveGainK.
  Removing or inverting the gate at the call site (`== 1`) or dropping the function call leaves the test green. The test would fail
  only if the function body were inverted/removed. Add a module-level check (or a test of the wiring) so that the module call is covered.
- MINOR, run_scenario.py:826: setdefault sits inside the o11_build() branch but outside the MC_RATE_CTL_TYPE==1 check, so PID runs also get
  MC_INDI_ID_OK 1 pushed. Harmless (module not started, MC_INDI_EN unset), but it is a stray param in PID runs. Move it under the
  `== "1"` condition if the cleaner intent is wanted. It is not recorded in meta (only the overlay), so the run record does not
  say the bench forced ID_OK 1 unless the overlay is logged.
- MINOR, run_scenario.py:826: o11_build() only detects MC_INDI_EN. A stale build with MC_INDI_EN but without MC_INDI_ID_OK would get an
  unknown param set; check how the overlay handles unknown names. Low risk after rebuild.
- MINOR, quad5in_indi_defaults.params: sets ID_OK 0 explicitly, so runs of this file fly K at 0.5x (intended, matches the spec "pre-identification set"),
  but the line 14-18 comment "yaml defaults, flown by bench unchanged" for K_R/K_P is now false for this file (effective K 10/10/5).

## Checks
1. Halving path: setGainK is called in production only at McIndiRateControl.cpp:98 inside parameters_updated(), which runs at init (line 59)
   and on every parameter_update (298-299). ID_OK is in the same ParamInt block, so a runtime ID_OK change is picked up. Other callers of
   setGainK are tests only (indi_rate_control_test.cpp, IndiInjectionStepTest.cpp:56, which set K directly by design). No autotune or injection
   path sets gains. PASS. The lead term (K x ACT_TC x LEAD) uses _gain_k, so it scales consistently.
2. Double halving or bypass: the halving happens once, on the value passed to the lib; the lib does not rescale and the param values are
   never written back, so no cumulative halving. Bypass only by ID_OK=1 (yaml max 1, so no other value). PASS.
3. run_scenario.py: for every o11 INDI run, setdefault gives ID_OK 1 unless the params file (or af_params merge, which has no ID_OK) sets it.
   The params-file value wins. PASS. See MINOR on PID runs.
4. Yaml: type int32, default 0 within 0..1, long text accurate to code. G1 defaults 1757/1640/205 within [0.001, 5000]; G2_Y 27 within
   [0, 1000]. G1_Y long text updated. PASS. Stylistic: other params carry no `|-` multi-line, check the yaml lint once (make).
   The ROMFS only has the 4040 airframe with MC_INDI params; other airframes use the new G1 defaults (per spec).
5. Unit test: fails if the function is inverted (halved vs full cases are both asserted, k values not equal to zero). It does not catch the
   wiring (see MAJOR).
