import glob,sys
from pyulog import ULog
import numpy as np
for n in ('gap085_indi_htoff','loss08_indi'):
    u=ULog(glob.glob('indi_flight/results/stage5_s72/%s/run/*.ulg'%n)[0],['indi_pos_status'])
    d=u.data_list[0].data; t=d['timestamp']/1e6; b=d['blend']
    print(n,'t0',round(float(t[0]),1),'max|b|',round(float(abs(b).max()),4),'frozen frac',round(float(d['blend_frozen'].mean()),3),
      [(tt,round(float(b[min(np.searchsorted(t,tt),len(b)-1)]),4)) for tt in (60,70,75,80,90,100,110,125)])
