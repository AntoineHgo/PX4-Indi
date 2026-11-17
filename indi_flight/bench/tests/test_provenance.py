#!/usr/bin/env python3
"""Self-test of provenance.py (G1.7) on a throw-away git repository with a fake build."""
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import provenance as pv  # noqa: E402

ok = True


def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name)
    ok &= bool(cond)


with tempfile.TemporaryDirectory() as d:
    repo, build = os.path.join(d, "repo"), os.path.join(d, "build")
    os.makedirs(repo)
    g = lambda *a: subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t", *a],  # noqa: E731
                                  capture_output=True, text=True, check=True).stdout.strip()
    g("init", "-q")
    model = os.path.join(repo, "model.sdf")
    open(model, "w").write("<sdf/>")
    g("add", "model.sdf")
    g("commit", "-qm", "c1")
    head = g("rev-parse", "HEAD")

    os.makedirs(os.path.join(build, "src", "lib", "version"))
    os.makedirs(os.path.join(build, "bin"))
    hdr = os.path.join(build, "src", "lib", "version", "build_git_version.h")

    def make_build(commit):
        open(hdr, "w").write(f'#define PX4_GIT_VERSION_STR "{commit}"\n')
        time.sleep(0.01)
        open(os.path.join(build, "bin", "px4"), "wb").write(b"\x7fELF" + commit.encode())

    make_build(head)
    p = pv.collect(repo, build, [model])
    check("clean tree + matching binary accepted", pv.refusal(p) is None)
    check("binary commit read", p["binary_commit"] == head)
    check("model hash recorded", p["files_sha256"][model] == pv.sha256(model) and len(p["files_sha256"][model]) == 64)

    open(model, "w").write("<sdf>changed</sdf>")
    check("dirty tree refused", "dirty" in (pv.refusal(pv.collect(repo, build, [model])) or ""))
    g("commit", "-qam", "c2")
    check("stale binary refused", "rebuild" in (pv.refusal(pv.collect(repo, build, [model])) or ""))

    make_build(g("rev-parse", "HEAD"))
    check("rebuilt binary accepted", pv.refusal(pv.collect(repo, build, [model])) is None)
    os.utime(hdr, (time.time() + 10, time.time() + 10))
    check("header newer than binary refused", "did not finish" in (pv.refusal(pv.collect(repo, build, [model])) or ""))
    os.utime(hdr, (0, 0))
    check("missing input refused", "missing" in (pv.refusal(pv.collect(repo, build, [model, model + ".x"])) or ""))
    os.remove(os.path.join(build, "bin", "px4"))
    check("missing binary refused", "missing" in (pv.refusal(pv.collect(repo, build, [model])) or ""))

print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
