import sys,pickle,re
sys.path.insert(0,'.')
from extract import out,osc
rows=pickle.load(open('/tmp/claude-1001/-home-ahugo-Documents-Drotek-Codes-PX4-Indi/fc0236dc-079e-43b5-bb6f-32da6e289fb3/scratchpad/rows.pkl','rb'))
cls={}
for i,r in out.items():
    if r['outcome']!='ok': continue
    s1,s2=osc(r)
    hi=any(abs(x[1]-10.75)<1.5 and x[1]>5 for x in s1+s2)
    # land-only: key1 only, every line start rel>=44
    o=r['c1']['item2_oscillation']
    lines=[(a,l) for a in 'pqr' for l in o[a]['lines']]
    land=bool(lines) and all(l[1]>=44 for a,l in lines)
    if hi: c='A_10.75Hz'
    elif s2: c='B_2Hz_inflight_k2'
    elif s1 and land: c='C_landing_only_k1'
    elif s1: c='D_inflight_k1only'
    else: c='-'
    cls[i]=c
import collections
print(collections.Counter(cls.values()))
for c in sorted(set(cls.values())):
    ids=[i for i in cls if cls[i]==c]
    print(c,ids if c!='-' else '')
fm={x[0]:x[1] for x in rows}
import statistics as st
for c in sorted(set(cls.values())):
    L=[fm[i] for i in cls if cls[i]==c and i<240]
    if L: print(c,len(L),{k:round(st.median(x[k] for x in L),2) for k in ('loop_delay_ms','mass','tau_up','tau_down','gust_peak','gnss_delay_ms','vib')})
pickle.dump(cls,open('/tmp/claude-1001/-home-ahugo-Documents-Drotek-Codes-PX4-Indi/fc0236dc-079e-43b5-bb6f-32da6e289fb3/scratchpad/cls.pkl','wb'))
# bins
for k,edges in (('loop_delay_ms',[0,2.5,5,7.5,10,20]),('mass',[0,.8,.9,1.0,1.1,2])):
    print(k)
    for a,b in zip(edges,edges[1:]):
        L=[i for i in cls if i<240 and a<=fm[i][k]<b or False]
        L=[i for i in cls if i<240 and a<=fm[i][k]<b]
        n=len(L); print(f'  [{a},{b}) n={n}', {c:sum(cls[i]==c for i in L) for c in sorted(set(cls.values())) if c!='-'})
