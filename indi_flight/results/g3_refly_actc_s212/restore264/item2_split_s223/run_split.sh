cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
R=indi_flight/results/g3_refly_actc_s212/restore264
O=$R/item2_split_s223; mkdir -p $O
for p in indi_joint pid_joint falsifier_s222/p1_bld015 falsifier_s222/p2_nomeas; do
 n=$(echo $p | tr / _)
 cut=$(python3 - $R/$p/run_024/flight.ulg <<'P'
import sys
from pyulog import ULog
u=ULog(sys.argv[1]); pt=[x[0]*1e-6 for x in u.changed_parameters if 'EC_MAX' in x[1]]
print(min(pt)-u.start_timestamp*1e-6)
P
)
 echo "$n cut(ulog-start base)=$cut"
 python3 indi_flight/bench/g3_item2_split.py $R/$p/run_024 --cut $cut --json $O/split_$n.json >/dev/null 2>$O/stderr_$n.txt
done
