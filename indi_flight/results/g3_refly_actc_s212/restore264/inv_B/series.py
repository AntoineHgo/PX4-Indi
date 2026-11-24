import sys, numpy as np
from pyulog import ULog
u=ULog(sys.argv[1]); t0=float(sys.argv[2]); t1=float(sys.argv[3]); step=float(sys.argv[4])
ch=[(t/1e6,n,v) for t,n,v in u.changed_parameters if n.startswith(('SIM_GZ_EC_MAX','SIM_GZ_EC_MIN')) and t>1e6]
print('param changes', ch[:12]); p=u.initial_parameters; print('W_MAX',p.get('MC_INDI_W_MAX'),'HOVER',p.get('MPC_THR_HOVER'),'EC_MAX1..4',[p.get(f'SIM_GZ_EC_MAX{i}') for i in range(1,5)])
def ds(n):
    try: return u.get_dataset(n).data
    except Exception: return None
def at(d,k,t):
    i=np.searchsorted(d['timestamp'],t*1e6); i=min(max(i-1,0),len(d['timestamp'])-1); return d[k][i]
M=ds('actuator_motors');E=ds('esc_status');C=ds('control_allocator_status');R=ds('vehicle_angular_velocity');RS=ds('vehicle_rates_setpoint')
A=ds('vehicle_attitude');TS=ds('vehicle_thrust_setpoint');Q=ds('vehicle_torque_setpoint');I=ds('indi_rate_status');TM=ds('actuator_torque_measured');P=ds('indi_pos_status');LP=ds('vehicle_local_position')
print('t  thr_z | m0 m1 m2 m3 | rpm0..3 | unT xyz unThr_z | p q r | psp qsp rsp | tilt | tq_sp xyz | tf xyz | tmeas xyz | vz alt')
for t in np.arange(t0,t1,step):
    q=[at(A,f'q[{i}]',t) for i in range(4)]; tilt=np.degrees(np.arccos(np.clip(1-2*(q[1]**2+q[2]**2),-1,1)))
    s=f"{t:6.2f} {at(TS,'xyz[2]',t):+.3f} |"+' '.join(f"{at(M,f'control[{i}]',t):.2f}" for i in range(4))+' |'
    s+=' '.join(f"{at(E,f'esc[{i}].esc_rpm',t):5.0f}" for i in range(4))+' |'
    s+=' '.join(f"{at(C,f'unallocated_torque[{i}]',t):+.2f}" for i in range(3))+f" {at(C,'unallocated_thrust[2]',t):+.2f} |"
    s+=' '.join(f"{at(R,f'xyz[{i}]',t):+5.1f}" for i in range(3))+' |'+' '.join(f"{at(RS,k,t):+5.1f}" for k in ('roll','pitch','yaw'))+f" |{tilt:5.1f} |"
    s+=' '.join(f"{at(Q,f'xyz[{i}]',t):+.2f}" for i in range(3))+' |'
    if I is not None: s+=' '.join(f"{at(I,f'torque_filtered[{i}]',t):+.2f}" for i in range(3))+' |'+' '.join(f"{at(TM,f'torque[{i}]',t):+.2f}" for i in range(3))+f" v{int(at(TM,'valid',t))}u{int(at(I,'measured_torque_in_use',t))}|"
    s+=f" {at(LP,'vz',t):+.1f} {-at(LP,'z',t):.1f}"
    print(s)
