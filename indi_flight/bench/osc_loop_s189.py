"""S189: band amplitude/phase of gyro, truth gyro, rate sp, torque sp/meas, eRPM around the oscillation line of a G3 run ulog."""
import sys, numpy as np
from pyulog import ULog
def load(f):
    u=ULog(f); D={}
    for d in u.data_list:
        if d.multi_id==0 and d.name not in D: D[d.name]=d.data
    return D
def sig(D,n,k):
    d=D[n]; return d['timestamp']*1e-6, np.asarray(d[k],float)
def band(t,x,t0,t1,fs=250.0):
    tt=np.arange(t0,t1,1/fs); xi=np.interp(tt,t,x); xi=xi-xi.mean()
    w=np.hanning(len(xi)); N=1<<16; F=np.fft.rfft(xi*w,N); f=np.fft.rfftfreq(N,1/fs)
    return tt,xi,f,F
def main(fn,t0,t1,ax,flo,fhi):
    D=load(fn); ax=int(ax); flo=float(flo); fhi=float(fhi); t0=float(t0); t1=float(t1)
    ch={'gyro':('vehicle_angular_velocity',f'xyz[{ax}]'),'gyro_gt':('vehicle_angular_velocity_groundtruth',f'xyz[{ax}]'),
        'rate_sp':('vehicle_rates_setpoint',['roll','pitch','yaw'][ax]),'tau_sp':('vehicle_torque_setpoint',f'xyz[{ax}]'),
        'tau_meas':('actuator_torque_measured',f'torque[{ax}]'),'alpha_f':('indi_rate_status',f'angular_accel_filtered[{ax}]'),
        'motor0':('actuator_motors','control[0]')}
    ref=None; out={}
    for k,(n,c) in ch.items():
        t,x=sig(D,n,c); tt,xi,f,F=band(t,x,t0,t1)
        m=(f>=flo)&(f<=fhi); i=np.argmax(abs(F[m])); fp=f[m][i]
        amp=2*abs(F[m][i])/np.sum(np.hanning(len(xi)))
        out[k]=(fp,amp,F[m][i]); 
    fp=out['gyro'][0]
    print(f'{fn} t[{t0},{t1}] axis{ax} peak gyro f={fp:.2f}Hz')
    for k,(f_,a,Fc) in out.items():
        # evaluate complex at the gyro peak freq
        t,x=sig(D,*ch[k]); tt,xi,f,F=band(t,x,t0,t1); j=np.argmin(abs(f-fp)); c=F[j]; r=out['gyro'][2] if False else None
        out[k]=(f_,a,c)
    g=out['gyro'][2]
    for k,(f_,a,c) in out.items():
        print(f'{k:9s} peak {f_:5.2f}Hz amp {a:9.4g}  amp@f {2*abs(c)/np.sum(np.hanning(int((t1-t0)*250))):9.4g} phase vs gyro {np.degrees(np.angle(c/g)):7.1f} deg')
    # motors rms/saturation
    t,x=sig(D,'actuator_motors','control[0]'); m=(t>t0)&(t<t1)
    allm=np.array([sig(D,'actuator_motors',f'control[{i}]')[1] for i in range(4)])
    mm=np.interp(0,[0,1],[0,1]); sel=(t>t0)&(t<t1)
    print('motor cmd min/max in window',allm[:,sel].min(),allm[:,sel].max())
if __name__=='__main__': main(*sys.argv[1:])
