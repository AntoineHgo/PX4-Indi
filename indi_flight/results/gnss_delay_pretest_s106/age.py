import sys, numpy as np
from pyulog import ULog
u=ULog(sys.argv[1], ['sensor_gnss'])
for d in u.data_list:
    t=d.data['timestamp'].astype(np.int64); s=d.data['timestamp_sample'].astype(np.int64)
    a=t-s; dur=(t[-1]-t[0])/1e6
    print('multi_id',d.multi_id,'n',len(t),'rate_hz',round(len(t)/dur,2),'age_us median',np.median(a),'min',a.min(),'max',a.max(),'neg',int((a<0).sum()))
