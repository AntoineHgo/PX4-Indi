import sys, numpy as np
sys.path.insert(0,"/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/bench")
import ident_actc as ia
rng=np.random.default_rng(42)
def sim(tu,td,dly=7.5e-3,frames=2,closed=False,K=0.0,tl=30.0):
    h=1.25e-3; sub=10; hh=h/sub; n=int(tl/h)
    f=rng.uniform(2,45,9); ph=rng.uniform(0,6.28,9)
    t=np.arange(n)*h
    ms=0.03*np.sum(np.sin(2*np.pi*f[:,None]*t+ph[:,None]),0)/np.sqrt(3)
    u=np.zeros(n); rpmtrue=np.zeros(n); x=0.45
    # forward euler on fine grid, delay by linear interpolation of u in continuous time
    ym_hist=np.full(n,0.4**0)  # placeholder
    U=lambda tt: np.interp(tt,t[:k+1],u[:k+1]) if k>0 else 0.45
    y0=0.01+0.9*0.45
    for k in range(n):
        ym=(rpmtrue[max(k-1-frames,0)]/1e4)**2 if closed else y0
        u[k]=0.45+ms[k]-K*(ym-y0)
        for s in range(sub):
            tt=t[k]+s*hh-dly
            ud=np.interp(tt,t[max(k-30,0):k+1],u[max(k-30,0):k+1]) if tt>=0 else 0.45
            x+=hh*(ud-x)/(tu if ud>x else td)
        rpmtrue[k]=np.sqrt(0.01+0.9*x)*1e4
    rpm=np.round((rpmtrue+rng.normal(0,30,n))/20)*20
    rl=np.concatenate([np.full(frames,rpm[0]),rpm[:n-frames]])
    return t,u,rl
for tu,td in ((0.033,0.099),(0.033,0.033),(0.099,0.033)):
  for cl in (False,True):
    t,u,r=sim(tu,td,closed=cl,K=1.5)
    m=ia.identify(t,u[:,None],t,r[:,None],1e4)["motors"][0]
    print(f"true {tu*1e3:.0f}/{td*1e3:.0f} closed={cl}: up {m['tau_up']*1e3:.1f} down {m['tau_down']*1e3:.1f} sym {m['tau_sym']*1e3:.1f} d {m['delay_ms']:.2f} (true 10.0) pass {m['pass_']} {m['flags']}",flush=True)
