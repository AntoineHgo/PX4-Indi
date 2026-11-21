import sys, numpy as np
from pyulog import ULog
f=sys.argv[1]; u=ULog(f,['vehicle_angular_velocity','vehicle_rates_setpoint','vehicle_attitude_setpoint','trajectory_setpoint','vehicle_status'])
t0=u.start_timestamp
g=lambda n:[d for d in u.data_list if d.name==n][0].data
av=g('vehicle_angular_velocity'); t=(av['timestamp']-t0)/1e6; q=np.degrees(av['xyz[1]'])
sp=g('vehicle_rates_setpoint'); ts=(sp['timestamp']-t0)/1e6; qs=np.degrees(sp['pitch'])
tr=g('trajectory_setpoint'); tt=(tr['timestamp']-t0)/1e6
for a in np.arange(float(sys.argv[2]),float(sys.argv[3]),0.5):
    m=(t>=a)&(t<a+1); ms=(ts>=a)&(ts<a+1); mt=(tt>=a)&(tt<a+1)
    vx=tr['velocity[0]'][mt]; px=tr['position[0]'][mt]
    print(f"{a:5.0f} q std {q[m].std():5.2f} qsp std {qs[ms].std():5.2f} traj n {mt.sum():3d} px {np.nanmean(px) if mt.sum() else np.nan:7.3f} vx {np.nanmean(vx) if mt.sum() else np.nan:6.3f}")
