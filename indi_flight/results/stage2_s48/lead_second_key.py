import numpy as np
T=1/800; tau=0.033; wn=2*np.pi*40; w20=2*np.pi*20
f=np.logspace(np.log10(0.2),np.log10(399),400001); s=1j*2*np.pi*f; w=2*np.pi*f
A=np.exp(-s*T/2)/(1+s*tau); Am=A
F=wn**2/(s**2+np.sqrt(2)*wn*s+wn**2); H=F/(1+s/w20)
def L(K,tc,P):
    # returned = H Am e^{-sT} u - (1+K tc) H A u - K (F+P/s) A/s u ; L=-returned/u
    return (1+K*tc)*H*A + K*(F+P/s)*A/s - H*Am*np.exp(-s*T)
rows=[("K20 tc0 P8",20,0,8,(28.6,2.97,14.2,26.8)),("K20 tc0 P3",20,0,3,(43.8,2.81,15.7,43.3)),
("K20 tc0 P0",20,0,0,(53.7,2.78,16.5,53.6)),("K20 tc.033 P8",20,.033,8,(60.8,3.02,16.3,55.8)),
("K40 tc0 P8",40,0,8,(19.8,4.74,8.7,11.6)),("K40 tc.033 P8",40,.033,8,(56.0,6.65,10.7,23.4)),
("K60 tc.033 P8",60,.033,8,(41.1,9.91,7.4,11.5))]
out=["| case | PM all (deg @Hz) | GM all (dB @Hz) | DM ms (main) | key1 PM/fc/GM/DM | verdict |","|--|--|--|--|--|--|"]
for n,K,tc,P,k1 in rows:
    l=L(K,tc,P); m=np.abs(l); ph=np.degrees(np.angle(l))
    ic=np.where(np.diff(np.sign(m-1))!=0)[0]
    pms=[((ph[i]+180+180)%360-180, f[i]) for i in ic]
    ig=np.where((np.diff(np.sign(l.imag))!=0)&(l.real[:-1]<0))[0]
    gms=[(-20*np.log10(m[i]),f[i]) for i in ig]
    hi=[g for g in gms if g[1]>0.5]; lo=[g for g in gms if g[1]<=0.5]
    pm,fc=pms[-1]; dm=np.radians(pm)/(2*np.pi*fc)*1e3
    gm=min(hi,key=lambda g:abs(g[0]))[0] if hi else float('nan')
    ok=abs(pm-k1[0])<=5 and abs(gm-k1[2])<=1.5
    out.append(f"| {n} | {', '.join(f'{a:.1f}@{b:.2f}' for a,b in pms)} | {', '.join(f'{a:.1f}@{b:.2f}' for a,b in hi)}{' (low<0.5Hz: '+', '.join(f'{a:.1f}@{b:.2f}' for a,b in lo)+')' if lo else ''} | {dm:.1f} | {k1[0]}/{k1[1]}/{k1[2]}/{k1[3]} | {'AGREE' if ok else 'DISAGREE'} (mine {pm:.1f}/{fc:.2f}/{gm:.1f}/{dm:.1f}) |")
print("\n".join(out)); open("table.tmp","w").write("\n".join(out))
