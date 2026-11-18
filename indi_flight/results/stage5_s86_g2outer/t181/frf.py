import sys,numpy as np
sys.path.insert(0,'bench')
import margins_est as me
for p in ('pt0','pt1'):
    a=np.loadtxt(f'results/stage5_s86_g2outer/{p}_ax1_r400_s1_pinj.csv',delimiter=',',skiprows=1)
    t,d,x,y=a.T; fs=1/np.median(np.diff(t))
    r=me.frf_periodic(d,x,y,fs,10.0,me.log_bins(0.2,8,10.0),1,t=t)
    print(p,'N',len(t),'T',t[-1]-t[0],'rms d,x,y',d.std(),x.std(),y.std())
    for f,L,c,ac in zip(r['f'],r['L'],r['thr'],r['accepted']):
        print(f"{f:.2f} |L|={abs(L):.3f} ph={np.degrees(np.angle(L)):7.1f} coh={c:.3f} {ac}")
