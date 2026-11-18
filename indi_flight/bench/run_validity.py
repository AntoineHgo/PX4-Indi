"""Run-validity check: did a G3 simulation fly the controller it was labelled with? (S121: ~94 "indi" runs flew PID.)

check_run(ulog_path, requested_params, controller) -> {"valid", "problems", "checked"}.
Params are compared against the ulog's initial_parameters ONLY (not changed_parameters): the runner applies its
params at boot, so the initial values are the ones that count.
MC_RATE_CTL_TYPE is a boot alias that run_scenario maps to MC_INDI_EN; it is absent from the log, so when absent it
is not compared (the controller check on MC_INDI_EN covers it). Pure python; loads only the topics it needs.
"""
import statistics

RATE_TOPIC = "indi_rate_status"
POS_TOPIC = "indi_pos_status"
REL_TOL = 1e-4
ALIASED = ("MC_RATE_CTL_TYPE",)
PARAM_ALIAS = {"CA_R_W_MAX": "MC_INDI_W_MAX"}  # run_scenario.py:826 renames it for indi runs


def _close(a, b):
    return abs(a - b) <= REL_TOL * max(abs(a), abs(b), 1e-12)


def _load(ulog_path):
    from pyulog import ULog
    return ULog(ulog_path, [RATE_TOPIC, POS_TOPIC])


def _topic_rate(ulog, name):
    """(present, n_samples, median_rate_hz or None) for topic `name` (multi_id 0 only if several)."""
    ds = [d for d in ulog.data_list if d.name == name]
    if not ds:
        return False, 0, None
    d = ds[0]
    ts = [float(t) for t in d.data["timestamp"]]
    if len(ts) < 2:
        return len(ts) > 0, len(ts), None
    dts = [b - a for a, b in zip(ts, ts[1:]) if b > a]
    if not dts:
        return True, len(ts), None
    return True, len(ts), 1e6 / statistics.median(dts)


def check_run(ulog_path, requested_params, controller, expected_rate_hz=800.0, _ulog=None):
    problems, checked = [], {}
    try:
        ulog = _ulog if _ulog is not None else _load(ulog_path)
    except Exception as e:  # noqa: BLE001 - unreadable log is itself an invalid run
        return {"valid": False, "problems": [f"cannot read ulog: {e}"], "checked": checked}
    init = ulog.initial_parameters
    if controller not in ("indi", "pid"):
        problems.append(f"unknown controller {controller!r}")

    cmp = {}
    for name, want in requested_params.items():
        try:
            want = float(want)
        except (TypeError, ValueError):
            problems.append(f"param {name}: non-numeric requested value {want!r}")
            continue
        if controller == "indi" and name in PARAM_ALIAS:
            name = PARAM_ALIAS[name]  # the runner applied the value under the translated name
        if name not in init:
            if name in ALIASED:
                cmp[name] = {"want": want, "got": None, "note": "boot alias, covered by MC_INDI_EN"}
                continue
            problems.append(f"param {name}: requested {want:g}, missing in log")
            cmp[name] = {"want": want, "got": None}
            continue
        got = float(init[name])
        cmp[name] = {"want": want, "got": got}
        if not _close(want, got):
            problems.append(f"param {name}: requested {want:g}, log has {got:g}")
    checked["params"] = cmp

    present, n, rate = _topic_rate(ulog, RATE_TOPIC)
    en = init.get("MC_INDI_EN")
    checked.update({"MC_INDI_EN": en, "indi_rate_status_n": n, "indi_rate_status_hz": rate})
    if controller == "indi":
        if en is None or float(en) != 1:
            problems.append(f"indi run but MC_INDI_EN = {en} in log")
        if not present or n == 0:
            problems.append("indi run but no indi_rate_status samples in log")
        elif rate is None or rate < 0.8 * expected_rate_hz:
            problems.append(f"indi_rate_status median rate {rate} Hz < 0.8 x {expected_rate_hz:g}")
        pos_req = requested_params.get("MC_INDI_POS_EN")
        if pos_req is not None and float(pos_req) == 1:
            pp, pn, _ = _topic_rate(ulog, POS_TOPIC)
            checked["indi_pos_status_n"] = pn
            if not pp or pn == 0:
                problems.append("MC_INDI_POS_EN 1 requested but no indi_pos_status samples in log")
    elif controller == "pid":
        if present and n > 0:
            problems.append(f"pid run but indi_rate_status has {n} samples")
        if en is not None and float(en) == 1:
            problems.append("pid run but MC_INDI_EN = 1 in log")
    return {"valid": not problems, "problems": problems, "checked": checked}
