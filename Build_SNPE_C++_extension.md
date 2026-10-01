## Build the SNPE C++ extension

Use the same Conda environment that you use to run the simulation, so the extension is built for that environment’s Python and PyTorch.

Replace the SDK and source-directory paths with the paths on your system:

```bash
conda activate isaaclab

export QAIRT_SDK_ROOT="/path/to/your/qairt/installation"
source "$QAIRT_SDK_ROOT/bin/envsetup.sh"
export LD_LIBRARY_PATH="$QAIRT_SDK_ROOT/lib/x86_64-linux-clang${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

cd "/path/to/directory/containing/the/cpp/source"
BUILD_DIR="$PWD"

CPP_FILE="$BUILD_DIR/uav_fv2_snpe_pipeline_int8.cpp"
test -f "$CPP_FILE" || { echo "Source file not found: $CPP_FILE"; exit 1; }

TORCH_INCLUDE="$(python -c 'import pathlib, torch; print(pathlib.Path(torch.__file__).parent / "include")')"
EXT_SUFFIX="$(python -c 'import sysconfig; print(sysconfig.get_config_var("EXT_SUFFIX"))')"

clang++ -O2 -std=c++17 -stdlib=libc++ -shared -fPIC \
  $(python -m pybind11 --includes) \
  -I"$TORCH_INCLUDE" \
  -I"$QAIRT_SDK_ROOT/include/SNPE" \
  "$CPP_FILE" \
  -L"$QAIRT_SDK_ROOT/lib/x86_64-linux-clang" \
  -Wl,-rpath,"$QAIRT_SDK_ROOT/lib/x86_64-linux-clang" \
  -lSNPE \
  -o "$BUILD_DIR/uav_fv2_snpe_pipeline${EXT_SUFFIX}"
```

Check that Python can load the compiled module:

```bash
python -c 'import torch; import uav_fv2_snpe_pipeline as m; print(m.__file__); print(m.YoloFV2SNPEDLPackRunner)'
```
