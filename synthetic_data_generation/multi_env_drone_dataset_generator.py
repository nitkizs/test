"""
Multi-environment synthetic data generation for drone detection.

This script:
- Loads a USD scene into multiple parallel environments
- Moves a target drone along randomized trajectories
- Captures RGB and semantic segmentation using Isaac Lab cameras
- Generates YOLO bounding box labels from segmentation
- Saves RGB (Replicator), labels (.txt), and overlay images

Requirements:
- USD must contain semantic label: "target_drone"
- Update USD_PATH and OUTPUT_DIR before running

Run:
./isaaclab.sh -p multi_env_drone_dataset_generator.py --headless --enable_cameras
"""

import argparse
import math
import os
import random
import shutil
import traceback
import glob

from isaaclab.app import AppLauncher

# =========================================================
# Launch
# =========================================================
# Standard Isaac Lab launcher setup.
parser = argparse.ArgumentParser(
    description="Isaac Lab multi-env RGB + bbox + full trajectory capture using BasicWriter"
)
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
# Camera rendering must be enabled for image capture, so the script
# turns it on automatically if the flag was omitted.
if hasattr(args_cli, "enable_cameras") and not args_cli.enable_cameras:
    print("[INFO] --enable_cameras not provided. Enabling automatically.", flush=True)
    args_cli.enable_cameras = True

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# =========================================================
# Imports after launch
# =========================================================
# These imports are placed after AppLauncher so the Isaac Sim runtime is
# already initialized when simulation- and rendering-dependent modules load.
import cv2
import numpy as np
import omni
import omni.replicator.core as rep
import omni.usd
import isaaclab.sim as sim_utils

from isaaclab.sim import SimulationContext
from isaaclab.sensors.camera import Camera, CameraCfg
from isaaclab.utils import convert_dict_to_backend
from pxr import Gf, Usd, UsdGeom

# =========================================================
# CONFIG
# =========================================================
# Source USD scene that will be referenced into every environment.
USD_PATH = "synthetic_data_generation/assets/drone_scene_base.usd"

# Number of cloned environments and spacing between them in world coordinates.
NUM_ENVS = 13
ENV_SPACING = 400

# Camera resolution.
IMAGE_WIDTH = 1280
IMAGE_HEIGHT = 720

# Simulation time step.
PHYSICS_DT = 1.0 / 60.0

# Motion / capture configuration.
FRAMES_PER_SEGMENT = 80
CAPTURE_EVERY_N_STEPS = 3
ROTOR_SPEED = 30.0
BASE_SEED = 42

# Output locations.
OUTPUT_DIR = "synthetic_data_generation/output"
REPLICATOR_DIR = os.path.join(OUTPUT_DIR, "replicator")
LABELS_DIR = os.path.join(OUTPUT_DIR, "labels")
OVERLAY_DIR = os.path.join(OUTPUT_DIR, "overlay")

# Detection label configuration.
YOLO_CLASS_ID = 0
TARGET_LABEL = "target_drone"

# Relative prim paths inside each environment instance.
CAMERA_REL_PATH = "DJI_Mavic_3/Camera"
TARGET_REL_PATH = "DJI_Mavic_04"

# Number of broad trajectory families reused across environments.
# Environments with the same style still differ because each uses its own RNG.
TRAJECTORY_STYLE_COUNT = 4

# Rotor prim paths for the observer drone.
MAVIC3_ROTOR_REL_PATHS = [
    "DJI_Mavic_3/Dummy01/Group04",
    "DJI_Mavic_3/Dummy02/Group02",
    "DJI_Mavic_3/Dummy03/Group01",
    "DJI_Mavic_3/Dummy04/Group03",
]

# Rotor prim paths for the target drone.
MAVIC04_ROTOR_REL_PATHS = [
    "DJI_Mavic_04/Dummy01/Group04",
    "DJI_Mavic_04/Dummy02/Group02",
    "DJI_Mavic_04/Dummy03/Group01",
    "DJI_Mavic_04/Dummy04/Group03",
]

# =========================================================
# Helpers
# =========================================================
def dbg(msg: str):
    """Consistent debug-print helper."""
    print(f"[DEBUG] {msg}", flush=True)


def ensure_clean_dir(path: str):
    """
    Remove an existing directory and recreate it.
    """
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)


def wait_updates(num_frames: int = 30, label: str = "wait_updates"):
    """
    Advance the app update loop for a fixed number of frames.

    This is mainly useful after stage creation and USD referencing so that
    assets, materials and scene graph changes have time to settle.
    """
    dbg(f"ENTER {label}: {num_frames}")
    for i in range(num_frames):
        simulation_app.update()
        if (i + 1) % 10 == 0 or i == num_frames - 1:
            dbg(f"{label}: {i + 1}/{num_frames}")
    dbg(f"EXIT  {label}")


def get_stage():
    """Return the currently active USD stage."""
    return omni.usd.get_context().get_stage()


def get_prim_or_raise(stage: Usd.Stage, prim_path: str):
    """
    Retrieve a prim from the stage and raise a clear error if it is missing.
    """
    prim = stage.GetPrimAtPath(prim_path)
    if not prim.IsValid():
        raise RuntimeError(f"Prim not found: {prim_path}")
    return prim


def get_or_create_translate_op(prim):
    """
    Return the Translate xform op for a prim, creating one if needed.
    """
    xformable = UsdGeom.Xformable(prim)
    for op in xformable.GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
            return op
    return xformable.AddTranslateOp()


def get_existing_or_new_rotate_xyz(prim, allow_create=True):
    """
    Return the RotateXYZ xform op for a prim.
    """
    xform = UsdGeom.Xformable(prim)
    for op in xform.GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeRotateXYZ:
            return op
    if allow_create:
        return xform.AddRotateXYZOp()
    return None


def set_translate_op(prim, xyz):
    """Set a prim's translate op from the provided XYZ values."""
    translate_op = get_or_create_translate_op(prim)
    translate_op.Set(Gf.Vec3d(float(xyz[0]), float(xyz[1]), float(xyz[2])))


def get_local_translation(prim):
    """
    Read a prim's local translation.
    If no explicit translate op exists, return the origin.
    """
    xformable = UsdGeom.Xformable(prim)
    for op in xformable.GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
            value = op.Get()
            return float(value[0]), float(value[1]), float(value[2])
    return 0.0, 0.0, 0.0


def add_usd_reference(stage: Usd.Stage, prim_path: str, usd_path: str, translation_xyz):
    """
    Create an environment root prim, position it, and reference the source USD under it.
    This is how the same scene is cloned into multiple environments.
    """
    dbg(f"Creating env prim at {prim_path}")
    env_prim = stage.DefinePrim(prim_path, "Xform")
    set_translate_op(env_prim, translation_xyz)
    dbg(f"Adding USD reference: {usd_path} -> {prim_path}")
    env_prim.GetReferences().AddReference(usd_path)
    return env_prim


def squeeze_segmentation(seg: np.ndarray) -> np.ndarray:
    """
    Convert semantic segmentation arrays into a 2D ID map.

    Supported input shapes:
                            seg -> (H,W) or (H,W,1)
                            Output:
                            (H,W) segmentation ID map
    """
    seg = np.asarray(seg)

    if seg.ndim == 2:
        return seg

    if seg.ndim == 3 and seg.shape[2] == 1:
        return seg[:, :, 0]

    raise RuntimeError(f"Unexpected semantic segmentation shape: {seg.shape}")


def mask_to_bbox(mask: np.ndarray):
    """
    Convert a binary mask into a bounding box.

    Input:
        mask -> boolean mask

    Output:
        (x_min, y_min, x_max, y_max) or None
    """
    ys, xs = np.where(mask)
    if len(xs) == 0 or len(ys) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def bbox_to_yolo(x_min, y_min, x_max, y_max, img_w, img_h):
    """
    Convert pixel bbox coordinates into YOLO normalized format:
        x_center, y_center, width, height
    """
    x_center = ((x_min + x_max) / 2.0) / img_w
    y_center = ((y_min + y_max) / 2.0) / img_h
    width = (x_max - x_min) / img_w
    height = (y_max - y_min) / img_h
    return x_center, y_center, width, height


def get_target_id_from_seg_info(single_cam_info, target_label):
    """
    Resolve the integer semantic ID corresponding to the desired semantic class name.

    Example semantic metadata:
        {
            "0": {"class": "BACKGROUND"},
            "1": {"class": "UNLABELLED"},
            "2": {"class": "target_drone"}
        }
    """
    seg_info = single_cam_info.get("semantic_segmentation", {})
    id_to_labels = seg_info.get("idToLabels", {})

    target_id = None

    for k, v in id_to_labels.items():
        label_name = None

        if isinstance(v, str):
            label_name = v
        elif isinstance(v, dict):
            label_name = v.get("class", None)

        if label_name == target_label:
            target_id = int(k)
            break

    return target_id, id_to_labels


# =========================================================
# Motion helpers
# =========================================================
def catmull_rom(p0, p1, p2, p3, t):
    """
    Catmull-Rom spline interpolation.

    This gives smooth motion through a sequence of control points.
    """
    return 0.5 * (
        (2 * p1)
        + (-p0 + p2) * t
        + (2 * p0 - 5 * p1 + 4 * p2 - p3) * (t ** 2)
        + (-p0 + 3 * p1 - 3 * p2 + p3) * (t ** 3)
    )


def ease_in_out(t):
    """
    Smooth the progression through a segment.

    This reduces abrupt starts and stops inside each spline segment.
    """
    return 0.5 * (1.0 - math.cos(math.pi * t))


def generate_realistic_target_path(start_pos, rng, env_id):
    """
    Generate a smooth randomized target trajectory for the target drone.
    """
    sx, sy, sz = start_pos[0], start_pos[1], start_pos[2]

    style = env_id % TRAJECTORY_STYLE_COUNT

    # Broad random ranges that create stronger visual diversity across envs
    near_side = rng.uniform(8.0, 20.0)
    far_side = rng.uniform(10.0, 30.0)
    away_dist = rng.uniform(45.0, 120.0)

    low_z = rng.uniform(-3.0, -0.5)
    high_z = rng.uniform(0.5, 4.0)

    zig_x1 = rng.uniform(-15.0, 15.0)
    zig_y1 = rng.uniform(-10.0, 10.0)
    zig_z1 = rng.uniform(-3.0, 3.0)

    zig_x2 = rng.uniform(-18.0, 18.0)
    zig_y2 = rng.uniform(-12.0, 12.0)
    zig_z2 = rng.uniform(-3.5, 3.5)

    final_side_x = rng.uniform(-20.0, 20.0)
    final_side_y = rng.uniform(-12.0, 12.0)
    final_side_z = rng.uniform(-3.0, 3.0)

    if style == 0:
        # Left sweep, then deep forward motion, then wide return
        side_dir = -1.0
        p0 = Gf.Vec3d(sx, sy, sz)
        p1 = Gf.Vec3d(sx + side_dir * near_side, sy, sz + rng.uniform(low_z, high_z))
        p2 = Gf.Vec3d(p1[0] + rng.uniform(-5.0, 5.0), sy + rng.uniform(-4.0, 4.0), sz + away_dist)
        p3 = Gf.Vec3d(p2[0] + zig_x1, p2[1] + zig_y1, p2[2] + zig_z1)
        p4 = Gf.Vec3d(p3[0] + zig_x2, p3[1] + zig_y2, p3[2] + zig_z2)
        p5 = Gf.Vec3d(sx + final_side_x, sy + final_side_y, sz + final_side_z)

    elif style == 1:
        # Right arc with larger height change
        side_dir = 1.0
        p0 = Gf.Vec3d(sx, sy, sz)
        p1 = Gf.Vec3d(sx + side_dir * near_side, sy + rng.uniform(-3.0, 3.0), sz + rng.uniform(1.0, 4.5))
        p2 = Gf.Vec3d(p1[0] + far_side, sy + rng.uniform(-5.0, 5.0), sz + away_dist * 0.7 + rng.uniform(1.0, 6.0))
        p3 = Gf.Vec3d(p2[0] - rng.uniform(5.0, 12.0), p2[1] + zig_y1, p2[2] + zig_z1)
        p4 = Gf.Vec3d(p3[0] - rng.uniform(5.0, 15.0), p3[1] + zig_y2, p3[2] + zig_z2)
        p5 = Gf.Vec3d(sx + final_side_x, sy + final_side_y, sz + rng.uniform(-2.0, 2.0))

    elif style == 2:
        # Mostly forward motion with large far-field lateral drift
        p0 = Gf.Vec3d(sx, sy, sz)
        p1 = Gf.Vec3d(sx + rng.uniform(-4.0, 4.0), sy, sz + rng.uniform(low_z, high_z))
        p2 = Gf.Vec3d(sx + rng.uniform(-8.0, 8.0), sy + rng.uniform(-3.0, 3.0), sz + away_dist)
        p3 = Gf.Vec3d(p2[0] + rng.uniform(-20.0, 20.0), p2[1] + rng.uniform(-10.0, 10.0), p2[2] + rng.uniform(-4.0, 4.0))
        p4 = Gf.Vec3d(p3[0] + rng.uniform(-20.0, 20.0), p3[1] + rng.uniform(-10.0, 10.0), p3[2] + rng.uniform(-4.0, 4.0))
        p5 = Gf.Vec3d(sx + final_side_x, sy + final_side_y, sz + final_side_z)

    else:
        # Strong S-curve
        p0 = Gf.Vec3d(sx, sy, sz)
        p1 = Gf.Vec3d(sx - near_side, sy + rng.uniform(-4.0, 4.0), sz + rng.uniform(-1.0, 3.0))
        p2 = Gf.Vec3d(sx + far_side, sy + rng.uniform(-6.0, 6.0), sz + away_dist * 0.5 + rng.uniform(-2.0, 2.0))
        p3 = Gf.Vec3d(sx - far_side, sy + rng.uniform(-8.0, 8.0), sz + away_dist * 0.85 + rng.uniform(-3.0, 3.0))
        p4 = Gf.Vec3d(sx + rng.uniform(-10.0, 10.0), sy + rng.uniform(-10.0, 10.0), sz + away_dist + rng.uniform(-4.0, 4.0))
        p5 = Gf.Vec3d(sx + final_side_x, sy + final_side_y, sz + final_side_z)

    # Duplicate endpoints to keep spline behavior stable at start and end
    return [p0, p0, p1, p2, p3, p4, p5, p5]


def spin_rotors(angle, mavic3_rotor_ops, mavic04_rotor_ops):
    """
    Spin rotor meshes for both drones.

    This is a visual only effect used to make the scene appear more realistic.
    """
    if len(mavic3_rotor_ops) >= 4:
        if mavic3_rotor_ops[0]:
            mavic3_rotor_ops[0].Set(Gf.Vec3f(0, 0, angle))
        if mavic3_rotor_ops[1]:
            mavic3_rotor_ops[1].Set(Gf.Vec3f(0, 0, -angle))
        if mavic3_rotor_ops[2]:
            mavic3_rotor_ops[2].Set(Gf.Vec3f(0, 0, angle))
        if mavic3_rotor_ops[3]:
            mavic3_rotor_ops[3].Set(Gf.Vec3f(0, 0, -angle))

    if len(mavic04_rotor_ops) >= 4:
        if mavic04_rotor_ops[0]:
            mavic04_rotor_ops[0].Set(Gf.Vec3f(0, 0, angle))
        if mavic04_rotor_ops[1]:
            mavic04_rotor_ops[1].Set(Gf.Vec3f(0, 0, -angle))
        if mavic04_rotor_ops[2]:
            mavic04_rotor_ops[2].Set(Gf.Vec3f(0, 0, angle))
        if mavic04_rotor_ops[3]:
            mavic04_rotor_ops[3].Set(Gf.Vec3f(0, 0, -angle))


def pack_rgb_to_replicator_format(single_cam_data, single_cam_info):
    """
    Pack only RGB into the format expected by Replicator's BasicWriter.
    """
    rep_output = {"annotators": {}}

    rgb_data = single_cam_data["rgb"]
    rgb_info = single_cam_info.get("rgb", None)

    if rgb_info is not None:
        rep_output["annotators"]["rgb"] = {
            "render_product": {
                "data": rgb_data,
                **rgb_info,
            }
        }
    else:
        rep_output["annotators"]["rgb"] = {
            "render_product": {
                "data": rgb_data,
            }
        }

    return rep_output


def save_yolo_and_overlay(
    single_cam_data,
    single_cam_info,
    env_id,
    frame_name,
    label_dir,
    overlay_dir,
):
    """
    Create a YOLO label file and an overlay image for one frame.
    """
    rgb = np.asarray(single_cam_data["rgb"])
    if rgb.dtype != np.uint8:
        rgb = np.clip(rgb, 0, 255).astype(np.uint8)

    seg = squeeze_segmentation(single_cam_data["semantic_segmentation"])

    target_id, id_to_labels = get_target_id_from_seg_info(single_cam_info, TARGET_LABEL)

    label_path = os.path.join(label_dir, frame_name + ".txt")
    overlay_path = os.path.join(overlay_dir, frame_name + ".png")

    # If semantic metadata does not expose the target label in this frame,
    # create an empty label file and continue.
    if target_id is None:
        open(label_path, "w", encoding="utf-8").close()
        return False, None, None

    mask = (seg == target_id)
    bbox = mask_to_bbox(mask)

    # If the target is not visible, still create an empty label file.
    if bbox is None:
        open(label_path, "w", encoding="utf-8").close()
        return False, None, target_id

    x_min, y_min, x_max, y_max = bbox
    xc, yc, w, h = bbox_to_yolo(x_min, y_min, x_max, y_max, IMAGE_WIDTH, IMAGE_HEIGHT)

    with open(label_path, "w", encoding="utf-8") as f:
        f.write(f"{YOLO_CLASS_ID} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")

    overlay = cv2.cvtColor(rgb[:, :, :3], cv2.COLOR_RGB2BGR)
    cv2.rectangle(overlay, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
    cv2.putText(
        overlay,
        f"{TARGET_LABEL}_env{env_id}",
        (x_min, max(0, y_min - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
        1,
        cv2.LINE_AA,
    )
    cv2.imwrite(overlay_path, overlay)

    return True, bbox, target_id


def cleanup_label_jsons(env_rep_dirs):
    """
    Remove Replicator-generated label JSON files after capture completes.

    These files are useful internally for segmentation metadata handling, but they
    are not needed once custom YOLO labels have been written.
    """
    for env_dir in env_rep_dirs:
        json_files = glob.glob(os.path.join(env_dir, "*_labels_*.json"))
        for f in json_files:
            try:
                os.remove(f)
            except Exception as e:
                print(f"[WARN] Could not delete {f}: {e}", flush=True)


# =========================================================
# Main
# =========================================================
try:
    dbg("START")

    if not os.path.exists(USD_PATH):
        raise FileNotFoundError(f"USD not found: {USD_PATH}")

    ensure_clean_dir(OUTPUT_DIR)
    os.makedirs(REPLICATOR_DIR, exist_ok=True)
    os.makedirs(LABELS_DIR, exist_ok=True)
    os.makedirs(OVERLAY_DIR, exist_ok=True)

    env_rep_dirs = []
    env_label_dirs = []
    env_overlay_dirs = []

    # Create output folders for each environment
    for env_id in range(NUM_ENVS):
        rep_dir = os.path.join(REPLICATOR_DIR, f"env_{env_id}")
        label_dir = os.path.join(LABELS_DIR, f"env_{env_id}")
        overlay_dir = os.path.join(OVERLAY_DIR, f"env_{env_id}")

        os.makedirs(rep_dir, exist_ok=True)
        os.makedirs(label_dir, exist_ok=True)
        os.makedirs(overlay_dir, exist_ok=True)

        env_rep_dirs.append(rep_dir)
        env_label_dirs.append(label_dir)
        env_overlay_dirs.append(overlay_dir)

    dbg("Creating new stage")
    omni.usd.get_context().new_stage()
    wait_updates(10, "post_new_stage")

    stage = get_stage()
    if stage is None:
        raise RuntimeError("Failed to create new stage")

    stage.DefinePrim("/World", "Xform")
    stage.DefinePrim("/World/envs", "Xform")

    # Create all environments by referencing the same source USD with different offsets
    env_paths = []
    for env_id in range(NUM_ENVS):
        env_path = f"/World/envs/env_{env_id}"
        env_offset = (env_id * ENV_SPACING, 0.0, 0.0)
        add_usd_reference(stage, env_path, USD_PATH, env_offset)
        env_paths.append(env_path)

    wait_updates(120, "post_reference_load")

    cameras = []
    rep_writers = []
    env_data = []

    # Build one camera and one target handle per environment
    for env_id, env_path in enumerate(env_paths):
        cam_path = f"{env_path}/{CAMERA_REL_PATH}"
        tgt_path = f"{env_path}/{TARGET_REL_PATH}"

        camera_prim = get_prim_or_raise(stage, cam_path)
        target_prim = get_prim_or_raise(stage, tgt_path)

        mavic3_rotor_ops = []
        for rel_path in MAVIC3_ROTOR_REL_PATHS:
            rotor_prim = get_prim_or_raise(stage, f"{env_path}/{rel_path}")
            mavic3_rotor_ops.append(get_existing_or_new_rotate_xyz(rotor_prim, allow_create=True))

        mavic04_rotor_ops = []
        for rel_path in MAVIC04_ROTOR_REL_PATHS:
            rotor_prim = get_prim_or_raise(stage, f"{env_path}/{rel_path}")
            mavic04_rotor_ops.append(get_existing_or_new_rotate_xyz(rotor_prim, allow_create=True))

        # Standard per-environment camera
        camera_cfg = CameraCfg(
            prim_path=cam_path,
            update_period=0,
            height=IMAGE_HEIGHT,
            width=IMAGE_WIDTH,
            data_types=[
                "rgb",
                "semantic_segmentation",
            ],
            spawn=None,
            colorize_semantic_segmentation=False,
        )
        camera = Camera(cfg=camera_cfg)
        cameras.append(camera)

        # One BasicWriter per environment, used only for RGB output
        rep_writer = rep.BasicWriter(
            output_dir=env_rep_dirs[env_id],
            frame_padding=0,
            colorize_instance_id_segmentation=camera.cfg.colorize_instance_id_segmentation,
            colorize_instance_segmentation=camera.cfg.colorize_instance_segmentation,
            colorize_semantic_segmentation=camera.cfg.colorize_semantic_segmentation,
        )
        rep_writers.append(rep_writer)

        env_data.append({
            "env_id": env_id,
            "camera_prim": camera_prim,
            "target_prim": target_prim,
            "mavic3_rotor_ops": mavic3_rotor_ops,
            "mavic04_rotor_ops": mavic04_rotor_ops,
            "angle": 0.0,
            "path_points": None,
            "segment_idx": 1,
            "segment_step": 0,
            "done": False,
        })

    dbg("Creating SimulationContext")
    sim_cfg = sim_utils.SimulationCfg(
        dt=PHYSICS_DT,
        render_interval=1,
        device=args_cli.device,
        render=sim_utils.RenderCfg(
            rendering_mode="quality",
            antialiasing_mode="FXAA",
            enable_shadows=True,
            enable_reflections=False,
            enable_global_illumination=False,
            enable_ambient_occlusion=False,
            samples_per_pixel=8,
            dlss_mode=1,
        ),
    )
    sim = SimulationContext(sim_cfg)

    try:
        sim.set_camera_view([8.0, 8.0, 6.0], [0.0, 0.0, 0.0])
    except Exception:
        pass

    dbg("Calling sim.reset()")
    sim.reset()
    dbg("sim.reset() complete")

    # Warm up the camera buffers before capture begins
    dbg("Cameras warmup started")
    for i in range(20):
        sim.step()
        for camera in cameras:
            camera.update(dt=sim.get_physics_dt())
    dbg("Cameras warmup complete")

    # Initialize one visually distinct path per environment
    for env in env_data:
        env_id = env["env_id"]
        target_start = get_local_translation(env["target_prim"])

        rng = random.Random(BASE_SEED + env_id)
        env["path_points"] = generate_realistic_target_path(target_start, rng, env_id)
        env["segment_idx"] = 1
        env["segment_step"] = 0
        env["done"] = False

        dbg(f"[env_{env_id}] trajectory initialized with high variation")

    env_frame_counts = [0 for _ in range(NUM_ENVS)]
    global_step = 0

    # Continue stepping until every environment has finished its trajectory
    while not all(env["done"] for env in env_data):
        dbg(f"===== STEP {global_step} =====")

        # Update target motion and rotor animation in every active environment
        for env in env_data:
            env_id = env["env_id"]

            if env["done"]:
                continue

            path_points = env["path_points"]
            segment_idx = env["segment_idx"]
            segment_step = env["segment_step"]

            p0 = path_points[segment_idx - 1]
            p1 = path_points[segment_idx]
            p2 = path_points[segment_idx + 1]
            p3 = path_points[segment_idx + 2]

            denom = max(FRAMES_PER_SEGMENT - 1, 1)
            t_linear = segment_step / float(denom)
            t = ease_in_out(t_linear)

            pos = catmull_rom(p0, p1, p2, p3, t)
            set_translate_op(env["target_prim"], pos)

            env["angle"] += ROTOR_SPEED
            spin_rotors(env["angle"], env["mavic3_rotor_ops"], env["mavic04_rotor_ops"])

            env["segment_step"] += 1

            if env["segment_step"] >= FRAMES_PER_SEGMENT:
                env["segment_step"] = 0
                env["segment_idx"] += 1

                if env["segment_idx"] >= len(path_points) - 2:
                    env["done"] = True
                    dbg(f"[env_{env_id}] trajectory complete")

        sim.step()

        # Refresh all cameras after the simulation step
        for env_id, camera in enumerate(cameras):
            camera.update(dt=sim.get_physics_dt())

        # Capture only every configured number of simulation steps
        if global_step % CAPTURE_EVERY_N_STEPS == 0:
            for env_id, camera in enumerate(cameras):
                if "rgb" not in camera.data.output or "semantic_segmentation" not in camera.data.output:
                    dbg(f"[env_{env_id}] outputs not ready")
                    continue

                # Extract one camera's outputs into NumPy arrays
                single_cam_data = convert_dict_to_backend(
                    {k: v[0] for k, v in camera.data.output.items()},
                    backend="numpy",
                )
                single_cam_info = camera.data.info[0]

                frame_name = f"{env_frame_counts[env_id]:06d}"

                # Save RGB image through Replicator
                rep_output = pack_rgb_to_replicator_format(single_cam_data, single_cam_info)
                rep_output["trigger_outputs"] = {"on_time": int(env_frame_counts[env_id])}
                rep_writers[env_id].write(rep_output)

                # Save YOLO label and overlay image manually
                found_bbox, bbox, target_id = save_yolo_and_overlay(
                    single_cam_data=single_cam_data,
                    single_cam_info=single_cam_info,
                    env_id=env_id,
                    frame_name=frame_name,
                    label_dir=env_label_dirs[env_id],
                    overlay_dir=env_overlay_dirs[env_id],
                )

                dbg(
                    f"[env_{env_id}] saved {frame_name}, "
                    f"target_id={target_id}, bbox_found={found_bbox}, bbox={bbox}"
                )
                env_frame_counts[env_id] += 1

        global_step += 1

    wait_updates(20, "final_updates")

    dbg("Cleaning up replicator label JSON files")
    cleanup_label_jsons(env_rep_dirs)

    total_saved = sum(env_frame_counts)
    print(f"[DONE] Saved total frames: {total_saved}", flush=True)
    print(f"[DONE] Capture every N sim steps: {CAPTURE_EVERY_N_STEPS}", flush=True)
    print(f"[DONE] Frames per trajectory segment: {FRAMES_PER_SEGMENT}", flush=True)

    for env_id in range(NUM_ENVS):
        print(f"[DONE] env_{env_id}: {env_frame_counts[env_id]} frames", flush=True)
        print(f"       Replicator: {env_rep_dirs[env_id]}", flush=True)
        print(f"       Labels: {env_label_dirs[env_id]}", flush=True)
        print(f"       Overlay: {env_overlay_dirs[env_id]}", flush=True)

except Exception as e:
    print("[ERROR]", str(e), flush=True)
    traceback.print_exc()

finally:
    simulation_app.close()

