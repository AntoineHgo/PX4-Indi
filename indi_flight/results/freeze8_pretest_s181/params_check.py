import sys
from pyulog import ULog
for p in sys.argv[1:]:
    u = ULog(p, disable_str_exceptions=True); d = u.initial_parameters
    print(p, {k: d.get(k) for k in ("MC_INDI_XY_P", "MC_INDI_XY_VP", "MC_INDI_ACT_TC", "MC_INDI_POS_EN")})
