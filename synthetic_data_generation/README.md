# Synthetic Data Generation for Drone Detection (Isaac Lab)

## Overview
This module generates synthetic training data for drone detection using NVIDIA Isaac Lab.

A single USD scene is replicated into multiple parallel environments. A target drone
moves along randomized trajectories while a fixed observer camera captures data.

The pipeline produces:
- RGB images (via Replicator)
- YOLO bounding box labels
- Overlay images (for validation)

---

## Installation

### 1. Install Isaac Sim
Follow the official NVIDIA documentation:  
https://docs.isaacsim.omniverse.nvidia.com/latest/installation/index.html

### 2. Install Isaac Lab
Follow:  
https://isaac-sim.github.io/IsaacLab/main/source/setup/installation.html

> Isaac Lab requires Isaac Sim to be installed first.

---

## Setup

### 1. Prepare the USD Scene

Place your USD file inside this repository:

```

synthetic_data_generation/assets/two_drones1.usd

```
---

### 2. Configure Paths

Open the script:

```

multi_env_drone_dataset_generator.py

````

Update the following variables if needed:

```python
USD_PATH = "synthetic_data_generation/assets/two_drones1.usd"
OUTPUT_DIR = "synthetic_data_generation/output"
````

---

## Run

### 1. Activate Isaac Lab environment

```bash
conda activate isaaclab
```

---

### 2. Navigate to Isaac Lab directory

```bash
cd IsaacLab
```

---

### 3. Execute the script

```bash
./isaaclab.sh -p synthetic_data_generation/multi_env_drone_dataset_generator.py --headless --enable_cameras
```

---

### Optional (with GUI)

```bash
./isaaclab.sh -p synthetic_data_generation/multi_env_drone_dataset_generator.py --enable_cameras
```

---

## Output Structure

```
OUTPUT_DIR/
├── replicator/   # RGB images
├── labels/       # YOLO annotations (.txt)
└── overlay/      # Images with bounding boxes (debug)
```

---

## How it Works (Brief)

* Isaac Lab launches Isaac Sim internally
* The script replicates a USD scene into multiple environments
* Each environment runs in parallel
* A camera captures:

  * RGB images
  * semantic segmentation
* Segmentation is processed to:

  * extract target mask
  * compute bounding box
  * generate YOLO labels

---

## Key Notes

* Camera is fixed (observer drone does not move)
* Only the target drone is animated
* Target is identified using semantic label:

  ```
  target_drone
  ```
* Replicator is used only for RGB image saving
* Labels are generated manually from segmentation

---

## Use Case

* Synthetic dataset generation
* Multi-environment parallel data collection
* Training object detection models (e.g., YOLO)

---
