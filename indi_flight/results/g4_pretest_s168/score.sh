#!/bin/sh
# Score the G4 pre-test with bench/g4_metrics.py; window from run.json (absolute us) minus ulog start_timestamp.
O=indi_flight/results/g4_pretest_s168
for d in hoverL_quiet_s1:hold:5 hoverL_harsh_s1:hold:5 lemn_typ_s1:traj:3; do
  n=${d%%:*}; rest=${d#*:}; ev=${rest%%:*}; skip=${rest#*:}
  w=$(python3 -c "
import json; from pyulog import ULog
u=ULog('$O/$n/flight.ulg',['vehicle_status']); s=u.start_timestamp
e=[e for e in json.load(open('$O/$n/run.json'))['events'] if e['name']=='$ev'][0]
t=(e['t_us']-s)*1e-6; print('%.2f %.2f'%(t+$skip, t+e['dur_s']))")
  set -- $w
  python3 indi_flight/bench/g4_metrics.py $O/$n/flight.ulg --t0 $1 --t1 $2 --json $O/$n/g4_metrics.json > /dev/null
  python3 -c "
import json; d=json.load(open('$O/$n/g4_metrics.json'))
print('$n', d['window_s'], 'truth', d['rotor_speed_is_truth'], 'R20 %.3f%% R4 %.3f%% C20 %.5f C4 %.5f clip %.4f hover %.0f' % (d['R20']['mean_pct_hover'], d['R4']['mean_pct_hover'], d['C20']['mean'] if 'mean' in d['C20'] else sum(d['C20']['per_motor'])/4, d['C4']['mean'] if 'mean' in d['C4'] else sum(d['C4']['per_motor'])/4, d['clip_fraction'], d['hover_speed_rad_s']))"
done
