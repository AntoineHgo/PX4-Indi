#!/usr/bin/env bash
# S62: unit tests with the yaw-toggle fix, then break-check (fix removed), then restore. Run from repo root.
O=indi_flight/results/stage3_s62; F=src/lib/indi_rate_control/indi_rate_control.cpp
cp $F $O/.fixed.cpp.bak
indi_project/docker/run.sh -n s62t1 -c 6 -t 2400 -- make tests 'TESTFILTER=[iI]ndi' > $O/tests_fixed.log 2>&1; echo "fixed rc=$?" > $O/yaw_toggle_check.txt
python3 - <<'PY'
p='src/lib/indi_rate_control/indi_rate_control.cpp'; s=open(p).read()
s=s.replace("\n\t// the yaw setpoint entering the derivative switches between raw and filtered: restart the derivative\n\t_sp_lead_reset = true;\n","\n",1); open(p,'w').write(s)
PY
indi_project/docker/run.sh -n s62t2 -c 6 -t 2400 -- make tests 'TESTFILTER=[iI]ndi' > $O/tests_broken.log 2>&1; echo "broken rc=$?" >> $O/yaw_toggle_check.txt
cp $O/.fixed.cpp.bak $F && rm $O/.fixed.cpp.bak
grep -c "YawFilterToggleGivesNoDerivativeImpulse" $O/tests_broken.log >> $O/yaw_toggle_check.txt
echo DONE >> $O/yaw_toggle_check.txt
