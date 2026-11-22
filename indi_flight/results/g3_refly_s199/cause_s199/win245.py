import sys; from common import *
kind,r,f0=sys.argv[1],sys.argv[2],float(sys.argv[3]); t1=float(sys.argv[4]); tend=float(sys.argv[5]); win=float(sys.argv[6]) if len(sys.argv)>6 else 2.0
D=load(kind,r); t=D['t']; print(kind,r,'end t',t[-1])
d2=np.degrees
print('t0   f   |pitch_sp| |pitch| g(att/sp) ph | |wsp| |w| g(w/wsp) ph | |tsp| |tmeas| g(tm/tsp) ph | |tfilt| | accel_f | motmax motmin satfrac(>.98,<.02) rpmamp tmeas_in_use')
tt=t1
while tt+win<=tend:
    i0=int(tt*FS);i1=int((tt+win)*FS)
    f=f0
    ga=gp(t,D['pitch'],D['pitch_sp'],f,i0,i1); gw=gp(t,D['wy'],D['wsp_y'],f,i0,i1); gt=gp(t,D['tmeas_y'],D['tsp_y'],f,i0,i1)
    am=lambda k:abs(fit(t,D[k],f,i0,i1))
    m=D['mot'][:,i0:i1]; sat=np.mean((m>.98).any(0)); lo=np.mean((m<.02).any(0))
    rp=np.mean([abs(fit(t,D['rpm'][k],f,i0,i1)) for k in range(4)])
    print(f"{tt:5.1f} {peakf(t,D["wy"],i0,i1):.2f} {d2(am('pitch_sp')):6.2f} {d2(am('pitch')):6.2f} {ga[0]:.2f} {ga[1]:6.0f} | {d2(am('wsp_y')):6.1f} {d2(am('wy')):6.1f} {gw[0]:.2f} {gw[1]:6.0f} | {am('tsp_y'):.4f} {am('tmeas_y'):.4f} {gt[0]:.2f} {gt[1]:6.0f} | {am('torque_filtered_y'):.4f} | {am('angular_accel_filtered_y'):.1f} | {m.max():.2f} {m.min():.2f} {sat:.2f} {lo:.2f} {rp:.0f} {D['mtq_in_use'][i0:i1].mean():.2f}")
    tt+=win
