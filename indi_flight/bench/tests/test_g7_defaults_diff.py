#!/usr/bin/env python3
"""Synthetic self-test of g7_defaults_diff: fake yaml, params and airframe with known mismatches."""
import contextlib
import io
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import g7_defaults_diff as g  # noqa: E402

YAML = """module_name: x
parameters:
- group: g
  definitions:
    MC_INDI_K_R:
      type: float
      default: 20.0
    MC_INDI_ACT_TC:
      type: float
      default: 0.05
    MC_INDI_ID_OK:
      type: int32
      default: 0
    MC_INDI_SAME:
      type: int32
      default: 1
"""


def run(params_txt):
    with tempfile.TemporaryDirectory() as d:
        y, p, a = (os.path.join(d, n) for n in ("y.yaml", "p.params", "af"))
        open(y, "w").write(YAML)
        open(p, "w").write(params_txt)
        open(a, "w").write("param set-default MC_INDI_ACT_TC 0.033\n")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = g.main(["--yaml", y, "--params", p, "--airframe", a])
        return rc, buf.getvalue()


def main():
    # class ii mismatches only (ACT_TC, ID_OK), K_R equal as 20 vs 20.0 -> exit 0
    rc, out = run("MC_INDI_K_R 20\nMC_INDI_ACT_TC 0.033\nMC_INDI_ID_OK 1\n")
    assert rc == 0, out
    assert "mismatches: 2 (MC_INDI_ACT_TC:ii, MC_INDI_ID_OK:ii)" in out, out
    assert "| MC_INDI_SAME | 1 | not set -> fw default" in out, out
    # a gain mismatch is class i -> exit 1
    rc, out = run("MC_INDI_K_R 25\n")
    assert rc == 1 and "MC_INDI_K_R:i" in out, out
    # a params key unknown to the yaml counts as class i
    rc, out = run("MC_INDI_BOGUS 1\n")
    assert rc == 1, out
    print("OK")


if __name__ == "__main__":
    main()
