import sys; sys.argv=['x']
exec(open('/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/stage3_s78_a34/compare.py').read().split("for lat in")[0])
for nm,p,kw in (('S57 vs PRE_DA64',sets[0][1],MM.PRE_DA64),('S77 tb0 vs HEAD_FLIGHT',sets[1][1],MM.HEAD_FLIGHT)):
    f,m,ph,j=rd(p);a,b,_=model(kw,f);print(nm);print('| f Hz | meas dB | model dB | d dB | meas deg | model deg | d deg |\n|---|---|---|---|---|---|---|')
    for i in range(len(f)):
        if f[i]<=8: print('| %.1f | %.1f | %.1f | %+.1f | %.1f | %.1f | %+.1f |'%(f[i],m[i],a[i],a[i]-m[i],ph[i],b[i],wr(b[i]-ph[i])))
