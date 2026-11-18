import sys,numpy as np
from pyulog import ULog
for F in ("F1","F2"):
    u=ULog(f"{F}/run/flight.ulg"); d={x.name:x.data for x in u.data_list if x.multi_id==0}
    e=d['esc_status']; t=e['timestamp']
    ec=np.array([e[f'esc[{i}].esc_errorcount'] for i in range(4)])
    inc=np.diff(ec,axis=1)>0
    n=inc.shape[1]
    print(F,"esc samples",n+1,"frac drop per motor",inc.mean(axis=1).round(3),"total errs",ec[:,-1]-ec[:,0])
    idx=np.where(inc[0])[0][:50]; print(" first50 drop idx m0",idx[:12].tolist())
    d0=np.where(inc[0])[0][:50]
    globals()[F]=d0
    g=d['sensor_gyro']; ts=g['timestamp']*1e-6
    print(" gyro n",len(ts),"rate",len(ts)/(ts[-1]-ts[0]))
    m=(ts>ts[0]+0.5*(ts[-1]-ts[0]))&(ts<ts[0]+0.9*(ts[-1]-ts[0]))
    for ax in 'xyz':
        y=g[ax]; x=np.zeros_like(y); x[2:]=(y[2:]-2*y[1:-1]+y[:-2])/np.sqrt(6); print(" 2nd-diff white-std",ax,x[m].std().round(6),"raw std", g[ax][m].std().round(5))
print("same first50?",np.array_equal(F1,F2) if len(F1)==len(F2) else False)
