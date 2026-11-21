from pyulog import ULog
import sys
for f in sys.argv[1:]:
    u=ULog(f,message_name_filter_list=['x'])
    ip={k:v for k,v in u.initial_parameters.items() if k in('MC_INDI_XY_P','MC_INDI_XY_VP','MPC_XY_P','MPC_XY_VEL_P_ACC','MC_INDI_INJ_AX')}
    ch=[c for c in u.changed_parameters if c[1] in ('MC_INDI_XY_P','MC_INDI_XY_VP')]
    print(f,ip,ch)
