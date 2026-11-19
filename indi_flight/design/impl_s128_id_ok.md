# S128 impl: MC_INDI_ID_OK gate and quad5in defaults (D-DEFAULTS-FW)
Plan: yaml param + defaults; lib pure fn indiEffectiveGainK; module call; gtest + break check; airframe W_MAX 2700 (SIM_GZ_EC_MAX1..4 = 2700 found);
bench run_scenario overlay.setdefault MC_INDI_ID_OK 1; params file ID_OK 0; docker build/test; make format.
## Steps
- edits applied (yaml, lib fn+test, module, airframe, run_scenario setdefault, params file)
- unit tests (make tests TESTFILTER=indi_rate_control, docker): 70 tests pass, 8 suites, incl. new EffectiveGainKIdentStatus.
- break check: function changed to `return k_set;` -> ctest unit-indi_rate_control_test FAILED; restored (hpp has the 0.5f again).
- px4_sitl_default build (docker): OK (714/714).
- format: Tools/astyle/fix_code_style.sh on 4 C++ files: Unchanged.
- files changed: 4040_gz_quad5in, bench/params/quad5in_indi_defaults.params, bench/run_scenario.py (overlay.setdefault MC_INDI_ID_OK "1" in o11 branch; a params file value wins),
  lib hpp + test, McIndiRateControl.cpp/.hpp, mc_indi_rate_control_params.yaml, this note. (DECISIONS.md/STATE.md were already modified before.) G1 max 5000, G2_Y max 1000: admit values, unchanged.
- UNVERIFIED: bench run with ID_OK (no flight run); params.xml containing ID_OK not inspected; module-level unit tests (IndiInjection etc.) not run separately; no lib test hard-coded old defaults (kG1True=100 used); g3_run.py not changed (goes through run_scenario).
