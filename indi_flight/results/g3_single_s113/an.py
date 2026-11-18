import sys,numpy as np
from pyulog import ULog
u=ULog(sys.argv[1]+"/flight.ulg")
def g(n):
    return next(d for d in u.data_list if d.name==n and d.multi_id==0)
t0=u.start_timestamp
def ts(d): return (d.data['timestamp']-t0)*1e-6
def at(d,key,t,sign=1):
    x=ts(d); i=np.argmin(abs(x-t)); return d.data[key][i]
try:
    lp=g('vehicle_local_position_groundtruth'); print('gt')
except StopIteration:
    lp=None
est=g('vehicle_local_position')
print('names',[d.name for d in u.data_list if 'ground' in d.name or 'thrust' in d.name or 'land' in d.name or 'status'==d.name])
for t in (10,30,45,50,52,53,54,55.5):
    s=f"t={t}: est_alt={-at(est,'z',t):.2f} vz={at(est,'vz',t):.2f}"
    if lp is not None: s+=f" gt_alt={-at(lp,'z',t):.2f}"
    print(s)
th=g('vehicle_thrust_setpoint'); 
for t in (10,30,45,50,52,53,54): print('thr',t,at(th,'xyz[2]',t))
st=g('vehicle_status'); x=ts(st); 
prev=None
for i,v in enumerate(st.data['nav_state']):
    if v!=prev: print('nav_state',round(x[i],2),v, 'arm',st.data['arming_state'][i]); prev=v
try:
    ld=g('vehicle_land_detected'); x=ts(ld); p=None
    for i in range(len(x)):
        k=(ld.data['landed'][i],ld.data['maybe_landed'][i],ld.data['freefall'][i])
        if k!=p: print('land',round(x[i],2),k); p=k
except StopIteration: print('no land det')
