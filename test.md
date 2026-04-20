# Data Engineering

The Data Engineering stage of the AI-Workflow-Toolkit focuses on preparing raw data for downstream tasks. It includes data collection, extraction, and preprocessing, ensuring that the dataset is structured, consistent, and ready for further use.

---

## 1. Data Collection

Data collection is the initial step where raw data is acquired from different sources.

Data may be collected using:

* External recording devices
* Cloud storage platforms (e.g., OneDrive)
* Remote transfer tools such as croc

Ensure that the required access permissions and credentials are available before retrieving the data. All files should be verified for completeness after transfer.

---

## 2. Data Extraction

The collected data is provided in compressed `.zip` format.

The extraction process includes:

* Obtaining necessary credentials to access the data
* Extracting the `.zip` file
* Ensuring all subfolders are properly unpacked
* Preserving the original folder structure

Maintaining the folder structure is important, as it is used in later stages of the pipeline.

---

## 3. Data Preprocessing

The preprocessing stage prepares the dataset by validating and standardizing the image files.

---

### 3.1 Image Integrity Check

Verifies the integrity of the images to ensure no corrupted files are present.

---

### 3.2 Image Renaming

All images are renamed to follow a consistent naming convention. The renaming is performed using the provided scripts and applied across all subfolders.
Use this script: [image_rename.py](https://github.com/username/repo-name/blob/main/scripts/image_rename.py)

**Naming format:**

```text
{PREFIX}_{folder_name}_{DATE}_{time_str}_{seq}{ext}
```

**Components:**

* `PREFIX` → Dataset identifier (e.g., `dd15`, `dd16`)
* `folder_name` → Name of the subfolder (e.g., `flug-01`, `flug-02`)
* `DATE` → Derived from parent folder, formatted as `DD-MM-YYYY`
* `time_str` → Time of the first image in the subfolder, reused for all images
* `seq` → Sequence number to ensure uniqueness
* `ext` → File extension (e.g., `.png`)

**Example:**

Input:

```text
orig_00000.png
```

Output:

```text
dd15_flug-01_09-04-2026_12-32-03_000000.png
```

## 4. Data Filtering

The dataset undergoes multiple filtering stages to improve quality and relevance.

---

### 4.1 Positive-Negative Filtering (Manual)

* Manually separate:

  * **Positive images** (contain target objects)
  * **Negative images** (do not contain target objects)

---

### 4.2 Model-Based Filtering

Filtering is applied separately to positive and negative datasets using a detection model.

#### For Positive Images:

Images are retained (**Pos-filtered**) under the following conditions:

* Model detects object correctly
* No detections
* Low-confidence detections
* Multiple detections

#### For Negative Images:

Images are retained (**Negs-filtered**) if:

* Any object is detected (to identify challenging negatives)

---

### 4.3 HI-Filtering (High-Information Filtering)

This stage removes duplicate or redundant images using feature-based similarity.

#### Process:

* Combine datasets:

  * **UAV Positive Dataset + Pos-filtered**
  * **UAV Negative Dataset + Negs-filtered**

* Apply:

  * **DINOv2** (feature extraction model)

#### Output:

* **Unique Positive Images**
* **Unique Negative Images**

---

## 5. Final Output

After all filtering stages:

* Cleaned and structured dataset
* High-quality, non-redundant images
* Ready for training or further analysis



# 4. Data Filtering

The dataset undergoes multiple filtering stages to improve quality, remove noise, and ensure relevance for model training. The filtering pipeline is divided into three stages: manual filtering, model-based filtering, and high-impact (uniqueness) filtering.

---

## 4.1 Positive–Negative Filtering

The initial filtering step is performed manually to separate the dataset into positive and negative samples.

* **Positive images** contain the target object (e.g., UAV)
* **Negative images** do not contain the target object

**Note:**
Images where the drone appears below the horizon (e.g., with background such as ground, trees, or mountains) are excluded from both positive and negative datasets and are not used for further processing.

---

## 4.2 Model-Based Filtering

Model-based filtering refines the dataset using a detection model. This process is applied separately to positive and negative datasets and consists of two stages: inferencing and filtering.

---

### Stage 1: Inferencing

A trained model is used to generate predictions on the dataset.

**Setup:**

* Clone the repository:
  `https://github.com/DEFAINE-GmbH/Yolo-FV2` *(access required)*
* Create an environment using the `requirements.txt` file
* Use the `test_images.py` script for inference

**Script arguments:**

* `--data` → Path to the `.data` configuration file
* `--weights` → Path to the trained model (`.pth`)
* `--img` → Directory containing input images
* `--channels` → Number of input channels (default: 3)
* `--viz` → Enable visualization output (bounding boxes)
* `--conf` → Confidence threshold for detections
* `--iou` → IoU threshold
* `--exp` → Experiment name (output folder identifier)
* `--eval_json` → Optional evaluation JSON file

**Requirements:**

* Latest trained `.pth` model
* Compatible `.data` file
* `uav_sq.names` file (must match the path defined in `.data`)

**Execution example:**

```bash
activate <env>
cd <repo_directory>
python test_images.py \
  --data uav_sq-6px_muv4-7.data \
  --channels 1 \
  --exp exp_2026-04-09-flug-07_uav-mu-v4-7 \
  --viz 1 \
  --weights weights/uav-mu-fv2-yolo-v4-7-best.pth \
  --img "/home/dataset/260409/flug-07/Positive/"
```

---

### Stage 2: Filtering

The inference step generates:

* Images with bounding boxes
* Label files (`.txt`) for each image

These outputs are processed using a filtering script to categorize images based on detection results and confidence thresholds (typically between **0.7–0.9**, depending on requirements).

**Filtering categories:**

1. No detections
2. Low confidence (below threshold)
3. High confidence (above threshold)
4. Multiple detections (potential false positives)

---

### Dataset-Specific Selection

**For Positive Dataset (used for next stage):**

* No detections
* Low confidence
* Multiple detections

**For Negative Dataset:**

* Low confidence
* High confidence
* Multiple detections

The filtering script also generates **XML files** for each category, which are used in subsequent processing steps.

**Important:**
Do not use the model-filtered output images for further filtering stages, as they may be modified (e.g., resized, grayscale). Always use the original images.

---

## 4.3 High-Impact Filtering (Uniqueness Filtering)

This stage removes duplicate and redundant images using feature-based similarity.

The process is applied separately to positive and negative datasets and uses **DINOv2** for feature extraction.

---

### Preparation

* Download existing (previous) positive and negative datasets from the database

* Download corresponding CVAT XML annotations

* Organize datasets into:

  * Old Positive / Old Negative
  * New Positive / New Negative

* Generate CVAT XML files for the new datasets using the provided script (`Generate_cvat_xml.py`)

---

### Processing

* Combine datasets:

  * Old Positive + New Positive
  * Old Negative + New Negative

* Run the high-impact filtering Jupyter Notebook:

  * Update paths for images, XML files, and output directories
  * Execute the notebook to perform similarity-based filtering

---

### Output

* Unique Positive Images
* Unique Negative Images

This step ensures removal of redundant samples and improves dataset diversity for training.






