#!/bin/sh
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=indi_flight/results/g4_chatter_probe_s175
indi_project/docker/run.sh -n s175build -t 3000 -- make px4_sitl_default > $D/build.log 2>&1
echo "BUILD_RC $?" >> $D/build.log
sh indi_flight/bench/gate_g4.sh fly $D typ hover 1 > $D/fly.out 2>&1
mv $D/hover_typ_s1 $D/hover_typ_s1_tmp 2>/dev/null; mv $D/hover_typ_s1_tmp $D/hover_typ_s1 2>/dev/null
touch $D/FLY_DONE
