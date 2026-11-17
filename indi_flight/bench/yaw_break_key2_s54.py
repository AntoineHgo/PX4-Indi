import sys, numpy as np
fs=800.; dt=1/fs; G1=205.; G2=27.; P=2.8; K=10.; tm=0.05; c=K*tm
def run(f, G2p=G2, taup=0.033, law="coded"):
    z=np.exp(1j*2*np.pi*f*dt); zi=1/z
    def A(t):
        a=np.exp(-dt/t); return (1-a)*zi/(1-a*zi)
    D=(1-zi)/dt; I=dt/(1-zi)
    k=np.tan(np.pi*30/fs); n=1+np.sqrt(2)*k+k*k
    b=[k*k/n,2*k*k/n,k*k/n]; a=[1,2*(k*k-1)/n,(1-np.sqrt(2)*k+k*k)/n]
    H=sum(b[k]*zi**k for k in range(3))/sum(a[k]*zi**k for k in range(3))
    # per unit x
    alpha=(G1+G2p*D)*A(taup)
    r=I*alpha; psi=I*r; nu=K*(-P*psi-r)
    tf=H*A(tm); af=H*alpha
    num=nu-(1+c)*af
    if law=="coded": num=num+G2*D*tf
    # S54 orchestrator fix: the code divides by the STATIC G1 + g2/dt (indi_rate_control.cpp l.388-390); option (c) by G1 + G2*D
    y=tf+num/((G1+G2/dt) if law=="coded" else (G1+G2*D))
    return -y
def margins(fg,L):
    m=20*np.log10(abs(L)); ph=np.unwrap(np.angle(L))*180/np.pi
    Ms=np.max(-20*np.log10(abs(1+L)))
    out=[]
    for i in np.where(np.diff(np.sign(m))!=0)[0]:
        w=m[i]/(m[i]-m[i+1]); f0=fg[i]*(fg[i+1]/fg[i])**w; p=ph[i]+w*(ph[i+1]-ph[i])
        arg=p%360; arg=arg-360 if arg>0 else arg
        out.append((f0,arg,180+arg,'down' if m[i]>0 else 'up'))
    return Ms,out
def main(path):
    fg=np.logspace(np.log10(0.1),np.log10(60),6000)
    o=[]
    for law in("coded","c"):
        L=run(fg,law=law); Ms,cx=margins(fg,L)
        o.append(f"== law {law}")
        for f in(.1,1,10,20):
            l=run(np.array([f]),law=law)[0]
            o.append(f"f={f}: |L|={20*np.log10(abs(l)):.2f} dB arg={np.degrees(np.angle(l)):.1f} deg")
        o.append(f"Ms={Ms:.2f} dB")
        for f0,arg,pm,d in cx: o.append(f"crossover {f0:.3f} Hz ({d}) arg={arg:.1f} PM={pm:.1f}")
        if not cx: o.append("no crossover in 0.1-60 Hz")
    for name,kw in(("G2x0.5",dict(G2p=G2*.5)),("G2x2",dict(G2p=G2*2)),("taup x2",dict(taup=.066))):
        Ms,cx=margins(fg,run(fg,law="c",**kw)); o.append(f"law c {name}: Ms={Ms:.2f} dB, crossovers={[(round(a,2),round(p,1)) for a,_,p,_ in cx]}")
    open(path,"w").write("\n".join(o)+"\n"); print("\n".join(o))
main(sys.argv[1])
