import sys; from common import *
kind,r,ax,lo,hi=sys.argv[1],sys.argv[2],sys.argv[3],float(sys.argv[4]),float(sys.argv[5])
D=load(kind,r);t=D['t']
x=D['w'+ax]; F=np.fft.rfftfreq(len(x),1/FS); X=np.fft.rfft(x-x.mean()); X[(F<lo)|(F>hi)]=0; y=np.fft.irfft(X,len(x))
import json
ts0=json.load(open('/dev/null')) if False else None
n=int(1*FS); out=[]
for k in range(0,len(t)-n,n): out.append((t[k],np.degrees(np.sqrt(2)*y[k:k+n].std())))
top=sorted(out,key=lambda z:-z[1])[:6]
print(kind,r,ax,'log-rel t of top 1s bands amp(dps)',[(round(a,1),round(b,1)) for a,b in top])
print('count windows >5 dps:',sum(1 for a,b in out if b>5),'of',len(out))
