import sys, json, numpy as np
sys.path.insert(0,"indi_flight/bench")
import metrics
from pyulog import ULog
R=sys.argv[1]; run=json.load(open(R+"/run.json")); u=ULog(R+"/flight.ulg")
print({k:v for k,v in u.initial_parameters.items() if k in("MPC_XY_P","MPC_XY_VEL_P_ACC","MC_INDI_ID_OK")})
for m in u.changed_parameters:
    if m[1] in ("MPC_XY_P","MPC_XY_VEL_P_ACC"): print("changed",m)
ev={e["name"]:e for e in run["events"]}
gt,_=metrics.truth_local_position(u)
t0=ev["traj"]["t_us"]; t=gt["timestamp"]; m=(t>=t0)&(t<t0+ev["traj"]["dur_s"]*1e6)
pos=np.column_stack([gt[k][m] for k in "xyz"])
e=pos-metrics.analytic_reference(run["trajectory"],run["trajectory"]["t0_us"],run["hold_pos_ned"],t[m])
eh=np.hypot(e[:,0],e[:,1]); print("rms_h",np.sqrt(np.mean(eh**2)),"max_h",eh.max(),"max_v",abs(e[:,2]).max())
tw=(t[m]-t0)*1e-6
# tilt and rates from ground truth
d=u.get_dataset("sim_ground_truth").data
tg=d["timestamp"].astype(float)*1e-6; mm=(d["timestamp"]>=t0)&(d["timestamp"]<t0+ev["traj"]["dur_s"]*1e6)
q=np.stack([d[f"q[{i}]"] for i in range(4)],1)
tilt=np.degrees(np.arccos(np.clip(1-2*(q[:,1]**2+q[:,2]**2),-1,1)))
print("tilt max (traj window)",tilt[mm].max(),"whole",tilt.max())
w=np.stack([d[f"angular_velocity[{i}]"] for i in range(3)],1)
def spec(x,ts,name):
    x=x-np.mean(x); dt=np.median(np.diff(ts)); fs=1/dt
    n=len(x); f=np.fft.rfftfreq(n,dt); P=np.abs(np.fft.rfft(x*np.hanning(n)))**2
    b=(f>0.5)&(f<40); i=np.argmax(P[b]); med=np.median(P[b])
    # exclude <=0.5 Hz lemniscate content
    print(f"{name}: peak {f[b][i]:.2f} Hz, peak/median {P[b][i]/med:.0f}, rms {np.std(x):.3f}")
for k,nm in enumerate("pqr"): spec(np.degrees(w[mm,k]),tg[mm],"rate_"+nm+"_degs")
vx=d["vx"][mm]; vy=d["vy"][mm]
spec(vx,tg[mm],"vx"); spec(vy,tg[mm],"vy")
# rate RMS in higher band >2Hz
for k,nm in enumerate("pqr"):
    x=np.degrees(w[mm,k]); dt=np.median(np.diff(tg[mm])); n=len(x); f=np.fft.rfftfreq(n,dt); X=np.fft.rfft(x-x.mean()); X[f<2]=0
    print("rate_%s rms>2Hz %.2f deg/s"%(nm,np.sqrt(np.mean(np.fft.irfft(X,n)**2))))
am=u.get_dataset("actuator_motors").data
c=np.stack([am[f"control[{i}]"] for i in range(4)],1); ma=(am["timestamp"]>=t0)&(am["timestamp"]<t0+ev["traj"]["dur_s"]*1e6)
c=c[ma]; c=c[np.isfinite(c).all(1)]
print("motor max",c.max(),"min",c.min(),"frac>=0.99",(c>=0.99).mean(),"frac<=0.01",(c<=0.01).mean(),"frac<=0.05",(c<=0.05).mean())
