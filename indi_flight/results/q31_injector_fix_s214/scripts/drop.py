import sys,numpy as np
from pyulog import ULog
for f in sys.argv[1:]:
    u=ULog(f); ne=max(d.multi_id for d in u.data_list if d.name=='esc_status')
    e=[d for d in u.data_list if d.name=='esc_status' and d.multi_id==ne][0].data; t=e['timestamp']*1e-6
    m=[d for d in u.data_list if d.name=='actuator_motors'][0].data; tm=m['timestamp']*1e-6
    pt=[x[0]*1e-6 for x in u.changed_parameters if 'EC_MAX' in x[1]]
    if not pt: print(f,'no EC_MAX'); continue
    t0=min(pt)
    at=[d for d in u.data_list if d.name=='vehicle_attitude'][0].data; ta=at['timestamp']*1e-6
    tilt=np.degrees(np.arccos(np.clip(1-2*(at['q[1]']**2+at['q[2]']**2),-1,1)))
    w=(ta>t0)&(ta<t0+4); print(f.split('results/')[1], f"writes {t0:.2f}-{max(pt):.2f}", f"max tilt {tilt[w].max():.0f} at {ta[w][tilt[w].argmax()]:.2f}")
    for j in range(4):
        r=e[f'esc[{j}].esc_rpm']; cmd=np.interp(t,tm,m[f'control[{j}]'])
        # implied EC_MAX = omega/sqrt(cmd)
        om=r*2*np.pi/60; ok=cmd>0.05; imp=np.where(ok,om/np.sqrt(np.maximum(cmd,1e-3)),np.nan)
        s=(t>t0-0.2)&(t<t0+2.5)
        # first time implied EC_MAX < 2000
        idx=np.where(s&(imp<2150))[0]
        print(f"   motor {j}: implied EC_MAX<2150 from {t[idx[0]]:.2f}" if len(idx) else f"   motor {j}: never")
