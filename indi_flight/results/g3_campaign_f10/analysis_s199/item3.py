import sys,json
sys.path.insert(0,'.')
from extract import out
SP={'horizontal':0.16,'altitude':1.0,'attitude':0.26}
res=[]
for i,r in sorted(out.items()):
    if 'item3' not in r['f1']+r['f2']: continue
    c1=r['c1']['item3_steady_state']; c2=r['c2']['item3_steady_state']
    d=r['draw']['draw']['factors']
    print(f"### {i} mode={c1.get('mode',r['c1']['mode'])} wind={r['c1']['wind']} sag={r['c1']['sag']} win={r['c1']['window_s']} sat={d['saturation']['on']} weak={d['weak_motor']['on']} sagon={d['thrust_sag']['on']}")
    for k in ('horizontal_rms_m','altitude_mean_m','roll_pitch_mean_deg'):
        v=c1[k]; print('  k1',k,v)
    print('  k2',{k:c2[k] for k in ('horiz_rms_m','alt_mean_m','roll_mean_deg','pitch_mean_deg','limits','pass')})
