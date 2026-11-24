cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
R=indi_flight/results/g3_refly_actc_s212; B=indi_flight/results/g3_refly_actc_s212/restore264/blend264_s223
for n in q1_bld010 q2_bld005; do
 f=$B/$n/run_024/flight.ulg
 echo "== $n"; python3 $R/restore264/scripts/tilt.py $f
 cut=$(python3 - $f <<'P'
import sys
from pyulog import ULog
u=ULog(sys.argv[1]); pt=[x[0]*1e-6 for x in u.changed_parameters if 'EC_MAX' in x[1]]
print(min(pt)-u.start_timestamp*1e-6)
P
)
 echo cut=$cut
 python3 indi_flight/bench/g3_item2_split.py $B/$n/run_024 --cut $cut --json $B/$n/split.json | tail -30
done
python3 $R/restore264/scripts/tilt.py $R/speed1_s213/indi_024/run_024/flight.ulg
