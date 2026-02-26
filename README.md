# Nvidia Isaac Sim Workstation Installation
version: 5.1 Date:22.02.2026
The workstation installation is recommended if you want to run Isaac Sim as a GUI application on Linux with a GPU.
This guide is based on Nvidia Offical Isaac sim Documentation, purpose of this guide is for easy oinstallation Isaac Sim 5.1 on Ubundu.Ubundu 22.04.5 version is used in the process. It is stricly require to use ubundu 22.04.5. Isaac Sim 5.1 faced some trouble on Ubundu 24.04.4. that s y presffred ubundu 22.04.5. For detailed understanding and installation process plaese visit https://docs.isaacsim.omniverse.nvidia.com/5.1.0/index.html
### Isaac Sim Compatibility Checker
it is alyas bteter to start with check the requirements before proceding further To See Isaac Sim 5.1 [Requirements](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html#isaac-sim-requirements).
The Isaac Sim Compatibility Checker is a lightweight application that programmatically checks the above requirements and indicates which of them are valid, or not, for running NVIDIA Isaac Sim on the machine. it is better to check compatabilty system before proceeding installation of isaac sim

You can use pip install isaacsim[compatibility-check] to install a minimal setup for the Compatibility Checker app instead of installing the full version. Run the isaacsim isaacsim.exp.compatibility_check command.
#### Verifying Compatibility

The application highlights, in color, the following states:

- green excellent

- light-green good

- orange enough, more is recommended

- red not enough/unsupported

The application checks:

- NVIDIA GPU: Driver version, RTX-capable GPU, GPU VRAM

- CPU, RAM and Storage: CPU processor, Number of CPU cores, RAM, Available storage space

- Others: Operating system, Display
- <img width="1024" height="567" alt="isaac_sim_compatibility_checker" src="https://github.com/user-attachments/assets/3db6fef6-a0ee-412c-ade6-1bdce5ebc570" />
The Test Kit button, launches a minimal Kit application (in headless mode) and checks if its execution was successful or not, reporting the result on the panel next to it.
### Download Isaac Sim
for downloading isaac sim 5.1 [click](https://download.isaacsim.omniverse.nvidia.com/isaac-sim-standalone-5.1.0-linux-x86_64.zip). Facing any error in download or check aother version please visitt https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/download.html
### Isaac Sim Install and Launch
The first run of the Isaac Sim app takes some time to warm up the shader cache. Follow the steps for installation
1. create a folder named isaacsim
2. move the downloaded isaacsim zip file to the folder isaacsim
3. Unzip the package to that folder.
4. Navigate to that folder.
5. To create a symlink to the extension_examples for the tutorials, run the post_install script. The script can be run at this stage or after installation. run ./post_install.sh.
6. to run the Isaac Sim App Selector: run ./isaac-sim.selector.sh
<img width="502" height="461" alt="isim_4 5_base_ref_gui_ui_app_selector" src="https://github.com/user-attachments/assets/6d2c157b-e613-49bb-acf4-e7acb715c21e" />
<img width="503" height="497" alt="image" src="https://github.com/user-attachments/assets/f8374bac-ced7-4272-b1b2-3c53f9249462" />

7. In the popup window choose Isaac Sim Full.
8. Select the options like above images.
9. Click START to run the Isaac Sim main app.

The command window continues running scripts.
Then the Isaac Sim GUI window opens with nothing displayed in it. It can take 5-10 minutes to complete.
<img width="1850" height="1036" alt="Screenshot from 2026-02-24 06-36-35" src="https://github.com/user-attachments/assets/535c5b20-7ea4-4734-88eb-5f63303b48ea" />
#### For easy command line Installation
```bash
mkdir ~/isaacsim
cd ~/Downloads
unzip "isaac-sim-standalone-5.1.0-linux-x86_64.zip" -d ~/isaacsim
cd ~/isaacsim
./post_install.sh
./isaac-sim.selector.sh
```

## Python Environment Installation
Isaac Sim 5.1 requires Python 3.11. for installing all dependency and python packages required for working of isaac sim can use venv module or conda, here in the whole guide uses conda
#### Create and activate the virtual environment
```bash
conda create -n isaacsim python=3.11
conda activate isaacsim
```
#### Update Pip
```bash
pip install --upgrade pip
```
#### Install Isaac Sim - Python packages: 
```bash
pip install isaacsim[all,extscache]==5.1.0 --extra-index-url https://pypi.nvidia.com
```


---

#### Launching Isaac Sim from Terminal

When Isaac Sim is installed using the pip package method, a global command called `isaacsim` is automatically registered.

This allows launching Isaac Sim directly from any directory without navigating to the installation folder.

Instead of:

```bash
cd /path/to/isaac-sim
./isaac-sim.sh
```

You can simply run:

```bash
isaacsim
```

You can also launch a specific experience (.kit) file if required:

```bash
isaacsim path/to/experience_file.kit
```

This method simplifies execution and is recommended for scripted or automated workflows.

---

