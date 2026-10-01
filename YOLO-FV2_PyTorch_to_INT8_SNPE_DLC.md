# YOLO-FV2 PyTorch to INT8 SNPE DLC

This guide covers converting the trained YOLO-FV2 checkpoint into an INT8 SNPE DLC and checking that the converted model runs.

```text
.pth checkpoint → ONNX → FP32 DLC → INT8 DLC
```

## Step 1 — Clone the YOLO-FV2 repository

```bash
git clone https://github.com/DEFAINE-GmbH/Yolo-FV2.git
cd Yolo-FV2
```

## Step 2 — Prepare the Python environment

Use Python 3.10.19 with these package versions:

```text
PyTorch        2.7.0+cu128
torchvision    0.22.0+cu128
NumPy          2.2.6
OpenCV         4.11.0
ONNX           1.23.0
torchsummary   1.5.1
pycocotools    2.0
```

## Step 3 — Verify the checkpoint

Check that the checkpoint contains the expected model layers and input channel:

```bash
python - <<'PY'
import torch
from pathlib import Path

checkpoint_path = Path("path/to/uav-mu-yolo-fv2-v4-8-1-test-best.pth")
checkpoint = torch.load(checkpoint_path, map_location="cpu")
state = checkpoint["model"] if "model" in checkpoint else checkpoint

for key in (
    "backbone.first_conv.0.weight",
    "output_reg_layers.weight",
    "output_obj_layers.weight",
    "output_cls_layers.weight",
):
    print(key, tuple(state[key].shape))
PY
```

For this checkpoint, the output was:

```text
backbone.first_conv.0.weight (24, 1, 3, 3)
output_reg_layers.weight (12, 72, 1, 1)
output_obj_layers.weight (3, 72, 1, 1)
output_cls_layers.weight (1, 72, 1, 1)
```

This confirms a one channel input, three anchor slots and one class in the detection head.

## Step 4 — Record the model settings

Read the `.data` configuration associated with the checkpoint. Record the input dimensions, class count, anchor count and anchor values:

```text
classes=1
width=1024
height=768
anchor_num=3

anchors:
  output_770:
    [34.96, 29.33]
    [53.36, 53.99]
    [87.13, 33.07]

  output_772:
    [95.90, 83.81]
    [147.15, 176.52]
    [311.41, 262.31]
```
## Step 5 — Export the `.pth` checkpoint to ONNX

```bash
cd ~/path/to/Yolo-FV2

OUTPUT_DIR="/path/to/uav_fv2_v4_8_1_artifacts/onnx"
mkdir -p "$OUTPUT_DIR"

python pytorch2onnx.py \
  --weights path/to/uav-mu-yolo-fv2-v4-8-1-test-best.pth \
  --output "$OUTPUT_DIR/uav-mu-yolo-fv2-v4-8-1-test-best.onnx" \
  --h_w 768 1024 \
  --classes 1 \
  --anchor_num 3 \
  --channels 1
```
## Step 6 — Validate the ONNX file. 
Before converting ONNX to an FP32 DLC, check that the ONNX file is valid and record its actual input and output names and shapes:

```bash
unset LD_LIBRARY_PATH

python - <<'PY'
from pathlib import Path
import onnx

path = Path("/path/to/uav_fv2_v4_8_1_artifacts/onnx/uav-mu-yolo-fv2-v4-8-1-test-best.onnx")

model = onnx.load(str(path))
onnx.checker.check_model(model)
print("ONNX validation passed.")

def print_tensors(label, tensors):
    for tensor in tensors:
        shape = [
            dim.dim_value if dim.dim_value else (dim.dim_param or "?")
            for dim in tensor.type.tensor_type.shape.dim
        ]
        print(f"{label}: {tensor.name}, shape={shape}")

print_tensors("Input", model.graph.input)
print_tensors("Output", model.graph.output)
PY
```

Record the names and shapes it prints. The checker confirms the ONNX graph is structurally valid.
## Step 7 — Install and initialize the QAIRT/SNPE SDK

Install the Qualcomm QAIRT SDK for Linux x86_64. This conversion used QAIRT version `2.50.40.260831`, installed at:

```text
/opt/qcom/aistack/qairt/2.50.40.260831
```

Set up the SDK environment and check that the ONNX converter is present:

```bash
export QAIRT_SDK_ROOT=/opt/qcom/aistack/qairt/2.50.40.260831
source "$QAIRT_SDK_ROOT/bin/envsetup.sh"

test -x "$QAIRT_SDK_ROOT/bin/x86_64-linux-clang/snpe-onnx-to-dlc" \
  && echo "SNPE ONNX converter found"
```

The SDK setup also provides `SNPE_ROOT` for compatibility with SNPE tools.

## Step 8 — Convert ONNX to an FP32 DLC

```bash
mkdir -p /path/to/uav_fv2_v4_8_1_artifacts/dlc
mkdir -p /tmp/qairt_onnx_compat
printf 'import onnx.version\n' > /tmp/qairt_onnx_compat/sitecustomize.py

export PYTHONPATH="/tmp/qairt_onnx_compat:$SNPE_ROOT/lib/python${PYTHONPATH:+:$PYTHONPATH}"

"$SNPE_ROOT/bin/x86_64-linux-clang/snpe-onnx-to-dlc" \
  --input_network /path/to/onnx/uav-mu-yolo-fv2-v4-8-1-test-best.onnx \
  -d "input.1" 1,1,768,1024 \
  -o /path/to/uav_fv2_v4_8_1_artifacts/dlc/uav-mu-yolo-fv2-v4-8-1-test-best.dlc
```
## Step 9 — Check the FP32 DLC interface

Inspect the converted DLC to confirm that its input and output names and shapes match the ONNX model:

```bash
export PYTHONPATH="$SNPE_ROOT/lib/python${PYTHONPATH:+:$PYTHONPATH}"

FP32_DLC="/path/to/uav_fv2_v4_8_1_artifacts/dlc/uav-mu-yolo-fv2-v4-8-1-test-best.dlc"

"$SNPE_ROOT/bin/x86_64-linux-clang/snpe-dlc-info" -i "$FP32_DLC"
```


For this model, check for input `input.1` with shape `(1, 768, 1024, 1)` and output heads `770` `(1, 48, 64, 16)` and `772` `(1, 24, 32, 16)`.

## Step 10 — Prepare INT8 calibration inputs

The quantizer needs representative images to estimate activation ranges. This step preprocesses 100 training images using the model’s input preprocessing and saves them as float32 NHWC raw files, matching the DLC input shape.


```bash
unset LD_LIBRARY_PATH

python - <<'PY'
from pathlib import Path
import random
import sys

import numpy as np
import torch

source_dir = Path("/path/to/Yolo_FV2")
train_dir = Path("/path/to/data/train/images")
calib_dir = Path("/tmp/uav_fv2_int8_calibration")
calib_dir.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(source_dir))
from test_images import preprocess_image

images = sorted(
    p for p in train_dir.iterdir()
    if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg"}
)
if len(images) < 100:
    raise RuntimeError(f"Need at least 100 images; found {len(images)}")

selected = sorted(random.Random(42).sample(images, 100))
input_list = calib_dir / "input_list.txt"
raw_paths = []
cfg = {"height": 768, "width": 1024}

for index, image_path in enumerate(selected):
    _, image_tensor = preprocess_image(
        str(image_path), cfg, torch.device("cpu"), in_channels=1
    )
    raw = image_tensor.unsqueeze(0).permute(0, 2, 3, 1).contiguous().numpy()

    assert raw.shape == (1, 768, 1024, 1), raw.shape
    assert raw.dtype == np.float32, raw.dtype

    raw_path = calib_dir / f"calib_{index:03d}.raw"
    raw.tofile(raw_path)
    raw_paths.append(str(raw_path.resolve()))

input_list.write_text("\n".join(raw_paths) + "\n")
print(f"Created {len(raw_paths)} calibration files")
print(f"Input list: {input_list}")
PY
```

This creates 100 `.raw` files and an `input_list.txt` for the INT8 quantization step.

## Step 11 — Quantize the FP32 DLC

```bash
export SNPE_ROOT=/opt/qcom/aistack/qairt/2.50.40.260831
export PATH="$SNPE_ROOT/bin/x86_64-linux-clang:$PATH"
export LD_LIBRARY_PATH="$SNPE_ROOT/lib/x86_64-linux-clang${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PYTHONPATH="$SNPE_ROOT/lib/python${PYTHONPATH:+:$PYTHONPATH}"

FP32_DLC="/path/to/uav_fv2_v4_8_1_artifacts/dlc/uav-mu-yolo-fv2-v4-8-1-test-best.dlc"
INT8_DLC="/path/to/uav_fv2_v4_8_1_artifacts/dlc/uav-mu-yolo-fv2-v4-8-1-test-best-int8.dlc"
INPUT_LIST="/tmp/uav_fv2_int8_calibration/input_list.txt"

"$SNPE_ROOT/bin/x86_64-linux-clang/qairt-quantizer" \
  --input_dlc "$FP32_DLC" \
  --input_list "$INPUT_LIST" \
  --output_dlc "$INT8_DLC" \
  --act_bitwidth 8 \
  --weights_bitwidth 8
```

This requests 8-bit activation and weight quantization. 

## Step 12 — Inspect the INT8 DLC

Run `snpe-dlc-info` on the quantized model:

```bash
export SNPE_ROOT=/opt/qcom/aistack/qairt/2.50.40.260831
export PYTHONPATH="$SNPE_ROOT/lib/python${PYTHONPATH:+:$PYTHONPATH}"
export LD_LIBRARY_PATH="$SNPE_ROOT/lib/x86_64-linux-clang${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

INT8_DLC="/path/to/uav_fv2_v4_8_1_artifacts/dlc/uav-mu-yolo-fv2-v4-8-1-test-best-int8.dlc"

ls -lh "$INT8_DLC"
"$SNPE_ROOT/bin/x86_64-linux-clang/snpe-dlc-info" -i "$INT8_DLC"
```

Confirm that the input is `input.1` with dimensions `1,768,1024,1`, and that outputs `770` and `772` have dimensions `1,48,64,16` and `1,24,32,16`. 
