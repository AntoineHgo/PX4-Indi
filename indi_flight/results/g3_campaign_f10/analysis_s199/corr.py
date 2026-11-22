import sys,statistics as st
sys.path.insert(0,'.')
from extract import out,osc
def fac(r):
    d=r['draw']['draw']; f=d['factors']; F={}
    F['mode_attitude']=1.0 if d['mode']=='attitude' else 0.0
    for a in ('roll','pitch','yaw'): F['g1_err_'+a]=f['g1_err'][a]
    F['g1_err_max_dev']=max(abs(__import__('math').log(f['g1_err'][a])) for a in('roll','pitch','yaw'))
    F['gnss_delay_ms']=f['gnss']['ekf_delay_ms']; F['gnss_mismatch_abs']=abs(f['gnss'].get('mismatch_offset_ms') or 0)
    F['gnss_matched']=1.0 if f['gnss'].get('matched') else 0.0
    F['mass']=f['mass_scale']['value']; F['tau_up']=f['tau_up']['value']; F['tau_down']=f['tau_down']['value']
    F['tau_asym']=f['tau_asym']['value']; F['vib']=f['vibration']['mult']; F['vib_acc']=f['vibration']['acc_ms2']
    F['wind_steady']=f['wind']['steady_ms']; F['gust_peak']=f['wind']['gust_peak_total_ms']
    F['loop_delay_ms']=f['loop_delay']['total_ms']
    for k in('ixx','iyy','izz'): F['I_'+k]=f['inertia_scale'][k]
    for k in('saturation','tel_dropout','tel_frozen','tel_loss','thrust_sag','weak_motor'): F[k+'_on']=1.0 if f[k]['on'] else 0.0
    F['tel_dropout_prob']=f['tel_dropout'].get('prob',0)
    F['tel_latency']=f['tel_latency']['frames']
    return F
rows=[]
for i,r in sorted(out.items()):
    if r['outcome']!='ok': continue
    s1,s2=osc(r)
    rows.append((i,fac(r),bool(s1),bool(s2),bool(s1 or s2),bool([x for x in s1 if x[1]>5]) ,[x for x in s2]))
import pickle
pickle.dump(rows,open('/tmp/claude-1001/-home-ahugo-Documents-Drotek-Codes-PX4-Indi/fc0236dc-079e-43b5-bb6f-32da6e289fb3/scratchpad/rows.pkl','wb'))
def table(sel,label,cols):
    R=[x for x in rows if sel(x)]
    print('##',label,'n=',len(R),'union fails',sum(x[4] for x in R),'k1',sum(x[2] for x in R),'k2',sum(x[3] for x in R))
    for k in rows[0][1]:
        v=[x[1][k] for x in R]
        if len(set(v))<2: continue
        if set(v)<={0.0,1.0}:
            on=[x for x in R if x[1][k]==1.0]; off=[x for x in R if x[1][k]==0.0]
            print(f'{k:18s} on n={len(on):3d} u={sum(x[4] for x in on):3d} k1={sum(x[2] for x in on):3d} k2={sum(x[3] for x in on):3d} | off n={len(off):3d} u={sum(x[4] for x in off)} k1={sum(x[2] for x in off)} k2={sum(x[3] for x in off)}')
        else:
            m=st.median(v); lo=[x for x in R if x[1][k]<=m]; hi=[x for x in R if x[1][k]>m]
            f=lambda L,j:f'{sum(x[j] for x in L)}/{len(L)} ({100*sum(x[j] for x in L)/len(L):.0f}%)'
            print(f'{k:18s} med={m:.3g} low u {f(lo,4)} hi u {f(hi,4)} | k1 lo {f(lo,2)} hi {f(hi,2)} | k2 lo {f(lo,3)} hi {f(hi,3)}')
table(lambda x:x[0]<240,'LHS',0)
table(lambda x:x[0]>=240,'corners',0)
print('by corner'); 
for c in range(6):
    R=[x for x in rows if 240+10*c<=x[0]<250+10*c]
    print('C%d'%(c+1),'n',len(R),'u',sum(x[4] for x in R),'k1',sum(x[2] for x in R),'k2',sum(x[3] for x in R))
R=[x for x in rows if x[0]<240]
for m in (0,1):
    L=[x for x in R if x[1]['mode_attitude']==m]; print('mode_att',m,len(L),sum(x[4] for x in L),sum(x[2] for x in L),sum(x[3] for x in L))
