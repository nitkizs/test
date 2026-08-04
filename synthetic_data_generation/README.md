# Synthetic UAV Dataset Generation Pipeline

This project provides a synthetic data generation pipeline for training vision based UAV detection models using NVIDIA Isaac Sim and Isaac Lab.

The pipeline runs multiple simulation environments in parallel. Each environment contains a fixed observer UAV with a camera and a moving target UAV. RGB images and semantic segmentation are used to identify the target UAV and generate object detection annotations automatically.

To improve dataset diversity, the pipeline applies configurable domain randomization to lighting, observer orientation, target motion, trajectories, and starting poses.

## Features

* Parallel dataset generation across multiple environments
* RGB image capture from simulated cameras
* Target detection using semantic segmentation
* Automatic bounding box extraction
* YOLO format annotation generation
* CVAT-compatible XML annotation generation
* Positive and negative sample generation
* Bounding-box overlay images for visual inspection
* Multiple target motion patterns
* Configurable observer orientations
* HDRI lighting and intensity variation

---

## Pipeline Overview

Each generated environment contains:

* an observer UAV
* a fixed camera attached to the observer UAV
* a moving target UAV

All environments run in parallel within the same simulation.

For each captured frame, the pipeline:

1. reads the RGB and semantic segmentation camera outputs
2. identifies the segmentation ID of the target UAV
3. creates a binary target mask
4. removes invalid or unrelated mask regions
5. calculates and validates the target bounding boX
6. classifies the frame as positive, negative, or skipped
7. saves the RGB image
8. creates the YOLO annotation
9. adds the annotation to the CVAT XML file
10. optionally saves an overlay image for visual checking

---
## Frame Classification

Frames are classified as:

* **Positive:** The target UAV is visible and has a valid bounding box.
* **Negative:** The target UAV is not visible or no valid bounding box is found.
* **Skipped:** The target is visible, but the annotation is too small or unreliable.

Positive and negative frames are saved. Skipped frames are ignored.

---

## Bounding Box Validation

Before an annotation is saved, the pipeline can:

* retain the main connected component
* include nearby mask components
* add configurable padding
* reject extremely small boxes
* reject unreliable border touching detections

---

## Domain Randomization

Randomization is applied at batch, simulation run and environment level.

### Batch-Level Randomization

A batch define:

* the active HDRI environment
* motion pattern assignments
* observer orientation assignments
* domain assignments for each environment

The selected HDRI can remain active for all simulation runs within the same batch.

### Simulation Run Randomization

Each simulation run use:

* a new target uav trajectory
* a different lighting intensity
* reassigned motion patterns when enabled

### Environment Level Variation

Individual environments may use different:

* observer positions
* observer pitch angles
* observer yaw angles
* observer roll angles
* target motion patterns
* trajectory directions
* target starting poses

The randomization behaviour is controlled through the configuration values and seeds.

---

## Lighting

A global USD DomeLight is used for environment lighting.

HDRI selection and lighting intensity can be configured independently.


---

## Requirements

The pipeline requires:

* NVIDIA GPU with a supported driver
* NVIDIA Isaac Sim
* NVIDIA Isaac Lab
* Python dependencies listed in requirements.txt

---

## Installation

### 1. Install Isaac Sim

Follow the official NVIDIA Isaac Sim installation guide:

```text
[https://docs.isaacsim.omniverse.nvidia.com/](https://docs.isaacsim.omniverse.nvidia.com/)
```

### 2. Install Isaac Lab

Follow the official Isaac Lab installation guide:

```text
https://isaac-sim.github.io/IsaacLab/
```

Isaac Sim must be installed and working before installing Isaac Lab.

### 3. Clone the Repository

```bash
git clone git@github.com:DRAIVE/uaiv-synthetic-datagen.git
cd uaiv-synthetic-datagen
```

### 4. Install Project Dependencies

Activate the Isaac Lab environment and run:

```bash
pip install -r requirements.txt
```

---

## Project Structure

A typical project structure is:

```text
uaiv-synthetic-datagen/
├── assets/
│   ├── usd_assets/
│       └── synthetic_data_generation_scene.usd
│       └── UAV_model/
│   └── External_env/
│       └── HDRi/grasslands_sunset_1k.exr
├── scripts/
│   └── config.py
│   └── main.py
│   └── batch_utils.py
│   └── bbox_utils.py
│   └── dataset_utils.py
│   └── hdri_utils.py
│   └── image_utils.py
│   └── legacy_patterns.py
│   └── new_local_patterns.py
│   └── motion_utils.py
│   └── scene_utils.py
│   └── sim_utils_custom.py
│   └── utils.py
│   └── xml_utils.py
└── requirements.txt
└── output/
└── README.md
```


## Configuration

The main project settings are defined in scripts/config.py.

Review the following values before running the pipeline.

### Scene Configuration

```python
USD_PATH = "/path/to/synthetic_data_generation_scene.usd"
OUTPUT_DIR = "/path/to/output"
HDRI_DIR = "/path/to/hdri/files"
```

### Environment Configuration

```python
NUM_ENVS = 2
NUM_LEGACY_ENVS = 1
```

### Batch and Run Configuration

```python
NUM_BATCHES = 1
SIM_RUNS_PER_BATCH = 1
```

---

## Running the Pipeline

A typical headless run is:

```bash
./isaaclab.sh -p path/to/main.py --headless --enable_cameras
```
or

```bash
python path/to/main.py --headless --enable_cameras
```
---

## Output Structure

The generated dataset is organized by batch, environment and frame type.

A typical structure is:

```text
output/
└── batch_000/
    ├── images/
    │   ├── env_0/
    │   │   ├── positive/
    │   │   └── negative/
    │   └── env_1/
    │       ├── positive/
    │       └── negative/
    ├── labels/
    │   ├── env_0/
    │   │   ├── positive/
    │   │   └── negative/
    │   └── env_1/
    │       ├── positive/
    │       └── negative/
    ├── overlay/
    │   ├── env_0/
    │   └── env_1/
    └── annotations.xml
```

### Images

Contains the original RGB camera frames used for training.

### Labels

Contains YOLO .txt annotation files.

Positive files contain one target bounding box. Negative files are empty.

### Overlay

Contains validation images with the generated bounding box drawn over the target UAV.

Overlay images are intended only for annotation checking and should not be used for training.

### XML

Contains CVAT compatible XML annotations for dataset inspection or import into CVAT.





