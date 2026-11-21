import sys; sys.path.insert(0,"indi_flight/results/g4_chatter_probe_s175"); sys.path.insert(0,"indi_flight/bench")
import numpy as np, chatter_probe_s175 as C, g3_checks as k1
d=sys.argv[1]; log=d+"/flight.ulg"
tt,pos,q,w,tm,cmd,ref,src,tl,navc=k1.load(log,100.0,110.0)
ok=np.isfinite(cmd).all(axis=1); tr=C.band_track(tm[ok],cmd[ok][:,:4])
for a,b,fl,f,r in tr:
    if 92<=a<=110: print(f"{a:6.1f}-{b:6.1f} flag={int(fl)} peak {f:5.1f} Hz line RMS (+-2Hz, best ratio>20 motor) {r:.2e}")
