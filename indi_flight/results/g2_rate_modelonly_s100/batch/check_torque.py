"""S100 model-only check for one flight log.

Passes only if: indi_rate_status.measured_torque_in_use is 0 on every sample,
no actuator_torque_measured topic is logged, and MC_INDI_W_MAX is logged as 0.
Prints one summary line and MODEL_ONLY_VERIFIED / MODEL_ONLY_FAIL. Exit 0 on pass.
"""
import sys

import numpy as np
from pyulog import ULog

path = sys.argv[1]
ul = ULog(path, ["indi_rate_status"])
rs = [d for d in ul.data_list if d.name == "indi_rate_status"]
if not rs:
    print("MODEL_ONLY_FAIL no indi_rate_status topic")
    sys.exit(2)
mt = np.asarray(rs[0].data["measured_torque_in_use"])
params = ul.initial_parameters
wmax = params.get("MC_INDI_W_MAX")
ca = params.get("CA_R_W_MAX")

full = ULog(path)
has_meas = any(d.name == "actuator_torque_measured" for d in full.data_list)

nonzero = int(np.count_nonzero(mt))
ok = mt.size > 0 and nonzero == 0 and not has_meas and wmax == 0.0
print(f"samples {mt.size} measured_torque_in_use_nonzero {nonzero} "
      f"actuator_torque_measured_topic {has_meas} MC_INDI_W_MAX {wmax} CA_R_W_MAX {ca}")
print("MODEL_ONLY_VERIFIED" if ok else "MODEL_ONLY_FAIL")
sys.exit(0 if ok else 1)
