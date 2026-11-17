#!/usr/bin/env python3
"""G1.7 provenance of a run (owner answer Q4, S50).

A gate-bearing run records: repository commit and clean-tree flag, the commit the SITL binary was built from
(PX4_GIT_VERSION_STR of the build's generated version header), the binary's SHA-256, and SHA-256 of every input file
(world, sim model files, params files). refusal() returns the reason a gate-bearing run must not start, or None.
Rule: tracked tree clean, binary commit == HEAD, version header not newer than the binary.
"""
import hashlib
import os
import re
import subprocess


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(repo, *a):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True).stdout.strip()


def binary_commit(build):
    """Commit the build was configured from, read from its generated version header (None if absent)."""
    hdr = os.path.join(build, "src", "lib", "version", "build_git_version.h")
    if not os.path.exists(hdr):
        return None, None
    m = re.search(r'#define\s+PX4_GIT_VERSION_STR\s+"([0-9a-f]+)"', open(hdr, encoding="utf-8").read())
    return (m.group(1) if m else None), hdr


def collect(repo, build, files):
    """Provenance dict. files: input files to hash (missing ones are recorded as None)."""
    binary = os.path.join(build, "bin", "px4")
    bcommit, hdr = binary_commit(build)
    return {
        "commit": _git(repo, "rev-parse", "HEAD"),
        "dirty": bool(_git(repo, "status", "--porcelain", "--untracked-files=no")),
        "binary": binary,
        "binary_sha256": sha256(binary) if os.path.exists(binary) else None,
        "binary_commit": bcommit,
        "header_newer_than_binary": bool(hdr and os.path.exists(binary)
                                         and os.path.getmtime(hdr) > os.path.getmtime(binary)),
        "files_sha256": {f: (sha256(f) if f and os.path.exists(f) else None) for f in files if f},
    }


def refusal(prov):
    if prov["dirty"]:
        return "tracked tree is dirty"
    if not prov["binary_sha256"]:
        return "SITL binary missing"
    if not prov["binary_commit"]:
        return "binary commit unknown (no build_git_version.h)"
    if prov["binary_commit"] != prov["commit"]:
        return f"binary built from {prov['binary_commit'][:10]}, HEAD is {prov['commit'][:10]}: rebuild"
    if prov["header_newer_than_binary"]:
        return "version header newer than the binary: build did not finish"
    missing = [f for f, h in prov["files_sha256"].items() if h is None]
    if missing:
        return f"input files missing: {missing}"
    return None
