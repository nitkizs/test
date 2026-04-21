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


# 4. Data Filtering

The dataset undergoes multiple filtering stages to improve quality and remove noise for model training. The filtering pipeline is divided into three stages: manual filtering, model-based filtering, and high-impact (uniqueness) filtering.

---

## 4.1 Positive–Negative Filtering

The initial filtering step is performed manually to separate the dataset into positive and negative samples.

* **Positive images** contain the target object (UAV)
* **Negative images** do not contain the target object

**Note:**
Images where the drone appears below the horizon (e.g., with background such as ground, trees, or mountains) are excluded from both positive and negative datasets and are not used for further processing.

---

## 4.2 Model-Based Filtering

Model-based filtering refines the dataset using a latest trained detection model. This process is applied separately to positive and negative datasets and consists of two stages: inferencing and filtering.

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
* `--viz` → Enable visualization output in video format
* `--conf` → Confidence threshold for detections
* `--iou` → IoU threshold
* `--exp` → Experiment name (output folder identifier)
* `--eval_json` → Optional evaluation JSON file

**Requirements:**

* Latest trained `.pth` model
* Compatible `.data` file
* `uav_sq.names` file (keep this file in the path defined in `.data`)

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

**It generates output in the `output` folder of the cloned repository, including images with bounding boxes and label files (.txt)**

---

### Stage 2: Filtering

The inference output (bounding box images and .txt label files) is further processed using a filtering script to categorize images based on detection results and confidence thresholds.
A threshold value (typically between 0.7 and 0.9 depending on requirements) is used to classify detections.
Use this script: [model_filtering.py](https://github.com/username/repo-name/blob/main/scripts/image_rename.py)

This script categorizes .txt outputs into four groups.

1. No detections (Images with no detected objects)
2. Low confidence (Images where detected object confidence is below the defined threshold)
3. High confidence (Images where detected object confidence exceeds the threshold)
4. Multiple detections (Images with multiple detected objects,often considered false positives)

---

### Dataset Selection for Further Processing

The filtered categories are used differently for positive and negative datasets.

**Positive Dataset (used for next-stage filtering):**

* No Detections
* Low Confidence
* Multiple Detections

**Negative Dataset:**

* Low Confidence
* High Confidence
* Multiple Detections


The `Model_filtering.py` script also generates **XML files** for each category. These XML files are used to group and manage images in subsequent filtering stages.

**Important:**
The images generated during model filtering should **not** be used for further processing, as they may be altered (e.g., resized or converted to grayscale). Always use the **original images** for the next stage.

---


## 4.3 High-Impact Filtering (Uniqueness Filtering)

This stage focuses on removing duplicate and near-duplicate images to improve dataset quality, reduce redundancy, and ensure diversity for model training. The process is applied separately to positive and negative datasets and uses **DINOv2** for feature-based similarity.

Key Benefits of Duplicate Filtering:
 * Avoid Overfitting: Reduces the risk of overfitting by eliminating redundant images.
 * Prevent Model Bias: Ensures the model is trained on a diverse set of images.
 * Improve Training Efficiency: Optimizes training time by reducing the number of images.


---

### Preparation

Before executing this stage:

* Download existing (previous) positive and negative datasets from the database
  *(use the provided download script)*
* Download the corresponding CVAT XML annotations for the existing datasets
* Organize datasets into:

  * Old Positive / Old Negative
  * New Positive / New Negative
* Generate CVAT XML files for the new datasets using `Generate_cvat_xml.py`

---

### Processing

* Combine datasets by class:

  * Old Positive + New Positive → single directory
  * Old Negative + New Negative → single directory

* Run the **near-duplicate filtering notebook (`near-duplicate-filter.ipynb`)**:

  * Update paths for:

    * Image directories (old + new)
    * XML annotation files
    * Output directories
  * Execute the notebook separately for:

    * Positive dataset
    * Negative dataset

The notebook uses feature embeddings to compare images and identify duplicates or highly similar samples.

---

- To perform this filtering step another jupyter notebook is created using the [fiftyone-library](https://docs.voxel51.com/).
- The notebook performs the following tasks:
  - Load the dataset to FiftyOne, which consists of an image directory and an XML file corresponding to these images.
  - Next, select an AI model to use. The selected AI model will be used to generate image embeddings for all the images in the dataset.
    - An image embedding is a numeric representation of an image that encodes the semantics of contents in the image. 
    - Embeddings are calculated by computer vision models which are usually trained with large datasets of pairs of text and image.
  - Once the images embeddings are created, you will compute the uniqueness of each image by choosing a threshold percentage. 
  - If the similarity between images falls below the threshold, they will be considered duplicates.
  - Finally, an XML file will be generated containing only the unique images.
  - Optionally, you can launch the FiftyOne app to visualize the duplicates and better understand the results.
    
* The same workflow must be executed independently for:

  * Positive images
  * Negative images

### **Additional requirements**

- Based on the requirement of the project, the data can be sampled using a constant sampling rate.
- This can be achieved using the script [create-cvat-xml-6-frame.py](create-cvat-xml-6-frame.py).
- The constant sampling rate needs to be calculated based on the project requirement.

---

### Notebook Outputs

For each dataset (positive and negative), the notebook generates:

* **Duplicate XML**
  Contains images identified as duplicates across both old and new datasets

* **Unique New XML**
  Contains only unique images from the incoming dataset after duplicate removal

* **Unique Old XML**
  Contains only unique images from the existing dataset after duplicate removal

These XML files are used to finalize dataset selection and retrieve the corresponding filtered images.









