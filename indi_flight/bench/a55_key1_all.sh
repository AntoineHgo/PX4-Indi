#!/usr/bin/env bash
# A-55 closing test (S170): key1 g3_checks.py on every hover run of results/g4_gate_s169, window = last 10 s of the
# hold event in run.json; writes <run>/g3_checks_a55.json and prints key1 vs key2 per run.
cd "$(dirname "$0")/.." || exit 1
for r in results/g4_gate_s169/hover_*_s?; do
  read t0 t1 < <(python3 -c "import json;e=[e for e in json.load(open('$r/run.json'))['events'] if e['name']=='hold'][0];end=e['t_us']*1e-6+e['dur_s'];print(end-10,end)")
  python3 bench/g3_checks.py $r/flight.ulg --t0 $t0 --t1 $t1 > $r/g3_checks_a55.json 2>/dev/null
  python3 - "$r" <<'PY'
import json,sys
r=sys.argv[1]; a=json.load(open(r+'/g3_checks_a55.json'))
try: b=json.load(open(r+'/g3_checks_key2.json'))
except Exception: b={}
ch=lambda d:{k:(v.get('pass',v.get('flag')) if isinstance(v,dict) else v) for k,v in d.items() if 'chat' in k or k.startswith('item')}
print(r.split('/')[-1],'K1',json.dumps(ch(a))[:230],'| K2',json.dumps(ch(b))[:200])
PY
done
