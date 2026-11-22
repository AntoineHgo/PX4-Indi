import pickle,sys
sys.path.insert(0,'.')
from extract import out,osc
for i,r in sorted(out.items()):
    if not (r['c1'] and r['c2']): continue
    s1,s2=osc(r)
    if not (s1 or s2): continue
    a0=r['c2']['item2_oscillation']['airborne_span_s'][0]
    sk=[t-a0 for t in r['c2']['item2_oscillation']['rates']['p']['skipped_windows_t']]
    # skipped windows rel
    def ov(a,b): return any(a<t+4 and b>t for t in sk)
    o=r['c1']['item2_oscillation']
    d=[]
    for a in 'pqr':
        if o[a]['sustained']:
            for (f,st,n) in o[a]['lines']:
                d.append((a,f,st,n,'inSkip' if ov(st,st+n-1+4) else 'noSkip', 'k2has' if any(x[0]==a for x in s2) else 'k2no'))
    both = bool(s1) and bool(s2)
    print(i,'BOTH' if both else ('K1only' if s1 else 'K2only'), d, 'k2skip_rel',[round(x) for x in sk[::7]],'nlines2',[(x[0],x[3]-a0 if len(x)>3 else 0) for x in s2],'tland-a0',round(r['c1']['t_land']-r['c1']['airborne'][0],1) if r['c1'].get('t_land') else None)
