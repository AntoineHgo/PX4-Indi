import sys, numpy as np
from pyulog import ULog
u=ULog(sys.argv[1])
t0=None
def line(t,x,lo=36,hi=53.5):
    m=(t>=lo)&(t<=hi)
    t=t[m];x=x[m]
    if len(t)<400: return None
    fs=(len(t)-1)/(t[-1]-t[0])
    # resample uniformly (nearest) to fs
    tu=np.arange(t[0],t[-1],1/fs); x=np.interp(tu,t,x)
    x=x-np.mean(x)
    # segment 2 s hann welch
    n=int(2*fs);step=n//2;w=np.hanning(n);P=0;k=0
    for i in range(0,len(x)-n+1,step):
        P=P+np.abs(np.fft.rfft(x[i:i+n]*w))**2;k+=1
    P=P/k/(w**2).sum()*2  # power per bin (amp^2)
    f=np.fft.rfftfreq(n,1/fs)
    sel=(f>=85)&(f<=93)
    if f[-1]<93: return fs,None,None,'NOT RESOLV (Nyq %.0f)'%(fs/2)
    # RMS in band (bandpass)
    rms=np.sqrt(P[sel].sum()); pk=f[sel][np.argmax(P[sel])]
    # baseline neighbours 70-84,94-110
    nb=(((f>=70)&(f<84))|((f>94)&(f<=110)))
    base=np.sqrt(P[nb].mean()*sel.sum())
    return fs,rms,pk,'base %.2e'%base
names={d.name+str(d.multi_id):d for d in u.data_list}
def get(n,i=0): return names[n+str(i)]
T=lambda d:d.data['timestamp']*1e-6
arm=None
sig=[]
def add(topic,fields,idx=None,inst=0):
    if topic+str(inst) not in names: print(topic,'missing');return
    d=get(topic,inst);t=T(d)
    for f in fields:
        if f in d.data: sig.append((topic+'.'+f,t,d.data[f]))
        else:
            for k in range(8):
                kk='%s[%d]'%(f,k)
                if kk in d.data: sig.append((topic+'.'+kk,t,d.data[kk]))
for tp,fl in [('sensor_gyro',['x','y','z']),('sensor_accel',['x','y','z']),('sensor_combined',['gyro_rad','accelerometer_m_s2']),
 ('vehicle_angular_velocity',['xyz']),('vehicle_acceleration',['xyz']),
 ('indi_pos_status',['a_c','a_f','t_f','t_c','t_c_applied','omega_ff']),
 ('indi_rate_status',['nu','angular_accel_filtered','torque_filtered','torque_increment','torque_sp','rate_sp_dot']),
 ('vehicle_attitude_setpoint',['q_d','thrust_body']),('vehicle_rates_setpoint',['roll','pitch','yaw']),
 ('vehicle_torque_setpoint',['xyz']),('vehicle_thrust_setpoint',['xyz']),
 ('esc_status',[]),('actuator_motors',['control']),('actuator_torque_measured',['xyz']),
 ('vehicle_angular_velocity_groundtruth',['xyz'])]:
    add(tp,fl)
for inst in (0,1):
  if 'esc_status'+str(inst) in names:
    d=get('esc_status',inst);t=T(d)
    for k in range(4):
        sig.append(('esc_status%d.rpm[%d]'%(inst,k),t,d.data['esc[%d].esc_rpm'%k].astype(float)))
# time base: use 'seconds since arm'? use window as in README: absolute from log start? use vehicle_status arming
vs=get('vehicle_status');ts=T(vs);arm=ts[np.argmax(vs.data['arming_state']==2)]
off=float(sys.argv[2]) if len(sys.argv)>2 else arm
print('arm t',arm,'offset',off)
lo,hi=(float(sys.argv[3]),float(sys.argv[4])) if len(sys.argv)>4 else (36,53.5)
for n,t,x in sig:
    r=line(t-off,x.astype(float),lo,hi)
    if r is None: print('%-50s no data'%n);continue
    print('%-50s fs=%6.1f rms89=%s pk=%s %s'%(n,r[0],'%.3e'%r[1] if r[1] is not None else '-', r[2], r[3]))
