cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
f=indi_flight/results/g3_refly_actc_s212/restore264/ref264_s224/pid_024/run_024/flight.ulg
python3 indi_flight/results/g3_refly_actc_s212/restore264/scripts/tilt.py $f
cut=$(python3 - $f <<'P'
import sys
from pyulog import ULog
u=ULog(sys.argv[1]); pt=[x[0]*1e-6 for x in u.changed_parameters if 'EC_MAX' in x[1]]
print(min(pt)-u.start_timestamp*1e-6)
P
)
echo cut=$cut
python3 indi_flight/bench/g3_item2_split.py indi_flight/results/g3_refly_actc_s212/restore264/ref264_s224/pid_024/run_024 --cut $cut --json indi_flight/results/g3_refly_actc_s212/restore264/ref264_s224/pid_024/split.json | tail -30
