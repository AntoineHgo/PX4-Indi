"""Per-run Gazebo model variants for plant-mismatch scenarios (T9 now, held-out H5 later).

A scenario sets  model_variant=dict(ixx=1.3, iyy=1.3)  (multiplicative scale factors on the stock x500 values).
Supported keys:
  ixx, iyy, izz   base_link <inertia> diagonal terms (x500_base/model.sdf)
  mass            base_link <mass> (x500_base/model.sdf); propeller link masses are left unchanged
  tau             motor timeConstantUp and timeConstantDown of all four rotors (x500/model.sdf)
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
ALLOWED = INERTIA_KEYS + ("mass", "tau", "rpm")


def _copy_model(src, dst, real=("model.sdf", "model.config")):
    os.makedirs(dst, exist_ok=True)
    for name in os.listdir(src):
        s, d = os.path.join(src, name), os.path.join(dst, name)
        if name in real:
            shutil.copy(s, d)
        else:
            os.symlink(s, d)


def build_variant(spec, out_dir, stock_models):
    """Returns (variant_models_dir, record). record holds original and new values for run.json."""
    bad = set(spec) - set(ALLOWED)
    if bad:
        raise ValueError(f"unknown model_variant keys {sorted(bad)}; allowed {ALLOWED}")
    root = os.path.join(os.path.abspath(out_dir), "model_variant")
    shutil.rmtree(root, ignore_errors=True)
    for m in ("x500", "x500_base"):
        _copy_model(os.path.join(stock_models, m), os.path.join(root, m))
    rec = {"scale": dict(spec), "dir": root, "stock_models": stock_models, "original": {}, "new": {}}

    base_path = os.path.join(root, "x500_base", "model.sdf")
    tree = ET.parse(base_path)
    inertial = None
    for link in tree.getroot().iter("link"):
        if link.get("name") == "base_link":
            inertial = link.find("inertial")
            break
    if inertial is None:
        raise RuntimeError("base_link <inertial> not found in x500_base/model.sdf")
    for key in ALLOWED[:4]:
        if key in spec:
            el = inertial.find("mass") if key == "mass" else inertial.find("inertia").find(key)
            old = float(el.text)
            el.text = repr(old * spec[key])
            rec["original"][key], rec["new"][key] = old, old * spec[key]
    tree.write(base_path)

    if "tau" in spec:
        x_path = os.path.join(root, "x500", "model.sdf")
        tree = ET.parse(x_path)
        n = 0
        for tag in ("timeConstantUp", "timeConstantDown"):
            for el in tree.getroot().iter(tag):
                old = float(el.text)
                rec["original"].setdefault(tag, []).append(old)
                el.text = repr(old * spec["tau"])
                rec["new"].setdefault(tag, []).append(old * spec["tau"])
                n += 1
        if n != 8:
            raise RuntimeError(f"expected 8 motor time constants in x500/model.sdf, found {n}")
        tree.write(x_path)

    if spec.get("rpm"):
        x_path = os.path.join(root, "x500", "model.sdf")
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
