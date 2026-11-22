import sys,pickle
sys.path.insert(0,'.')
from extract import out,osc
S='/tmp/claude-1001/-home-ahugo-Documents-Drotek-Codes-PX4-Indi/fc0236dc-079e-43b5-bb6f-32da6e289fb3/scratchpad/'
cls=pickle.load(open(S+'cls.pkl','rb'))
def fmt1(r):
    o=r['c1']['item2_oscillation']; a=[]
    for ax in 'pqr':
        if o[ax]['sustained']:
            L=o[ax]['lines']; f=sorted(set(round(l[0],2) for l in L)); a.append(f"{ax}@{'/'.join(str(x) for x in f)}Hz {o[ax]['max_rms_ratio_flagged']:.0f}dps t{min(l[1] for l in L):.0f}")
    if o['position']['sustained']: a.append('pos')
    return '; '.join(a) or '-'
def fmt2(r):
    o=r['c2']['item2_oscillation']['rates']; a=[]
    for ax in 'pqr':
        if o[ax]['sustained']: a.append(f"{ax}@{o[ax]['at'][1]:g}Hz {o[ax]['max_rms_dps']:.0f}dps t{o[ax]['at'][0]:.0f}")
    if r['c2']['item2_oscillation']['position_limit_cycle']['sustained']: a.append('pos')
    return '; '.join(a) or '-'
rows=[];both=k1o=k2o=0
for i,r in sorted(out.items()):
    if r['outcome']!='ok': continue
    f1='item2' in r['f1']; f2='item2' in r['f2']
    if not(f1 or f2): continue
    ag='both' if f1 and f2 else ('k1 only' if f1 else 'k2 only')
    rows.append(f"| {i:03d} | {r['c1']['mode'][:3]} | {cls[i][0]} | {ag} | {fmt1(r)} | {fmt2(r)} |")
open('item2_table.md','w').write('\n'.join(rows)+'\n'); print(len(rows))
