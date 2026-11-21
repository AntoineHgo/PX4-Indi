import sys; sys.path.insert(0,"indi_flight/bench")
import g4_chatter_skip_key1 as s, numpy as np, g3_checks as k1
for n in sys.argv[1:]:
    tt,pos,q,w,tm,cmd,*_ = k1.load(f"indi_flight/results/freeze7_s177/g4/{n}/flight.ulg",0,0)
    h=-pos[:,2];h=h-h[0];up=np.flatnonzero(h>1);ta,te=float(tt[up[0]]),float(tt[up[-1]])
    v,_=s.scan(tm,cmd,ta,te,None)
    print(n,ta,te,[[(round(f,1),round(ta+a,1),nw) for f,a,nw in L] for L in v["lines"]])
