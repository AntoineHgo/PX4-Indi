import sys,glob,numpy as np
from pyulog import ULog
for d in sorted(glob.glob(sys.argv[1]+"/*_s?")+glob.glob(sys.argv[1]+"/pid_*")):
    if d.endswith(".log") or d.endswith(".rc"): continue
    u=ULog(d+"/flight.ulg",["vehicle_land_detected"]);x=u.get_dataset("vehicle_land_detected").data
    t=(x["timestamp"].astype(np.int64)-u.start_timestamp)*1e-6
    out=[]
    for k in ("ground_contact","landed"):
        v=x[k].astype(int);e=np.flatnonzero(np.diff(v)!=0)
        out.append(k+f"[0]={v[0]}: "+" ".join(("+" if v[i+1] else "-")+f"{t[i+1]:.2f}" for i in e))
    print(d.split("/")[-1],t[-1].round(1)," | ".join(out))
