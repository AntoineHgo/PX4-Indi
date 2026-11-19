from pyulog import ULog
for p in ["indi_flight/results/smoke_s128_idok0/flight.ulg", "indi_flight/results/smoke_s129_posctl/flight.ulg"]:
    ul = ULog(p); t0 = ul.start_timestamp
    D = {d.name: d.data for d in ul.data_list}
    vc = D["vehicle_command"]; ct = (vc["timestamp"] - t0) * 1e-6
    out = [(round(float(ct[i]), 2), int(vc["command"][i])) for i in range(len(ct)) if int(vc["command"][i]) in (21, 22, 400, 176)]
    vs = D["vehicle_status"]; nt = (vs["timestamp"] - t0) * 1e-6
    ch = [(round(float(nt[i+1]), 2), int(vs["nav_state"][i+1])) for i in range(len(nt)-1) if vs["nav_state"][i+1] != vs["nav_state"][i]]
    print(p.split("/")[1], "cmds", out, "nav", ch)
