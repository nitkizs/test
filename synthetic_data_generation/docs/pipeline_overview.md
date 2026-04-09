
# Pipeline Overview

## Overview

This pipeline generates synthetic training data for drone detection by combining
multi-environment simulation, camera-based sensing and post-processing.

A single USD scene is replicated into multiple environments, simulated in parallel,
and used to produce RGB images and YOLO annotations.

---

## End-to-End Flow

```

USD Scene
↓
Environment Replication
↓
Simulation (Target Motion)
↓
Camera Capture (RGB + Segmentation)
↓
Post-processing (Mask → Bounding Box → YOLO)
↓
Dataset Output

```

---

## 1. Scene Initialization

- A pre-built USD scene is used as input
- The scene must include:
  - a **target drone** (semantic label: `target_drone`)
  - an **observer drone with a camera**

---

## 2. Multi-Environment Replication

- The scene is cloned into multiple environments:

```

/World/envs/env_0
/World/envs/env_1
...

```

- Each environment is spatially offset to avoid overlap
- All environments are simulated **in parallel within a single stage**

---

## 3. Simulation and Motion

- The **target drone is animated**
- Motion is generated using:
  - Catmull-Rom spline interpolation
  - easing for smooth transitions
- Multiple trajectory variations are used across environments
- Rotor motion is applied for visual realism
- The **camera remains fixed**

---

## 4. Camera Capture

Each environment contains one camera configured with:

- RGB output
- Semantic segmentation output

At each capture step:
- camera data is updated
- outputs are retrieved per environment

---

## 5. Label Generation

Bounding boxes are derived from semantic segmentation:

1. Extract segmentation map
2. Resolve target class ID using label:
```

target_drone

```
3. Create binary mask of target pixels
4. Compute bounding box from mask
5. Convert to YOLO format:
```

class_id x_center y_center width height

```

---

## 6. Output Generation

For each environment and frame:

- **RGB images**
- saved using Replicator (`BasicWriter`)
- **YOLO labels**
- saved as `.txt` files
- **Overlay images**
- bounding boxes drawn for validation

---

## System Roles

| Component      | Responsibility                     |
|---------------|----------------------------------|
| Isaac Sim     | Rendering and physics simulation |
| Isaac Lab     | Multi-environment orchestration  |
| Camera        | Data capture (RGB + segmentation)|
| Replicator    | Efficient RGB image writing      |

---



