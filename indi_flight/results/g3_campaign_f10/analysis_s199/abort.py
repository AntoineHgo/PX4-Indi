import sys,json,numpy as np
from pyulog import ULog
d=sys.argv[1]; tstep=float(sys.argv[2]); t_from=float(sys.argv[3]) if len(sys.argv)>3 else 0
u=ULog(d+'/flight.ulg',message_name_filter_list=['sim_ground_truth','vehicle_status','vehicle_land_detected','vehicle_attitude_setpoint'])
D={x.name:x.data for x in u.data_list}; g=D['sim_ground_truth']; st=u.start_timestamp*1e-6
t=g['timestamp']*1e-6; 
print('sim_gt',len(t),'t range',t[0]-st,t[-1]-st)
q=np.stack([g[f'q[{i}]'] for i in range(4)],1)
tilt=np.degrees(np.arccos(np.clip(1-2*(q[:,1]**2+q[:,2]**2),-1,1)))
z=np.stack([g['x'],g['y'],g['z']],1)
v=np.stack([g[f'velocity[{i}]'] if f'velocity[{i}]' in g else g['x']*0 for i in range(3)],1) if 'velocity[0]' in g else None
w=np.stack([g[f'angular_velocity[{i}]'] for i in range(3)],1)
vs=D['vehicle_status']; vt=vs['timestamp']*1e-6-st
ch=[(round(vt[i],2),int(vs['nav_state'][i]),int(vs['arming_state'][i])) for i in range(len(vt)) if i==0 or vs['nav_state'][i]!=vs['nav_state'][i-1] or vs['arming_state'][i]!=vs['arming_state'][i-1]]
print('nav/arming changes',ch[:20])
ld=D.get('vehicle_land_detected')
if ld is not None:
    lt=ld['timestamp']*1e-6-st
    for k in ('landed','ground_contact','maybe_landed'):
        a=ld[k]; c=[(round(lt[i],2),int(a[i])) for i in range(len(a)) if i==0 or a[i]!=a[i-1]]; print(k,c[:12])
tt=t-st; z0=np.median(z[:800,2])
print('t  z-z0  tilt  |w|dps  xy')
for s in np.arange(max(t_from,tt[0]),tt[-1],tstep):
    i=np.searchsorted(tt,s)
    if i>=len(tt):break
    print(f'{tt[i]:7.2f} {z[i,2]-z0:7.2f} {tilt[i]:6.1f} {np.linalg.norm(np.degrees(w[i])):7.1f} {z[i,0]:6.2f} {z[i,1]:6.2f}')
