"""S189: in the strongest 2.5-8 Hz p-window of each G3 run, amplitude ratio q_d(att setpoint)/att and rate_sp/gyro (roll) - which loop carries the line; args ulg..."""
import sys, numpy as np
from pyulog import ULog
fs=250
for fn in sys.argv[1:]:
    u=ULog(fn); D={}
    for d in u.data_list:
        if d.multi_id==0 and d.name not in D: D[d.name]=d.data
    def roll(n,k):
        d=D[n]; w,x,y,z=[d[k%i] for i in range(4)]; return d['timestamp']*1e-6, np.arctan2(2*(w*x+y*z),1-2*(x*x+y*y))
    g=D['vehicle_angular_velocity']; tg=g['timestamp']*1e-6; s=D['vehicle_rates_setpoint']; ts=s['timestamp']*1e-6
    ta,a=roll('vehicle_attitude','q[%d]'); td,qd=roll('vehicle_attitude_setpoint','q_d[%d]')
    best=None
    for t0 in np.arange(tg[0]+1,tg[-1]-4,1.0):
        tt=np.arange(t0,t0+4,1/fs); w=np.hanning(len(tt)); f=np.fft.rfftfreq(len(tt),1/fs); m=(f>=2.5)&(f<=8)
        def sp(t,x): xi=np.interp(tt,t,x); xi-=xi.mean(); F=np.fft.rfft(xi*w); A=2*abs(F)/w.sum(); i=np.argmax(A*m); return A[i],f[i]
        pa,fp=sp(tg,g['xyz[0]'])
        if best is None or pa>best[0]: best=(pa,fp,t0,sp(ta,a)[0],sp(td,qd)[0],sp(ts,s['roll'])[0])
    pa,fp,t0,aa,qa,sa=best
    print(f'{fn.split("/")[-2]:>10s} {"PID" if "pid_refs" in fn else "INDI"} t0={t0:5.1f} f={fp:4.1f}Hz p={np.degrees(pa):5.2f}dps att={np.degrees(aa):.3f}deg q_d={np.degrees(qa):.3f}deg q_d/att={qa/max(aa,1e-9):5.1f} rate_sp/p={sa/pa:4.2f}')
