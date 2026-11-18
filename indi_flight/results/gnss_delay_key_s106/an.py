import sys, numpy as np
from pyulog import ULog
u=ULog(sys.argv[1])
names={d.name+str(d.multi_id):d for d in u.data_list}
print(sorted(names)[:200] if len(sys.argv)>2 else '')
d=names['sensor_gnss0'].data; t=d['timestamp'].astype(np.int64); s=d['timestamp_sample'].astype(np.int64); a=t-s
print('gnss n',len(t),'rate',round(len(t)/((t[-1]-t[0])/1e6),2),'age med/min/max',np.median(a),a.min(),a.max(),'neg',int((a<0).sum()))
for nm in ('estimator_aid_src_gnss_pos0','estimator_aid_src_gnss_vel0'):
    if nm not in names: print(nm,'absent'); continue
    d=names[nm].data; t=d['timestamp']/1e6
    keys=[k for k in d if k.startswith('innovation[') ]
    inn=np.array([d['innovation[%d]'%i] for i in range(2)]); h=np.hypot(*inn)
    tr=d['test_ratio[0]'] if 'test_ratio[0]' in d else d['test_ratio']
    fu=d['fused'] if 'fused' in d else np.ones_like(t)
    # hold: last 60 s window of fused samples
    m=(t>t[-1]-50)&(fu>0)
    print(nm,'n',m.sum(),'hRMS',np.sqrt(np.mean(h[m]**2)),'med test_ratio',np.median(tr[m]),'fused frac',fu.mean())
