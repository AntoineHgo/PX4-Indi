import sys,json,re,numpy as np
sys.path.insert(0,'/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/bench')
import margins_models as MM, margins_est as ME
R='/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/'
def rd(p):
    t=open(p).read().splitlines()
    f=eval(t[1][2:]);m=eval(t[2].split(']')[0].split('[',1)[1].join('[]'));ph=eval('['+t[3].split('[',1)[1])
    j=json.loads(t[4]);return np.array(f),np.array(m),np.array(ph),j
def model(kw,f,fs=800.):
    w=2*np.pi*f;L=MM.L_indi(w,fs,**kw);return 20*np.log10(abs(L)),np.degrees(np.angle(L)),kw
def mg(kw):
    m=MM.margins_of(MM.L_indi,800.,**kw);return m
def wr(d):return (d+180)%360-180
sets=[('S57 meas',R+'stage3_s57/roll_m3a_meas800/meas800_s1_margins.txt',MM.PRE_DA64,'PRE'),
      ('S77 tb0',R+'stage3_s77_a34/tb0_margins.txt',MM.HEAD_FLIGHT,'HEAD'),
      ('S77 bld1',R+'stage3_s77_a34/bld1.0_margins.txt',dict(MM.HEAD_FLIGHT,Tb=1.0),'HEAD')]
for lat in (1,0,2):
  print('att_lat',lat)
  for nm,p,kw,tag in sets:
    kw=dict(kw,att_lat=lat)
    f,m,ph,j=rd(p);mdb,mph,_=model(kw,f)
    sel=(f>=1)&(f<=8)
    dm=mdb-m; dp=wr(mph-ph)
    print(nm,tag,'max|dB|%.2f max|deg|%.1f'%(abs(dm[sel]).max(),abs(dp[sel]).max()),'meas PM %.1f fc %.2f DM %.1f'%(j['pm_deg'],j['crossings'][0]['f_c'],j['dm_s']*1e3))
    mm=mg(kw);print('   model',{k:(round(v,2) if isinstance(v,float) else v) for k,v in mm.items() if k!='crossings'} if isinstance(mm,dict) else mm)
    if lat==1 and nm=='S77 tb0': print(np.round(dm,1),np.round(dp,1))
print('=====')
def cross(kw):
    f=np.geomspace(0.3,100,4000);L=MM.L_indi(2*np.pi*f,800.,**kw);a=abs(L)
    i=np.where((a[:-1]>1)&(a[1:]<=1))[0]
    return [(round(f[k],2),round(180+np.degrees(np.angle(L[k])),1)) for k in i]
for nm,kw in (('PRE',MM.PRE_DA64),('HEAD',MM.HEAD_FLIGHT),('HEAD nosplead-only att',dict(MM.HEAD_FLIGHT,fb_lead=0)),('nolead no att',dict(MM.HEAD_FLIGHT,att_p=0,fb_lead=0))):
    print(nm,cross(kw))
fp,mp,pp,jp=rd(R+'stage3_s57/roll_m3a_meas800/meas800_s1_margins.txt')
fh,mh,ph,jh=rd(R+'stage3_s77_a34/tb0_margins.txt')
print('f',fp[:11]);print('meas dB shift HEAD-PRE',np.round((mh-mp)[:11],1),'phase',np.round((wr(ph-pp))[:11],1))
a,b,_=model(MM.HEAD_FLIGHT,fp);c,d,_=model(MM.PRE_DA64,fp)
print('model dB shift',np.round((a-c)[:11],1),'phase',np.round(wr(b-d)[:11],1))
print('PRE dm',np.round((model(MM.PRE_DA64,fp)[0]-mp)[:11],1),np.round(wr(model(MM.PRE_DA64,fp)[1]-pp)[:11],1))
# diagnostics only
for kw in ({'att_p':8.0},{'att_p':6.0},{'att_p':10.0},{'tau_r':0.04},{'lat':1},{'att_lat':4},{'gyro_fc':30.0}):
    e=[]
    for nm,p,base in (('P',sets[0][1],MM.PRE_DA64),('H',sets[1][1],MM.HEAD_FLIGHT)):
        f,m,ph_,j=rd(p);x,y,_=model(dict(base,**kw),f);s=(f>=1)&(f<=8);e.append((round(abs(x-m)[s].max(),1),round(abs(wr(y-ph_))[s].max(),1)))
    print(kw,e)
