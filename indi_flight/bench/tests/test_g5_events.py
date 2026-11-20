"""Synthetic self-test of the G5 event verdict parsing: known applied time and effect -> known verdict."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import g5_events as g


def synth(reset_dt_us=12000, dxy=(0.6, 0.8), dyaw_deg=5.0, kill_flag_dt=3000, out_zero_dt=1250):
    t_app = 100_000_000
    ts = [t_app + k * 2500 - 50000 for k in range(100)]
    n = len(ts)
    cnt = [0 if t < t_app + reset_dt_us else 1 for t in ts]
    lp = {"timestamp": ts, "xy_reset_counter": cnt, "heading_reset_counter": cnt,
          "delta_xy[0]": [dxy[0] if c else 0.0 for c in cnt], "delta_xy[1]": [dxy[1] if c else 0.0 for c in cnt],
          "delta_heading": [g.math.radians(dyaw_deg) if c else 0.0 for c in cnt]}
    kill = [1 if t >= t_app + kill_flag_dt else 0 for t in ts]
    aa = {"timestamp": ts, "kill": kill}
    ao = {"timestamp": ts, **{f"output[{m}]": [0.0 if t >= t_app + kill_flag_dt + out_zero_dt else 0.5 for t in ts]
                              for m in range(4)}}
    fl = {"timestamp": ts, "manual_control_signal_lost": [1 if t >= t_app + 100000 else 0 for t in ts],
          "gcs_connection_lost": [0] * n, "offboard_control_signal_lost": [0] * n}
    h = g.math.radians(dyaw_deg) / 2
    va = {"timestamp": ts, "q[0]": [1.0 if tt < t_app + reset_dt_us else g.math.cos(h) for tt in ts],
          "q[1]": [0.0] * n, "q[2]": [0.0] * n,
          "q[3]": [0.0 if tt < t_app + reset_dt_us else g.math.sin(h) for tt in ts]}
    return {"vehicle_attitude": va, "vehicle_local_position": lp, "actuator_armed": aa, "actuator_outputs": ao, "failsafe_flags": fl}, t_app


def events(t_app, dt_app=0):
    e = lambda n, **k: {"name": n, "t_cmd_us": t_app, "t_applied_us": t_app + dt_app, **k}
    return [e("ekf_yaw"), e("ekf_xy"), e("rc_loss", last_msg_us=t_app - 20000), e("kill")]


class T(unittest.TestCase):
    def line(self, lines, name):
        return [l for l in lines if l.startswith(f"G1.5 {name}:")][0]

    def test_pass(self):
        log, t = synth()
        L = g.analyse(log, events(t, 1000))
        for n in ("ekf_yaw", "ekf_xy", "rc_loss", "kill"):
            self.assertIn(": PASS", self.line(L, n), self.line(L, n))
        self.assertIn("mag=1/1", self.line(L, "ekf_xy"))
        self.assertIn("onset", self.line(L, "rc_loss"))
        self.assertIn("NOT INJECTABLE", self.line(L, "maybe_landed"))

    def test_fail_magnitude(self):
        log, t = synth(dxy=(0.6, 0.85))  # 1.04 m = 4 % off
        self.assertIn(": FAIL", self.line(g.analyse(log, events(t)), "ekf_xy"))
        log, t = synth(dyaw_deg=5.2)  # 4 %
        self.assertIn(": FAIL", self.line(g.analyse(log, events(t)), "ekf_yaw"))

    def test_fail_timing(self):
        log, t = synth()
        l = self.line(g.analyse(log, events(t, 5000)), "ekf_xy")  # applied 5 ms late > 1.25 ms
        self.assertIn(": FAIL", l)
        self.assertIn("applied-commanded", l)

    def test_fail_no_effect(self):
        log, t = synth()
        log["vehicle_local_position"]["xy_reset_counter"] = [0] * 100
        self.assertIn("not visible", self.line(g.analyse(log, events(t)), "ekf_xy"))
        log["vehicle_attitude"]["q[3]"] = [0.0] * 100
        self.assertIn("not visible", self.line(g.analyse(log, events(t)), "ekf_yaw"))

    def test_kill_motors_not_zero(self):
        log, t = synth(out_zero_dt=10 ** 9)
        self.assertIn(": FAIL", self.line(g.analyse(log, events(t)), "kill"))


if __name__ == "__main__":
    unittest.main()
