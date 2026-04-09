````md
# Commands

## 1. Activate Isaac Lab environment

```bash
conda activate isaaclab
````

---

## 2. Navigate to Isaac Lab root directory

```bash
cd IsaacLab
```

---

## 3. Run the script in headless mode

```bash
./isaaclab.sh -p synthetic_data_generation/multi_env_drone_dataset_generator.py --headless --enable_cameras
```

---

## 4. Run the script with GUI

```bash
./isaaclab.sh -p synthetic_data_generation/multi_env_drone_dataset_generator.py --enable_cameras
```

---

## 5. Output location

The output directory is defined inside the script:

```python
OUTPUT_DIR = "synthetic_data_generation/output"
```

Generated outputs will be available under:

```text
synthetic_data_generation/output/
├── replicator/
├── labels/
└── overlay/
```

```
```
