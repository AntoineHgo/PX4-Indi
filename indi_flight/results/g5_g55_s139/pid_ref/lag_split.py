import sys,json,numpy as np
from pyulog import ULog
d=sys.argv[1];u=ULog(d+'/flight.ulg');r=json.load(open(d+'/run.json'))
g=lambda n:[x for x in u.data_list if x.name==n][0].data
gt=g('vehicle_local_position_groundtruth');lp=g('vehicle_local_position');sp=g('trajectory_setpoint')
t0=r['trajectory']['t0_us'];t1=t0+r['trajectory']['dur_s']*1e6
def lag(ta,a,tb,b):  # delay of b relative to a, xy
  m=(tb>=t0+3e6)&(tb<t1);best=None
  for dl in np.arange(0,0.4,0.005):
    e=np.hypot(np.interp(tb[m]-dl*1e6,ta,a[0])-b[0][m],np.interp(tb[m]-dl*1e6,ta,a[1])-b[1][m]);rms=np.sqrt(np.mean(e**2))
    if best is None or rms<best[1]: best=(dl,rms)
  e0=np.hypot(np.interp(tb[m],ta,a[0])-b[0][m],np.interp(tb[m],ta,a[1])-b[1][m]);return best,np.sqrt(np.mean(e0**2))
print('est vs truth (truth->est delay, rms at best, rms at 0):',lag(gt['timestamp'],(gt['x'],gt['y']),lp['timestamp'],(lp['x'],lp['y'])))
ok=np.isfinite(sp['position[0]'])
print('sp vs est:',lag(sp['timestamp'][ok],(sp['position[0]'][ok],sp['position[1]'][ok]),lp['timestamp'],(lp['x'],lp['y'])))
print('sp vs truth:',lag(sp['timestamp'][ok],(sp['position[0]'][ok],sp['position[1]'][ok]),gt['timestamp'],(gt['x'],gt['y'])))
for k in ['EKF2_GPS_DELAY','SIM_GPS_DELAY','EKF2_EV_DELAY','MPC_XY_P','MPC_XY_VEL_P_ACC']:
  if k in u.initial_parameters: print(k,u.initial_parameters[k])
