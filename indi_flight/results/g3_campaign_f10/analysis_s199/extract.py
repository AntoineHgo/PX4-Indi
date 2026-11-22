import json,os,csv,glob
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows=[]
for l in list(csv.reader(open(R+'/SCORES.tsv'),delimiter='\t'))[1:]:
    rows.append(l)
out={}
for l in rows:
    i=l[0]; r={'idx':int(i),'outcome':l[1],'k1':l[2],'k2':l[3],'f1':l[4],'f2':l[5]}
    rd=f'{R}/run_{i}'
    try: c1=json.load(open(rd+'/g3_checks.json'))
    except Exception: c1=None
    try: c2=json.load(open(f'{R}/key2/run_{i}.json'))
    except Exception: c2=None
    try: dr=json.load(open(rd+'/g3_draw.json'))
    except Exception: dr=None
    r['c1']=c1;r['c2']=c2;r['draw']=dr
    out[int(i)]=r
import pickle;pickle.dump(out,open('/tmp/claude-1001/-home-ahugo-Documents-Drotek-Codes-PX4-Indi/fc0236dc-079e-43b5-bb6f-32da6e289fb3/scratchpad/all.pkl','wb'))
print(len(out))
def osc(r):
    s1=[];s2=[]
    if r['c1']:
        o=r['c1']['item2_oscillation']
        for a in 'pqr':
            if o[a]['sustained']: s1.append((a,o[a]['lines'][0][0],round(o[a]['max_rms_ratio_flagged'],1),round(r['c1']['airborne'][0]+o[a]['lines'][0][1],1),o[a]['lines'][0][2]))
        if o['position']['sustained']: s1.append(('pos',))
    if r['c2']:
        o=r['c2']['item2_oscillation']
        for a in 'pqr':
            if o['rates'][a]['sustained']: s2.append((a,o['rates'][a]['at'][1],round(o['rates'][a]['max_rms_dps'],1),o['rates'][a]['at'][0]))
        if o['position_limit_cycle']['sustained']: s2.append(('pos',))
    return s1,s2
if __name__=='__main__':
    for i,r in sorted(out.items()):
        if 'item2' in r['f1'] or 'item2' in r['f2'] or r['outcome']!='ok':
            s1,s2=osc(r); m=r['c1']['mode'] if r['c1'] else '?'
            print(i,r['outcome'][:20],m,'K1',s1,'K2',s2)
