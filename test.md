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

---




