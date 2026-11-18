"""Per-run Gazebo model variants for plant-mismatch scenarios (T9 now, held-out H5 later).

A scenario sets  model_variant=dict(ixx=1.3, iyy=1.3)  (multiplicative scale factors on the stock x500 values).
Supported keys:
  ixx, iyy, izz   base_link <inertia> diagonal terms (x500_base/model.sdf)
  mass            base_link <mass> (x500_base/model.sdf); propeller link masses are left unchanged
  tau             motor timeConstantUp and timeConstantDown of all four rotors (x500/model.sdf)
  tau_up          timeConstantUp only (multiplies with tau); for the asymmetric-actuator scenario (V2)
  tau_down        timeConstantDown only (multiplies with tau)
  imu_rate        x500_base imu_sensor <update_rate> in Hz (stock 250). The physics step is NOT coupled to it
                  (D-SIM-STEP: every run uses indi_flight/sim/worlds/default.sdf, 1.25 ms)
  rpm             True: add a JointStatePublisher (every physics step) to x500, the stage-2 rotor speed source
                  read by GZBridge when SIM_GZ_ESC_FB=1 (plan/s2_rotor_speed.md); no effect on the dynamics

build_variant() copies x500 and x500_base into <out>/model_variant/ (meshes/materials/thumbnails are symlinked,
only model.sdf and model.config are real copies), edits the copies, and returns the directory. The caller sets
PX4_GZ_MODELS to it (px4-rc.gzsim spawns file://$PX4_GZ_MODELS/x500/model.sdf) and prepends it to
GZ_SIM_RESOURCE_PATH (x500 includes model://x500_base). Tools/simulation/gz/models is never modified.
"""
import os
import shutil
import xml.etree.ElementTree as ET

INERTIA_KEYS = ("ixx", "iyy", "izz")
ALLOWED = INERTIA_KEYS + ("mass", "tau", "rpm", "imu_rate", "tau_up", "tau_down")


def _copy_model(src, dst, real=("model.sdf", "model.config")):
    os.makedirs(dst, exist_ok=True)
    for name in os.listdir(src):
        s, d = os.path.join(src, name), os.path.join(dst, name)
        if name in real:
            shutil.copy(s, d)
        else:
            os.symlink(s, d)


def build_variant(spec, out_dir, stock_models, model="x500"):
    """Returns (variant_models_dir, record). record holds original and new values for run.json.

    model="quad5in": same keys, on quad5in/quad5in_base. mass also scales the four rotor link masses (total mass x factor,
    like the x500 note above the rotor links keep their physical <inertia>, which is never touched); rpm is not
    supported (quad5in already carries a per-step JointStatePublisher).
    """
    bad = set(spec) - set(ALLOWED)
    if bad:
        raise ValueError(f"unknown model_variant keys {sorted(bad)}; allowed {ALLOWED}")
    root = os.path.join(os.path.abspath(out_dir), "model_variant")
    shutil.rmtree(root, ignore_errors=True)
    if model not in ("x500", "quad5in"):
        raise ValueError(f"unknown model {model}")
    if model == "quad5in" and spec.get("rpm"):
        raise ValueError("rpm is x500-only; quad5in already has the JointStatePublisher")
    base = model + "_base"
    for m in (model, base):
        _copy_model(os.path.join(stock_models, m), os.path.join(root, m))
    rec = {"model": model, "scale": dict(spec), "dir": root, "stock_models": stock_models, "original": {}, "new": {}}

    base_path = os.path.join(root, base, "model.sdf")
    tree = ET.parse(base_path)
    inertial = None
    for link in tree.getroot().iter("link"):
        if link.get("name") == "base_link":
            inertial = link.find("inertial")
            break
    if inertial is None:
        raise RuntimeError("base_link <inertial> not found in " + base + "/model.sdf")
    for key in ALLOWED[:4]:
        if key in spec:
            el = inertial.find("mass") if key == "mass" else inertial.find("inertia").find(key)
            old = float(el.text)
            el.text = repr(old * spec[key])
            rec["original"][key], rec["new"][key] = old, old * spec[key]
    if model == "quad5in" and "mass" in spec:
        rm = []
        for link in tree.getroot().iter("link"):
            if link.get("name", "").startswith("rotor_"):
                el = link.find("inertial").find("mass")
                old = float(el.text)
                el.text = repr(old * spec["mass"])
                rm.append((old, old * spec["mass"]))
        if len(rm) != 4:
            raise RuntimeError(f"expected 4 rotor links in {base}/model.sdf, found {len(rm)}")
        rec["original"]["rotor_mass"], rec["new"]["rotor_mass"] = [a for a, _ in rm], [b for _, b in rm]
    if "imu_rate" in spec:
        sensors = [s for s in tree.getroot().iter("sensor") if s.get("name") == "imu_sensor"]
        if len(sensors) != 1:
            raise RuntimeError("imu_sensor not found in x500_base/model.sdf")
        el = sensors[0].find("update_rate")
        rec["original"]["imu_rate"], rec["new"]["imu_rate"] = float(el.text), float(spec["imu_rate"])
        el.text = str(int(spec["imu_rate"]))
    tree.write(base_path)

    if {"tau", "tau_up", "tau_down"} & set(spec):
        x_path = os.path.join(root, model, "model.sdf")
        tree = ET.parse(x_path)
        n = 0
        for tag, own in (("timeConstantUp", "tau_up"), ("timeConstantDown", "tau_down")):
            factor = spec.get("tau", 1.0) * spec.get(own, 1.0)
            for el in tree.getroot().iter(tag):
                old = float(el.text)
                rec["original"].setdefault(tag, []).append(old)
                el.text = repr(old * factor)
                rec["new"].setdefault(tag, []).append(old * factor)
                n += 1
        if n != 8:
            raise RuntimeError(f"expected 8 motor time constants in {model}/model.sdf, found {n}")
        tree.write(x_path)

    if spec.get("rpm"):
        x_path = os.path.join(root, model, "model.sdf")
        tree = ET.parse(x_path)
        plugin = ET.SubElement(tree.getroot().find("model"), "plugin",
                               filename="gz-sim-joint-state-publisher-system",
                               name="gz::sim::systems::JointStatePublisher")
        for i in range(4):
            ET.SubElement(plugin, "joint_name").text = f"rotor_{i}_joint"
        ET.SubElement(plugin, "update_rate").text = "0"
        tree.write(x_path)
        rec["new"]["joint_state_publisher"] = [f"rotor_{i}_joint" for i in range(4)]
    return root, rec
