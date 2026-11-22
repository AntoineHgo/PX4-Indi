import numpy as np
from pyulog import ULog
R='/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g3_refly_s199/'
FS=200.0
def eul(q):
    w,x,y,z=q
    roll=np.arctan2(2*(w*x+y*z),1-2*(x*x+y*y))
    pitch=np.arcsin(np.clip(2*(w*y-z*x),-1,1))
    return roll,pitch
def load(kind,r):
    u=ULog(f'{R}{kind}_{r}/run_{r}/flight.ulg')
    D={}
    def g(n,i=0):
        return [d for d in u.data_list if d.name==n and d.multi_id==i][0].data
    t0=g('vehicle_angular_velocity')['timestamp'][0]
    def T(d): return (d['timestamp'].astype(float)-float(t0))*1e-6
    tmax=T(g('vehicle_angular_velocity'))[-1]
    tg=np.arange(0,tmax,1/FS)
    def rs(d,key): return np.interp(tg,T(d),d[key])
    av=g('vehicle_angular_velocity'); D['t']=tg
    for i,a in enumerate('xyz'): D['w'+a]=rs(av,f'xyz[{i}]')
    rsp=g('vehicle_rates_setpoint'); D['wsp_x']=rs(rsp,'roll'); D['wsp_y']=rs(rsp,'pitch'); D['wsp_z']=rs(rsp,'yaw')
    at=g('vehicle_attitude')
    q=[rs(at,f'q[{i}]') for i in range(4)]; D['roll'],D['pitch']=eul(q)
    asp=g('vehicle_attitude_setpoint'); q=[rs(asp,f'q_d[{i}]') for i in range(4)]; D['roll_sp'],D['pitch_sp']=eul(q)
    ir=g('indi_rate_status')
    for k in ['torque_sp','torque_filtered','torque_increment','angular_accel_filtered','rates_sp_applied','nu']:
        for i,a in enumerate('xyz'): D[f'{k}_{a}']=rs(ir,f'{k}[{i}]')
    D['fault']=rs(ir,'fault');D['mtq_in_use']=rs(ir,'measured_torque_in_use')
    tm=g('actuator_torque_measured')
    for i,a in enumerate('xyz'): D[f'tmeas_{a}']=rs(tm,f'torque[{i}]')
    D['tmeas_valid']=rs(tm,'valid')
    ts=g('vehicle_torque_setpoint')
    for i,a in enumerate('xyz'): D[f'tsp_{a}']=rs(ts,f'xyz[{i}]')
    am=g('actuator_motors'); D['mot']=np.array([rs(am,f'control[{i}]') for i in range(4)])
    e0=g('esc_status',0); D['rpm']=np.array([rs(e0,f'esc[{i}].esc_rpm') for i in range(4)])
    D['alt']=-rs(g('vehicle_local_position_groundtruth'),'z') if 'z' in g('vehicle_local_position_groundtruth') else None
    D['tilt']=None
    return D
def fit(t,x,f,i0,i1):
    tt=t[i0:i1]; A=np.c_[np.sin(2*np.pi*f*tt),np.cos(2*np.pi*f*tt),np.ones_like(tt)]
    c=np.linalg.lstsq(A,x[i0:i1],rcond=None)[0]
    return c[0]+1j*c[1]  # x ~ Re(z e^{-i..}) ; z = a sin + b cos => amp |z|, phase via angle
def gp(t,y,x,f,i0,i1):
    zy=fit(t,y,f,i0,i1); zx=fit(t,x,f,i0,i1)
    r=zy/zx if abs(zx)>1e-12 else np.nan
    return abs(r), np.degrees(np.angle(r))  # phase of y relative to x (deg, negative = lag)
def peakf(t,x,i0,i1,lo=1,hi=4):
    seg=x[i0:i1]-x[i0:i1].mean(); F=np.fft.rfftfreq(len(seg)*8,1/FS); S=abs(np.fft.rfft(seg*np.hanning(len(seg)),len(seg)*8))
    m=(F>=lo)&(F<=hi); return F[m][np.argmax(S[m])]
