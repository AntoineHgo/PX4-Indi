import sys
from pyulog import ULog
for f in sys.argv[1:]:
    u=ULog(f); print(f.split('/')[-3])
    for t,k,v in u.changed_parameters:
        if 'EC_M' in k or 'ACT_TC' in k: print(f"  {t*1e-6:8.3f} {k} {v}")
