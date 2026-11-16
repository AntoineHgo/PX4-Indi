import sys; sys.path.insert(0,'/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/bench')
import att_loop_model_s48 as A, margins_models as MM
def r(name, **kw):
    m=A.marg(A.L_att, **kw); fc=m["crossings"][0]["f_c"] if m["crossings"] else float('nan')
    print("| %s | %.1f | %.2f | %.1f | %.1f |"%(name,m["pm_deg"],fc,m["gm_db"],1e3*m["dm_s"]))
b=dict(tau_r=0.033,tau_m=0.033,meas=False)
for dg in (20,30,50):
  for K in (15,20,25,30):
    for P in (0,3,5,8):
      r("tau_m33 dgyro%d K%d P%d"%(dg,K,P),P_att=float(P),**dict(b,K=float(K),dgyro_fc=float(dg)))
for fs in (400.0,250.0):
  r("fs%d tau_m33 dg20 K20 P5"%fs,fs=fs,P_att=5.0,**dict(b,K=20.0))
