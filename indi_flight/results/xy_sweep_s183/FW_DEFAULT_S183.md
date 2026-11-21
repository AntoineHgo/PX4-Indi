# FW default MC_INDI_XY_VP 3.6 -> 2.4 (D-XY-PICK, S183)

Not committed.

## Diff
```
 indi_flight/bench/g2_outer_model_s164.py                        | 2 +-
 indi_flight/bench/margins_models.py                             | 4 ++--
 indi_flight/bench/tests/test_att_model.py                       | 6 +++---
 src/modules/mc_indi_pos_control/mc_indi_pos_control_params.yaml | 2 +-
 4 files changed, 7 insertions(+), 7 deletions(-)
-    ap.add_argument("--params", default=None, help="params file with MC_INDI_XY_P / MC_INDI_XY_VP (firmware defaults 1.2 / 3.6 when absent)")
+    ap.add_argument("--params", default=None, help="params file with MC_INDI_XY_P / MC_INDI_XY_VP (firmware defaults 1.2 / 2.4 when absent)")
-XY_GAINS_INDI = dict(Kp=1.2, Kv=3.6)  # firmware defaults (freeze-8); tests/test_att_model.py checks the yaml
+XY_GAINS_INDI = dict(Kp=1.2, Kv=2.4)  # firmware defaults (freeze-8); tests/test_att_model.py checks the yaml
-    MC_INDI_XY_P / MC_INDI_XY_VP (firmware defaults 1.2 / 3.6 when absent).  legacy_mpc=True evaluates the old MPC_XY_P /
+    MC_INDI_XY_P / MC_INDI_XY_VP (firmware defaults 1.2 / 2.4 when absent).  legacy_mpc=True evaluates the old MPC_XY_P /
-    """Since 7dd352bae2 the xy outer model default is MC_INDI_XY_P / MC_INDI_XY_VP (1.2 / 3.6 since freeze-8), not
+    """Since 7dd352bae2 the xy outer model default is MC_INDI_XY_P / MC_INDI_XY_VP (1.2 / 2.4 since D-XY-PICK), not
-    assert M.xy_gains() == dict(Kp=1.2, Kv=3.6)
+    assert M.xy_gains() == dict(Kp=1.2, Kv=2.4)
-    O = 1 + 3.6 / s + 1.2 * 3.6 / s ** 2 + 0.4 / s ** 2 + 0.4 * 1.2 / s ** 3 + 0.2 / (1 + s / (2 * math.pi * 5.0))
+    O = 1 + 2.4 / s + 1.2 * 2.4 / s ** 2 + 0.4 / s ** 2 + 0.4 * 1.2 / s ** 3 + 0.2 / (1 + s / (2 * math.pi * 5.0))
-      default: 3.6
+      default: 2.4
```

## Bench tests
pytest not installed on host; ran per gate_g1 fallback: python3 indi_flight/bench/tests/test_att_model.py
```
PASS test_identity_indi
PASS test_identity_pid
PASS test_limit_att_p_zero
PASS test_dc_closed_rate_loop_is_unity
PASS test_ideal_rate_loop_integrator_margins
PASS test_outer_factor
PASS test_outer_factor_uses_mc_indi_xy_gains
PASS test_model_xy_defaults_match_firmware_yaml
```

## Build
No flight container running (docker ps empty). indi_project/docker/run.sh -n build_s183 -t 3000 'make px4_sitl_default': rc=0, [431/431] Linking bin/px4.

## Metadata
```
14415:    <parameter name="MC_INDI_XY_VP" default="2.4" type="FLOAT">
14416-      <short_desc>Horizontal velocity P gain</short_desc>
14405:    <parameter name="MC_INDI_XY_P" default="1.2" type="FLOAT">
14406-      <short_desc>Horizontal position gain</short_desc>
```
Unchanged by design: historical records (results/, README param notes saying 1.2/3.6).
