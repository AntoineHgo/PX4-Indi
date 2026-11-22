import pickle,statistics as st
S='/tmp/claude-1001/-home-ahugo-Documents-Drotek-Codes-PX4-Indi/fc0236dc-079e-43b5-bb6f-32da6e289fb3/scratchpad/'
rows=pickle.load(open(S+'rows.pkl','rb')); cls=pickle.load(open(S+'cls.pkl','rb'))
fm={x[0]:x[1] for x in rows}
L=[i for i in fm if i<240]
def rate(sel,lab):
    n=[i for i in L if sel(fm[i])]
    f=lambda cs:sum(cls[i] in cs for i in n)
    print(f'{lab:40s} n={len(n):3d} A+B={f(("A_10.75Hz","B_2Hz_inflight_k2"))} A={f(("A_10.75Hz",))} B={f(("B_2Hz_inflight_k2",))} C={f(("C_landing_only_k1",))} D={f(("D_inflight_k1only",))}')
rate(lambda f:True,'all LHS')
rate(lambda f:f['loop_delay_ms']>=7.5,'delay>=7.5ms')
rate(lambda f:f['loop_delay_ms']<7.5,'delay<7.5ms')
rate(lambda f:f['loop_delay_ms']>=7.5 and f['tau_down']>=1.5,'delay>=7.5 & tau_down>=1.5')
rate(lambda f:f['loop_delay_ms']>=7.5 and f['tau_down']<1.5,'delay>=7.5 & tau_down<1.5')
rate(lambda f:f['loop_delay_ms']>=7.5 and f['tau_up']<=0.7,'delay>=7.5 & tau_up<=0.7')
rate(lambda f:f['loop_delay_ms']<7.5 and f['tau_up']<=0.7,'delay<7.5 & tau_up<=0.7')
rate(lambda f:f['tau_up']<=0.6,'tau_up<=0.6')
rate(lambda f:f['mass']<0.9,'mass<0.9')
rate(lambda f:f['mass']>=0.9,'mass>=0.9')
rate(lambda f:f['gust_peak']>=6,'gust_peak>=6')
rate(lambda f:f['gnss_delay_ms']<120,'gnss delay<120')
rate(lambda f:f['gnss_delay_ms']>=200,'gnss delay>=200')
for i in (8,25,42,62,112,220,283,285):
    f=fm[i]; print(i,{k:round(f[k],2) for k in('loop_delay_ms','mass','tau_up','tau_down','gust_peak','vib','gnss_delay_ms','g1_err_pitch','I_iyy')})
