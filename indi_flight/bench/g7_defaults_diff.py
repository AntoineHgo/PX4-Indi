#!/usr/bin/env python3
"""G7(c): firmware default INDI parameters vs the validated parameter file.

Reads every MC_INDI_* default from the module yaml files, the validated params file and the reference
airframe (param set-default lines), prints the table and the mismatches, exits 1 if a class (i) mismatch exists.
Classes: i gain/default to align, ii physical per-airframe, iii enable switch / bench-only. An unclassified
mismatch counts as class (i).
Usage: python3 -I g7_defaults_diff.py [--yaml F ...] [--params F] [--airframe F]
"""
import argparse
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
YAMLS = ["src/modules/mc_indi_rate_control/mc_indi_rate_control_params.yaml",
         "src/modules/mc_indi_pos_control/mc_indi_pos_control_params.yaml"]
PARAMS = "indi_flight/results/g5_freeze_s157/params.params"
AIRFRAME = "ROMFS/px4fmu_common/init.d-posix/airframes/4040_gz_quad5in"

# class of a parameter when it mismatches (see DEFAULTS_DIFF.md for the reasoning)
CLASS = {
    "MC_INDI_EN": "iii", "MC_INDI_POS_EN": "iii",             # enable switches
    "MC_INDI_W_MAX": "ii", "MC_INDI_ACT_TC": "ii",            # physical, per airframe
    "MC_INDI_ID_OK": "ii",                                    # identification attestation, per airframe
}


def yaml_defaults(path):
    """{name: default} from a PX4 params yaml; PyYAML if present, else a minimal line parser."""
    try:
        import yaml
        with open(path) as f:
            doc = yaml.safe_load(f)
        out = {}
        for grp in doc.get("parameters", []):
            for name, d in grp.get("definitions", {}).items():
                out[name] = d.get("default")
        return out
    except ImportError:
        out, cur = {}, None
        for line in open(path):
            m = re.match(r"^    ([A-Z][A-Z0-9_]*):\s*$", line)
            if m:
                cur = m.group(1)
                continue
            m = re.match(r"^      default:\s*(\S+)", line)
            if m and cur:
                out[cur] = m.group(1)
                cur = None
        return out


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def same(a, b):
    na, nb = num(a), num(b)
    return (na == nb) if na is not None and nb is not None else str(a) == str(b)


def read_params(path):
    out = {}
    for line in open(path):
        line = line.split("#", 1)[0].split()
        if len(line) >= 2:
            out[line[0]] = line[1]
    return out


def airframe_defaults(path):
    out = {}
    for line in open(path):
        m = re.match(r"\s*param\s+set-default\s+(MC_INDI_\w+)\s+(\S+)", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def compute(yamls, params, airframe):
    fw = {}
    for y in yamls:
        fw.update({k: v for k, v in yaml_defaults(y).items() if k.startswith("MC_INDI_")})
    val = read_params(params)
    af = airframe_defaults(airframe) if airframe and os.path.exists(airframe) else {}
    rows = []
    for k in sorted(fw):
        v = val.get(k)
        eff = af.get(k, fw[k])
        ok = v is None or same(fw[k], v)
        ok_eff = v is None or same(eff, v)
        rows.append({"name": k, "fw": fw[k], "val": v, "eq": ok, "af": af.get(k), "eq_eff": ok_eff,
                     "cls": None if ok else CLASS.get(k, "i")})
    extra = sorted(k for k in val if k.startswith("MC_INDI_") and k not in fw)
    return rows, extra


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--yaml", action="append")
    ap.add_argument("--params", default=os.path.join(REPO, PARAMS))
    ap.add_argument("--airframe", default=os.path.join(REPO, AIRFRAME))
    a = ap.parse_args(argv)
    yamls = a.yaml or [os.path.join(REPO, y) for y in YAMLS]
    rows, extra = compute(yamls, a.params, a.airframe)
    print("| param | firmware default | validated | airframe set-default | equal | equal with airframe | class |")
    print("|---|---|---|---|---|---|---|")
    for r in rows:
        print("| %s | %s | %s | %s | %s | %s | %s |" % (
            r["name"], r["fw"], r["val"] if r["val"] is not None else "not set -> fw default",
            r["af"] if r["af"] is not None else "-", "yes" if r["eq"] else "NO",
            "yes" if r["eq_eff"] else "NO", r["cls"] or "-"))
    for k in extra:
        print("params file sets %s which is not in any yaml" % k)
    bad = [r for r in rows if not r["eq"]]
    print("\nmismatches: %d (%s)" % (len(bad), ", ".join("%s:%s" % (r["name"], r["cls"]) for r in bad) or "none"))
    n1 = sum(1 for r in bad if r["cls"] == "i") + len(extra)
    print("G7(c) %s" % ("fails on %d class (i) mismatches" % n1 if n1 else "would pass (0 class (i) mismatches)"))
    return 1 if n1 else 0


if __name__ == "__main__":
    sys.exit(main())
