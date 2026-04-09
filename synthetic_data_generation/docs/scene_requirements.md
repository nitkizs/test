# Scene Requirements

## Overview

This pipeline assumes a specific USD scene structure.  
The required objects, semantic labels and prim paths must be present for the script to function correctly.

---

## Required Objects

### 1. Target Drone

- Must exist in the scene
- Expected prim path:
```

DJI_Mavic_04

```

---

### 2. Observer Drone and Camera

- Camera must exist at:
```

DJI_Mavic_3/Camera

```

- The camera should:
- be correctly oriented toward the target drone

---

## Semantic Label Requirement

The target drone must be labeled using the Replicator Schema Editor:

```

target_drone

```

This label is used to:
- identify target pixels in segmentation
- generate bounding boxes
- produce YOLO annotations

---

