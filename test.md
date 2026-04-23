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

Before starting the filtering process, refer to the provided guideline (link) to understand edge cases for both positive and negative samples. Mistakes made at this stage will propagate through subsequent stages, so careful inspection is essential.

**Note:** Images in which the drone appears below the horizon, for example with backgrounds such as ground, trees, or mountains, are treated as negative samples and are used as part of the negative dataset in subsequent stages.

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
* `uav_sq.names` file (Ensure that this file contains the correct class name corresponding to the actual target, "Mavic". The file must be placed in the path specified in the `.data` configuration file.)

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

The script groups outputs into the following categories:

* **No detections** – images with no detected objects
* **Low confidence** – detections below the defined threshold
* **High confidence** – detections above the defined threshold
* **Multiple detections (mixed confidence)** – at least one detection below the threshold
* **Multiple detections (high confidence)** – all detections above the threshold

**Important:**
For the positive dataset, images with multiple detections require manual verification. These cases may include all correct detections, a mix of correct and false detections, or entirely false detections. Carefully review these images using the verification script (link), which can also be used to inspect results and generate XML files if required.

Repeat this process for both positive and negative filtered images and save the outputs separately for further filtering stages.

---

### Dataset Selection for Further Processing

The filtered categories are used differently for positive and negative datasets for high impact filtering.

impact filtering stage.

**For the positive dataset, the following categories are used:**

* **No detections**
* **Low confidence**
* **Multiple detections (mixed confidence)**

In addition, images from **Multiple detections (high confidence)** may also be included **only if they are manually verified as false positives**. All other correctly detected images from this category are excluded from further processing.



**For the Negative Dataset, the following categories are used:**

* **Low confidence**
* **High confidence**
* **Multiple detections (mixed confidence)**
* **Multiple detections (high confidence)**

**Note:**
If detections are present, images may be optionally reviewed to verify whether the detections correspond to actual targets; however, this step is not strictly required.


The `Model_filtering.py` script also generates **XML files** for each category. These XML files are used to group and manage images in subsequent filtering stages.

**Important:**
The images generated during model filtering should **not** be used for further processing, as they may be altered (e.g., resized or converted to grayscale). Always use the **original images** for the next stage.

---


## 4.3 High-Impact Filtering (Uniqueness Filtering)

The new incoming data can be similar to the existing dataset, so it is important not to blindly add this to the training set..This stage focuses on removing duplicate and near-duplicate images to improve dataset quality, reduce redundancy, and ensure diversity for model training.

Unlike previous filtering stages, the new dataset is not processed independently. Instead, it is combined with the previously used training dataset to identify and remove redundant samples across both datasets.

The process is applied separately to the positive and negative datasets and uses DINOv2 for feature-based similarity comparison.

Key Benefits of Duplicate Filtering:
 * Avoid Overfitting: Reduces the risk of overfitting by eliminating redundant images.
 * Prevent Model Bias: Ensures the model is trained on a diverse set of images.
 * Improve Training Efficiency: Optimizes training time by reducing the number of images.


---

### Preparation

Before executing this stage:

* Generate **CVAT XML files** for the new datasets (both positive and negative) using `Generate_cvat_xml.py`

* Download the **current positive and negative datasets** from the database via LakeFS
  *(refer to guide: link)*

* Download the corresponding **CVAT XML annotations** for both datasets directly from the LakeFS UI
  ([http://ai-lakefs.int.draive.com:8000/repositories](http://ai-lakefs.int.draive.com:8000/repositories) — access required)

* Combine datasets:

  * Old Positive images + New Positive images → single directory
  * Old Negative images  + New Negative images → single directory




---

### Processing

* This filtering step is performed using a Jupyter Notebook built with the [fiftyone-library](https://docs.voxel51.com/).

* Run the **near-duplicate filtering notebook (`near-duplicate-filter.ipynb`)**:

  * Update the following parameters:

    * Image directory (combined old + new datasets)
    * XML annotation files
    * Output directory
    * Threshold value *(adjust based on similarity requirements to achieve the desired dataset balance, e.g., ~10–12% negatives relative to positives)*

  * Execute the notebook separately for:

    * **Positive dataset**
    * **Negative dataset**

- The notebook performs the following tasks:
  - Load the dataset to FiftyOne, which consists of an image directory and an XML file corresponding to these images.
  - Next, select an AI model(DINOv2) to use. The selected AI model will be used to generate image embeddings for all the images in the dataset.
    - An image embedding is a numeric representation of an image that encodes the semantics of contents in the image. 
    - Embeddings are calculated by computer vision models which are usually trained with large datasets of pairs of text and image.
  - Once the images embeddings are created, you will compute the uniqueness of each image by choosing a threshold percentage. 
  - If the similarity between images falls below the threshold, they will be considered duplicates.
  - Finally, an XML file will be generated containing only the unique images.
  - Optionally, you can launch the FiftyOne app to visualize the duplicates and better understand the results.
 
    
### Notebook Outputs

For each dataset (**positive** and **negative**), the notebook generates:

* **Duplicate XML**
  Contains images identified as duplicates across both old and new datasets

* **Unique New XML**
  Contains only unique images from the incoming dataset after duplicate removal

* **Unique Old XML**
  Contains only unique images from the existing dataset after duplicate removal

* **Combined Unique XML**
  Contains merged unique images from both new and old datasets

These XML files are used to finalize dataset selection and retrieve the corresponding filtered images.

If the new incoming dataset contains unique samples, these will be exported as a CVAT XML file for labeling.

If the new incoming dataset contains only similar samples, a unique (controllable) subset of the new data can be exported for labeling, and the similar samples from the existing training dataset will be deleted. The updated training dataset will also be exported as a CVAT XML file.


### **Additional requirements**

- Based on the requirement of the project, the data can be sampled using a constant sampling rate.
- This can be achieved using the script [create-cvat-xml-6-frame.py](create-cvat-xml-6-frame.py).
- The constant sampling rate needs to be calculated based on the project requirement.

  
## 5. Data Labelling

After the data has been extracted, preprocessed, sorted, and filtered, the next step is labeling.

For labeling, the CVAT tool is used. Follow the official quick installation guide for both Windows and Linux:
[https://docs.cvat.ai/docs/administration/community/basics/installation/](https://docs.cvat.ai/docs/administration/community/basics/installation/)

It is also recommended to familiarize yourself with the basic functions and tools of CVAT before starting:
[https://docs.cvat.ai/docs/workspace/](https://docs.cvat.ai/docs/workspace/)

### Labelling Workflow

After installation, follow these steps:

* Open a browser and navigate to: [http://localhost:8080/](http://localhost:8080/)
* Create a new project *(see GIF)*
* Zip the image folder before uploading
* Create a new task *(see GIF)*
* Start labeling *(see GIF)*
* Export the dataset *(see GIF)*

Before starting labeling, refer to the labeling guidelines.









