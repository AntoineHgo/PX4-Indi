"""Harness status of a G3 run directory, shared by both G3 scorers (g3_score.sh key 1, g3_checks_key2.py key 2).
A run the harness aborted (wall timeout, land timeout, runner exception, watchdog, void params) is INVALID: it is re-flown,
never scored PASS (Q27 item 8). Status sources: run.json (exit_status, error, g3_outcome) and g3_done.json (outcome).
Usage: python3 g3_run_status.py RUN_DIR  -> prints 'ok' or 'INVALID <reason>' (exit 0 / 3)."""
import json
import os
import sys


def invalid_reason(run_dir):
    """None if the runner finished the run cleanly, else a short reason string (fail closed: missing status = invalid)."""
    def load(n):
        try:
            with open(os.path.join(run_dir, n)) as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return None
    rj, gd = load("run.json"), load("g3_done.json")
    if rj is None:
        return "run.json missing or unreadable"
    why = []
    if rj.get("exit_status") != "ok":
        why.append(f"exit_status {rj.get('exit_status')!r}")
    if rj.get("error"):
        why.append("error: " + " ".join(str(rj["error"]).split())[:200])
    if rj.get("g3_outcome") not in (None, "ok"):
        why.append(f"g3_outcome {rj['g3_outcome']!r}")
    if gd is not None and gd.get("outcome") != "ok":
        why.append(f"g3_done outcome {gd.get('outcome')!r}")
    return "; ".join(why) or None


if __name__ == "__main__":
    r = invalid_reason(sys.argv[1])
    print("ok" if r is None else "INVALID " + r)
    sys.exit(0 if r is None else 3)
