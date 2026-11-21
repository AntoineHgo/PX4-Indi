cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
for n in hover_harsh_s1 hover_harsh_s2 hover_harsh_s3 hover_typ_s2 hover_quiet_s1; do
python3 -c "
import json;e=[e for e in json.load(open('indi_flight/results/g4_gate_s169/$n/run.json'))['events'] if e['name']=='hold'][0];end=e['t_us']*1e-6+e['dur_s'];print(end-10,end)" | { read a b
python3 indi_flight/bench/g3_checks.py indi_flight/results/g4_gate_s169/$n/flight.ulg --t0 $a --t1 $b 2>/dev/null | python3 -c "
import json,sys;o=json.load(sys.stdin)['item2_oscillation'];print('$n noskip pqr sustained',[o[k]['sustained'] for k in 'pqr'],[o[k]['lines'] for k in 'q'])"; }
done
