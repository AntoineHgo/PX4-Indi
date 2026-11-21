"""A-54 probe (S170): 1P line (sensor_accel x, 120-200 Hz), 3P alias (sensor_accel z, 250-400 Hz), mean true rotor rpm
(esc_status inst 1), z line in vehicle_acceleration 20-130 Hz, per window. Usage: LOG T0 T1 [T0 T1 ...] (ulog time, s)."""
import sys, numpy as np
from pyulog import ULog
from scipy.signal import welch
u=ULog(sys.argv[1],['sensor_accel','esc_status','vehicle_acceleration','actuator_motors']); s=u.start_timestamp
def get(n,i=0):
    d=[d for d in u.data_list if d.name==n and d.multi_id==i][0]; return (d.data['timestamp']-s)*1e-6, d.data
def pk(t,x,m,lo,hi):
    fs=1/np.median(np.diff(t[m])); f,p=welch(x[m]-x[m].mean(),fs=fs,nperseg=int(fs*2)); b=(f>=lo)&(f<=hi); i=np.argmax(p[b])
    return f[b][i], p[b][i]/np.median(p[b])
w=[float(a) for a in sys.argv[2:]]
for t0,t1 in zip(w[::2],w[1::2]):
    ta,a=get('sensor_accel'); m=(ta>=t0)&(ta<t1)
    te,e=get('esc_status',1); me=(te>=t0)&(te<t1); rpm=np.mean([np.mean(e['esc[%d].esc_rpm'%j][me]) for j in range(4)])
    tv,v=get('vehicle_acceleration'); mv=(tv>=t0)&(tv<t1)
    tm,am=get('actuator_motors'); mm=(tm>=t0)&(tm<t1)
    f1=pk(ta,a['x'],m,120,200); f3=pk(ta,a['z'],m,250,400); fv=pk(tv,v['xyz[2]'],mv,20,130); fa=pk(tm,am['control[0]'],mm,20,100)
    print('win %.0f-%.0f rpm %.0f (1P %.1f Hz) | acc x 1P %.1f Hz | acc z %.1f Hz (pred 800-3*1P %.1f) | vacc z %.1f Hz %.0fx (pred %.1f) | mot %.1f Hz %.0fx'%(
        t0,t1,rpm,rpm/60,f1[0],f3[0],800-3*f1[0],fv[0],fv[1],abs(800-3*f1[0]-800/3),fa[0],fa[1]))
