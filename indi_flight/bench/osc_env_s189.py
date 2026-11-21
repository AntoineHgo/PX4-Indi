"""S189: per-2s-window rms (dps) of p,q,rate-sp in a band, plus dominant freq, for a G3 ulog; args ulg flo fhi."""
import sys, numpy as np
from pyulog import ULog
u=ULog(sys.argv[1]); flo,fhi=float(sys.argv[2]),float(sys.argv[3]); D={}
for d in u.data_list:
    if d.multi_id==0 and d.name not in D: D[d.name]=d.data
g=D['vehicle_angular_velocity']; t=g['timestamp']*1e-6; s=D['vehicle_rates_setpoint']; ts=s['timestamp']*1e-6
def env(t,x,a,b):
    tt=np.arange(a,b,1/250); xi=np.interp(tt,t,x); xi-=xi.mean(); F=np.fft.rfft(xi*np.hanning(len(xi))); f=np.fft.rfftfreq(len(xi),1/250)
    m=(f>=flo)&(f<=fhi); A=2*abs(F)/np.sum(np.hanning(len(xi))); i=np.argmax(A*m); return np.degrees(A[i]/np.sqrt(2)),f[i]
for a in np.arange(t[0]+2,t[-1]-2,2.0):
    r=[env(t,g[f'xyz[{k}]'],a,a+2) for k in (0,1)]+[env(ts,s[k],a,a+2) for k in ('roll','pitch')]
    print(f'{a:6.1f} p {r[0][0]:5.2f}@{r[0][1]:4.1f} q {r[1][0]:5.2f}@{r[1][1]:4.1f} | spR {r[2][0]:5.2f}@{r[2][1]:4.1f} spP {r[3][0]:5.2f}@{r[3][1]:4.1f}')
