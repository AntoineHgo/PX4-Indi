import sys; from common import *
from pyulog import ULog
kind,r,f0,t1,t2,win=sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4]),float(sys.argv[5]),float(sys.argv[6])
ax=sys.argv[7] if len(sys.argv)>7 else 'y'
u=ULog(f'{R}{kind}_{r}/run_{r}/flight.ulg')
g=lambda n:[d for d in u.data_list if d.name==n and d.multi_id==0][0].data
tsim=lambda d:d['timestamp'].astype(float)*1e-6
ts0=tsim(g('vehicle_angular_velocity'))[0]
tg=np.arange(0,tsim(g('vehicle_angular_velocity'))[-1]-ts0,1/FS)
rs=lambda d,k:np.interp(tg,tsim(d)-ts0,d[k])
i={'x':0,'y':1,'z':2}[ax]
w=rs(g('vehicle_angular_velocity'),f'xyz[{i}]')
rsp=rs(g('vehicle_rates_setpoint'),['roll','pitch','yaw'][i])
at=g('vehicle_attitude');q=[rs(at,f'q[{j}]') for j in range(4)];ro,pi_=eul(q);att=[ro,pi_][min(i,1)]
asp=g('vehicle_attitude_setpoint');qd=[rs(asp,f'q_d[{j}]') for j in range(4)];rosp,pisp=eul(qd);attsp=[rosp,pisp][min(i,1)]
tq=rs(g('vehicle_torque_setpoint'),f'xyz[{i}]')
m=np.array([rs(g('actuator_motors'),f'control[{j}]') for j in range(4)])
try: tm=rs(g('actuator_torque_measured'),f'torque[{i}]')
except Exception: tm=None
gt=g('vehicle_local_position_groundtruth'); alt=-np.interp(tg,tsim(gt)-ts0,gt['z'])
print(kind,r,'log t0 sim',ts0,'end sim',tg[-1]+ts0)
print('sim_t | w amp dps | wsp | att deg | attsp | tsp | tmeas | g_w(w/wsp) ph | g_att ph | g_tm ph | mmax mmin  satHi satLo | alt')
d=np.degrees
for t in np.arange(t1,t2,win):
    a,b=int((t-ts0)*FS),int((t+win-ts0)*FS)
    if a<0 or b>len(tg): continue
    am=lambda x:abs(fit(tg,x,f0,a,b))
    gw=gp(tg,w,rsp,f0,a,b);ga=gp(tg,att,attsp,f0,a,b)
    gm=gp(tg,tm,tq,f0,a,b) if tm is not None else (0,0)
    mm=m[:,a:b]
    print(f"{t:5.1f} | {d(am(w)):6.1f} {d(am(rsp)):6.1f} | {d(am(att)):5.2f} {d(am(attsp)):5.2f} | {am(tq):.4f} {am(tm) if tm is not None else 0:.4f} | {gw[0]:.2f} {gw[1]:5.0f} | {ga[0]:.2f} {ga[1]:5.0f} | {gm[0]:.2f} {gm[1]:5.0f} | {mm.max():.2f} {mm.min():.2f} {np.mean((mm>.98).any(0)):.2f} {np.mean((mm<.02).any(0)):.2f} | {alt[a:b].mean():.1f}")
