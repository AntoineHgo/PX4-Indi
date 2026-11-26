import json,sys,subprocess
# usage: verify.py cand_run_dir ref_run_dir
c,r=sys.argv[1:3]
a=json.load(open(c+'/g3_draw.json'));b=json.load(open(r+'/g3_draw.json'))
print('draw equal:',a['draw']==b['draw'])
for k in a:
    if k not in('build','command') and a[k]!=b[k]: print('differs',k)
print('build equal:',a['build']==b['build'])
ca,cb=a['command'],b['command']
print('cmd len',len(ca),len(cb),'diff args:',[(x[-60:],y[-60:]) for x,y in zip(ca,cb) if x!=y])
ra=json.load(open(c+'/run.json'));rb=json.load(open(r+'/run.json'))
print('scenario',ra['scenario'],'ref',rb['scenario'],'exit',ra.get('exit_status'),'seed',ra.get('seed'),rb.get('seed'))
