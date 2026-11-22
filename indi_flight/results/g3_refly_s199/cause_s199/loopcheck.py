import sys; from common import *
kind,r,f0,t1,t2=sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4]),float(sys.argv[5]); AX=sys.argv[6] if len(sys.argv)>6 else 'y'
D=load(kind,r);t=D['t']
# t axis is relative to log start; user gives log-relative
a,b=int(t1*FS),int(t2*FS)
w=D['w'+AX];
zw=fit(t,w,f0,a,b); zacc=zw*1j*2*np.pi*f0
def rel(zy,zx): r=zy/zx; return abs(r),np.degrees(np.angle(r))
# fit uses sin/cos coeff: z=a+jb ; derivative of a sin+b cos -> w(a cos - b sin): handle explicitly
def d(x): 
    return np.gradient(x,1/FS)
zacc=fit(t,d(w),f0,a,b)
print('true accel / tmeas_y (gain=G1_true, phase)',rel(zacc,fit(t,D['tmeas_'+AX],f0,a,b)))
print('true accel / tsp_y',rel(zacc,fit(t,D['tsp_'+AX],f0,a,b)))
print('alpha_f / true accel',rel(fit(t,D['angular_accel_filtered_'+AX],f0,a,b),zacc))
print('tmeas / tsp',rel(fit(t,D['tmeas_'+AX],f0,a,b),fit(t,D['tsp_'+AX],f0,a,b)))
print('tfilt / tsp',rel(fit(t,D['torque_filtered_'+AX],f0,a,b),fit(t,D['tsp_'+AX],f0,a,b)))
print('tsp / (wsp-w) ',rel(fit(t,D['tsp_'+AX],f0,a,b),fit(t,D['wsp_'+AX]-w,f0,a,b)))
print('w/wsp',rel(zw,fit(t,D['wsp_'+AX],f0,a,b)))
print('wsp/(attsp-att) (attitude P gain)',rel(fit(t,D['wsp_'+AX],f0,a,b),fit(t,D['pitch_sp' if AX=='y' else 'roll_sp']-D['pitch' if AX=='y' else 'roll'],f0,a,b)))
print('attsp/att',rel(fit(t,D['pitch_sp' if AX=='y' else 'roll_sp'],f0,a,b),fit(t,D['pitch' if AX=='y' else 'roll'],f0,a,b)))
Cc=fit(t,D['tsp_'+AX],f0,a,b)/fit(t,D['wsp_'+AX]-w,f0,a,b); P=zacc/fit(t,D['tsp_'+AX],f0,a,b)/(1j*2*np.pi*f0)
# note: fit() returns a sin+b cos packed as a+jb, so use explicit rotation: phase of 1/(jw) already via amplitude only; compute |L| and phase from rel() values instead
rc=rel(fit(t,D['tsp_'+AX],f0,a,b),fit(t,D['wsp_'+AX]-w,f0,a,b)); rp=rel(zacc,fit(t,D['tsp_'+AX],f0,a,b))
print('OPEN-LOOP rate: |L|=%.2f phase=%.0f deg (controller %.4f@%.0f, plant accel/tsp %.0f@%.0f, integrator -90)'%(rc[0]*rp[0]/(2*np.pi*f0),rc[1]+rp[1]-90,rc[0],rc[1],rp[0],rp[1]))
