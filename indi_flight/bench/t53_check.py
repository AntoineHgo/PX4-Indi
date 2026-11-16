import sys
from pyulog import ULog
u=ULog(sys.argv[1]); d={x.name:x.data for x in u.data_list}
a=d['sim_schedule_applied']
print("applied:")
for i in range(len(a['timestamp'])):
    print(i,a['row_index'][i],a['kind'][i],"ts",a['timestamp'][i],"sched",a['t_sched_us'][i],"err",int(a['timestamp'][i])-int(a['t_sched_us'][i]),"anchor",a['anchor_us'][i],"sp",[round(float(a['sp[%d]'%k][i]),3) for k in range(4)])
s=d['vehicle_status']
prev=None
print("status changes:")
for t,n,ar in zip(s['timestamp'],s['nav_state'],s['arming_state']):
    if (n,ar)!=prev: print(t,"nav",n,"arm",ar); prev=(n,ar)
import numpy as np
p=d['vehicle_local_position']; t=p['timestamp']; 
anc=int(a['anchor_us'][-1])
for lo,hi in ((anc+1e6,anc+3e6),(anc+3e6,anc+6e6),(anc+6e6,anc+12e6)):
    m=(t>=lo)&(t<hi)
    print("win",(lo-anc)/1e6,(hi-anc)/1e6,"z mean %.3f min %.3f max %.3f |x|max %.3f |y|max %.3f"%(p['z'][m].mean(),p['z'][m].min(),p['z'][m].max(),abs(p['x'][m]).max(),abs(p['y'][m]).max()))
