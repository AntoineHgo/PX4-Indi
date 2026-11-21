import numpy as np
from pyulog import ULog
import sys;u=ULog(sys.argv[1]);off=float(sys.argv[2])
D={d.name+str(d.multi_id):d for d in u.data_list}
def amp(topic,f,win,inst=0):
    d=D[topic+str(inst)];t=d.data['timestamp']*1e-6-off;x=d.data[f].astype(float)
    m=(t>=win[0])&(t<=win[1]);t=t[m];x=x[m]
    fs=(len(t)-1)/(t[-1]-t[0]);tu=np.arange(t[0],t[-1],1/fs);x=np.interp(tu,t,x);x-=x.mean()
    n=len(x);w=np.hanning(n);X=np.abs(np.fft.rfft(x*w))*2/w.sum();fr=np.fft.rfftfreq(n,1/fs)
    s=(fr>=87)&(fr<=91);i=np.argmax(X[s]);pk=fr[s][i];a=X[s][i]
    nb=((fr>=75)&(fr<85))|((fr>=93)&(fr<=103))
    return pk,a/np.sqrt(2),np.median(X[nb])/np.sqrt(2)  # rms of sine, neighbour median bin rms
for win in((float(sys.argv[3]),float(sys.argv[3])+17.5),):
  print('window',win)
  for tp,f in [('sensor_gyro','x'),('sensor_gyro','y'),('sensor_accel','x'),('sensor_accel','y'),('sensor_accel','z'),('vehicle_angular_velocity','xyz[1]'),('indi_rate_status','angular_accel_filtered[1]'),
    ('vehicle_rates_setpoint','pitch'),('indi_rate_status','rate_sp_dot[1]'),('indi_rate_status','nu[1]'),('vehicle_torque_setpoint','xyz[1]'),('actuator_motors','control[0]'),('vehicle_angular_velocity_groundtruth','xyz[1]'),('esc_status','esc[0].esc_rpm')]:
    try:
      pk,a,b=amp(tp,f,win)
      print('%-42s %-26s pk %.2f Hz line rms %.3e  neighbour-bin-median %.3e ratio %.1f'%(tp,f,pk,a,b,a/b))
    except Exception as e: print(tp,f,'err',e)
