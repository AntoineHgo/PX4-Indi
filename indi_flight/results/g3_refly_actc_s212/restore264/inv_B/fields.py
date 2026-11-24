import sys
from pyulog import ULog
u=ULog(sys.argv[1])
for t in sys.argv[2:]:
    d=u.get_dataset(t).data
    print(t, [k for k in d.keys() if not k.startswith('esc[') or k.startswith('esc[0]')][:80])
p=u.initial_parameters
print({k:v for k,v in p.items() if k.startswith(('MC_INDI','SIM_GZ_EC_MAX','SIM_GZ_EC_MIN','CA_','MPC_THR_HOVER','MPC_THR_MAX'))})
for m in u.logged_messages: 
    if m.timestamp>40e6: print(m.timestamp/1e6, m.message[:100])
