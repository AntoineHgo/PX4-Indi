import sys,numpy as np
from pyulog import ULog
u=ULog(sys.argv[1]+"/flight.ulg"); end_sim=float(sys.argv[2])
def g(n): return next(d for d in u.data_list if d.name==n and d.multi_id==0)
gt=g('vehicle_local_position_groundtruth'); th=g('vehicle_thrust_setpoint'); st=g('vehicle_status')
t0=min(d.data['timestamp'][0] for d in u.data_list)
tend=gt.data['timestamp'][-1]; off=end_sim-(tend-0)*1e-6
print('ulog_start_us',u.start_timestamp,'t0',t0,'gt_end_us',tend,'log_end_sim?',end_sim,'offset',off)
tg=gt.data['timestamp']*1e-6; tt=th.data['timestamp']*1e-6
for t in np.arange(24,end_sim-off+0.1,2 if len(sys.argv)<4 else 1):
    i=np.argmin(abs(tg-t)); j=np.argmin(abs(tt-t))
    print(f"ulog {t:.0f} (sim~{t+off:.1f}) gt_alt={-gt.data['z'][i]:.2f} vz={-gt.data['vz'][i]:.2f} thr={-th.data['xyz[2]'][j]:.3f}")
for t in (end_sim-off-4,end_sim-off-3,end_sim-off-2,end_sim-off-1,end_sim-off-.2):
    i=np.argmin(abs(tg-t)); j=np.argmin(abs(tt-t)); print(f"last {t:.1f} (sim {t+off:.1f}) alt={-gt.data['z'][i]:.2f} thr={-th.data['xyz[2]'][j]:.3f}")
for k in ('timestamp','nav_state'): pass
x=st.data['timestamp']*1e-6; p=None
for i,v in enumerate(st.data['nav_state']):
    if v!=p and x[i]>0: print('nav',round(x[i],2),'sim',round(x[i]+off,2),v); p=v
