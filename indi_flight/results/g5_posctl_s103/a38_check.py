import sys, numpy as np
from pyulog import ULog
u=ULog(sys.argv[1]); ev=float(sys.argv[2])
d={(x.name,x.multi_id):x.data for x in u.data_list}
t0=u.start_timestamp
def g(n,f,m=0):
    x=d[(n,m)]; return (x['timestamp']-t0)/1e6, x[f]
tn,ns=g('vehicle_status','nav_state')
print('nav_state changes:',[(round(a,1),int(b)) for a,b in zip(tn,ns) if True][:1],[(round(tn[i],1),int(ns[i])) for i in range(1,len(ns)) if ns[i]!=ns[i-1]])
ts,zs=g('trajectory_setpoint','position[2]')
tl,zl=g('vehicle_local_position','z')
names=[k[0] for k in d if 'groundtruth' in k[0]]; print('gt topics',names)
tg,zg=g('vehicle_local_position_groundtruth','z')
end=float(sys.argv[3])
for a,b in [(ev-20,ev-1),(ev+10,end),(end-10,end)]:
    m=(tg>=a)&(tg<=b); zsp=np.interp(tg[m],ts,zs); zest=np.interp(tg[m],tl,zl)
    print(f'[{a:.1f},{b:.1f}] sp mean {np.nanmean(zsp):.3f} std {np.nanstd(zsp):.4f} nan {np.isnan(zsp).mean():.2f}; truth-sp {np.nanmean(zg[m]-zsp):.3f}; est-sp {np.nanmean(zest-zsp):.3f}; truth-est {np.mean(zg[m]-zest):.3f}')
m=(ts>ev-5)&(ts<ev+12); print('sp around event', np.round(zs[m][::max(1,m.sum()//12)],3))
