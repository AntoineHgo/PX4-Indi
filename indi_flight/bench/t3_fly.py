#!/usr/bin/env python3
"""T3: fly the quad5in reference airframe with the stock PID inside the px4-indi-sim container.
Usage (container): python3 indi_flight/bench/t3_fly.py --out indi_flight/results/t3_ref_airframe/run1 [--model quad5in]
Flight: takeoff to 3 m, hover 20 s, offboard: +1 m altitude step (8 s), +2 m x step (8 s), back (8 s), +45 deg yaw step (5 s), land.
Model resolution: PX4_GZ_MODELS is pointed at indi_flight/sim/models (px4-rc.gzsim spawns $PX4_GZ_MODELS/<model>/model.sdf),
and the original paths stay on GZ_SIM_RESOURCE_PATH (gz_env.sh); the model's quad5in_base include resolves through it.
"""
import argparse, glob, json, os, shutil, subprocess, sys, time

REPO = os.environ.get("PX4_INDI_REPO", os.getcwd())
BUILD = f"{REPO}/build/px4_sitl_default"
MODELS = f"{REPO}/indi_flight/sim/models"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="quad5in")
    ap.add_argument("--alt", type=float, default=3.0)
    ap.add_argument("--params", default="", help="comma list NAME=VALUE applied before arming")
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out + "/rootfs")
    src = subprocess.run(["bash", "-c", f"source {BUILD}/gz_env.sh; env -0"], capture_output=True, check=True).stdout
    env = dict(kv.split("=", 1) for kv in src.decode().split("\0") if "=" in kv)
    env.update(HEADLESS="1", PX4_SIM_MODEL=f"gz_{a.model}", PX4_GZ_MODELS=MODELS)
    env["GZ_SIM_RESOURCE_PATH"] = MODELS + ":" + env.get("GZ_SIM_RESOURCE_PATH", "")
    procs = []

    def spawn(argv, log):
        p = subprocess.Popen(argv, env=env, stdout=open(f"{out}/{log}", "w"), stderr=subprocess.STDOUT,
                             start_new_session=True, cwd=out)
        procs.append(p)
        return p

    def cli(tool, *args):
        r = subprocess.run([f"{BUILD}/bin/{tool}", *args], capture_output=True, text=True, timeout=30, env=env)
        return r.stdout + r.stderr

    try:
        spawn(["gz", "sim", "--verbose=1", "-r", "-s", f"{env['PX4_GZ_WORLDS']}/default.sdf"], "gz.log")
        t0 = time.time()
        while "/world/default/clock" not in subprocess.run(["gz", "topic", "-l"], capture_output=True, text=True,
                                                           env=env).stdout:
            assert time.time() - t0 < 120, "gz did not start"
            time.sleep(1)
        px4 = spawn([f"{BUILD}/bin/px4", "-d", "-w", out + "/rootfs", f"{BUILD}/etc"], "px4.log")
        t0 = time.time()
        while "Startup script returned successfully" not in open(f"{out}/px4.log", errors="replace").read():
            assert px4.poll() is None and time.time() - t0 < 180, "px4 startup failed"
            time.sleep(1)
        info = subprocess.run(["gz", "model", "-m", f"{a.model}_0"], capture_output=True, text=True, env=env)
        open(f"{out}/gz_model_info.txt", "w").write(info.stdout + info.stderr)
        params = {"NAV_DLL_ACT": 0, "COM_RC_IN_MODE": 4, "COM_RCL_EXCEPT": 4, "SDLOG_PROFILE": 17,
                  "MIS_TAKEOFF_ALT": a.alt, "COM_DISARM_LAND": 2}
        for kv in filter(None, a.params.split(",")):
            k, v = kv.split("=")
            params[k] = float(v)
        for k, v in params.items():
            cli("px4-param", "set", k, str(v))
        cli("px4-logger", "stop"); time.sleep(1); cli("px4-logger", "start", "-t")
        open(f"{out}/params_used.txt", "w").write(cli("px4-param", "show", "-q", "MPC_THR_HOVER") +
                                                  cli("px4-param", "show", "-q", "MC_*RATE_*"))
        from pymavlink import mavutil
        mav = mavutil.mavlink_connection("udpin:0.0.0.0:14540", source_system=255)
        assert mav.wait_heartbeat(timeout=60), "no heartbeat"
        sysid = mav.target_system
        for mid, hz in ((30, 100), (32, 50), (245, 2)):
            mav.mav.command_long_send(sysid, 1, 511, 0, mid, 1e6 / hz, 0, 0, 0, 0, 0)
        st = {"t": 0.0, "pos": None, "landed": None, "armed": False, "yaw": 0.0}

        def pump(timeout=2.0):
            m = mav.recv_match(blocking=True, timeout=timeout)
            if m is None:
                return False
            ty = m.get_type()
            if ty == "ATTITUDE":
                st["t"] = m.time_boot_ms * 1e-3
                st["yaw"] = m.yaw
                return True
            if ty == "LOCAL_POSITION_NED":
                st["pos"] = (m.x, m.y, m.z)
            elif ty == "EXTENDED_SYS_STATE":
                st["landed"] = m.landed_state
            elif ty == "HEARTBEAT" and m.get_srcSystem() == sysid and m.type != 6:
                st["armed"] = bool(m.base_mode & 128)
            return ty == "ATTITUDE"

        def run(dur=None, until=None, sp=None, wall=300):
            w0, t0, nxt = time.time(), st["t"], st["t"]
            while time.time() - w0 < wall:
                if until and until():
                    return True
                if dur is not None and st["t"] - t0 >= dur:
                    return True
                if pump() and sp and st["t"] >= nxt:
                    sp(); nxt = st["t"] + 0.02
            raise RuntimeError("wall timeout")

        log = {}
        t0 = time.time()
        while "Ready for takeoff" not in open(f"{out}/px4.log", errors="replace").read():
            assert time.time() - t0 < 180, "not ready"
            time.sleep(1)
        run(dur=2)
        for _ in range(5):
            cli("px4-commander", "takeoff")
            run(dur=3)
            if st["armed"]:
                break
        assert st["armed"], "not armed"
        log["t_arm"] = st["t"]
        run(until=lambda: st["pos"] and -st["pos"][2] > a.alt - 0.15, wall=120)
        log["t_at_alt"] = st["t"]
        run(dur=20)  # hover 20 s (stock takeoff hold)
        log["t_hover_end"] = st["t"]
        p0 = st["pos"]
        tgt = {"p": (p0[0], p0[1], p0[2]), "yaw": st["yaw"]}
        yaw0 = st["yaw"]; log["yaw0"] = yaw0

        def sp():
            p = tgt["p"]
            mav.mav.set_position_target_local_ned_send(int(st["t"] * 1e3), sysid, 1, 1, 0b100111111000,
                                                       p[0], p[1], p[2], 0, 0, 0, 0, 0, 0, tgt["yaw"], 0)
        run(dur=1.0, sp=sp)  # stream setpoints before offboard
        mav.mav.command_long_send(sysid, 1, 176, 0, 1, 6, 0, 0, 0, 0, 0)
        run(dur=3, sp=sp)
        log["t_step_alt"] = st["t"]
        tgt["p"] = (p0[0], p0[1], p0[2] - 1.0); run(dur=8, sp=sp)
        log["t_step_x"] = st["t"]
        tgt["p"] = (p0[0] + 2.0, p0[1], p0[2] - 1.0); run(dur=8, sp=sp)
        log["t_back"] = st["t"]
        tgt["p"] = (p0[0], p0[1], p0[2]); run(dur=8, sp=sp)
        log["t_step_yaw"] = st["t"]
        tgt["yaw"] = yaw0 + 0.7854; run(dur=5, sp=sp)
        log["t_land_cmd"] = st["t"]
        cli("px4-commander", "land")
        run(until=lambda: not st["armed"], wall=180)
        log["t_disarm"] = st["t"]
        log["p0"] = p0
        json.dump(log, open(f"{out}/phases.json", "w"), indent=1)
        print("phases", log)
    finally:
        cli("px4-shutdown")
        time.sleep(3)
        for p in procs:
            try:
                os.killpg(p.pid, 15)
            except Exception:
                pass
        ul = sorted(glob.glob(f"{out}/rootfs/**/*.ulg", recursive=True))
        if ul:
            shutil.copy(ul[-1], f"{out}/flight.ulg")
            print("ulog", ul[-1])


if __name__ == "__main__":
    main()
