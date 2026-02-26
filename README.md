# NVIDIA Isaac Sim 5.1 Workstation Installation Guide

**Version:** 5.1
**Date:** 22.02.2026
**Platform:** Ubuntu 22.04.5 LTS

---

## 1. Overview

This guide describes the complete installation procedure for **NVIDIA Isaac Sim 5.1 (Workstation version)** on Ubuntu Linux with a dedicated NVIDIA GPU.

The workstation installation method is recommended when running Isaac Sim as a **GUI-based desktop application**.

This guide is based on the official NVIDIA documentation:
[https://docs.isaacsim.omniverse.nvidia.com/5.1.0/index.html](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/index.html)

---

## 2. Operating System Requirement

**Ubuntu 22.04.5 LTS is strongly recommended.**

Isaac Sim 5.1 has shown compatibility and stability issues on Ubuntu 24.04 in certain configurations. For this reason, Ubuntu 22.04.5 LTS is used and recommended for this installation.

---

## 3. Isaac Sim Compatibility Check (Recommended Before Installation)

Before downloading Isaac Sim, verify that your system meets the minimum hardware and software requirements.

Official Requirements:
[https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html)

### 3.1 Install Compatibility Checker (Minimal Install)

```bash
pip install isaacsim[compatibility-check] --extra-index-url https://pypi.nvidia.com
```

Run the checker:

```bash
isaacsim isaacsim.exp.compatibility_check
```

### 3.2 Result Indicators

The Compatibility Checker displays system status using color indicators:

* 🟢 Green – Excellent
* 🟢 Light Green – Good
* 🟠 Orange – Sufficient (Higher recommended)
* 🔴 Red – Unsupported / Not sufficient

<img width="1024" height="567" alt="isaac_sim_compatibility_checker" src="https://github.com/user-attachments/assets/168eb332-7f51-4dd3-98e1-b6fa6000ae36" />


The tool validates:

* NVIDIA GPU (RTX support, driver version, VRAM)
* CPU (model and core count)
* RAM
* Storage availability
* Operating system
* Display configuration

The **Test Kit** button launches a minimal headless Kit application to confirm execution capability.

It is strongly recommended to pass this check before proceeding with installation.

---

## 4. Download Isaac Sim 5.1 (Workstation Version)

Download link:

[https://download.isaacsim.omniverse.nvidia.com/isaac-sim-standalone-5.1.0-linux-x86_64.zip](https://download.isaacsim.omniverse.nvidia.com/isaac-sim-standalone-5.1.0-linux-x86_64.zip)

For alternative versions or troubleshooting:

[https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/download.html](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/download.html)

---

## 5. Workstation Installation Procedure

### Step 1 – Create Installation Directory

```bash
mkdir ~/isaacsim
```

### Step 2 – Move Downloaded File

Move the downloaded ZIP file into the `isaacsim` directory.

### Step 3 – Extract Package

```bash
cd ~/Downloads
unzip isaac-sim-standalone-5.1.0-linux-x86_64.zip -d ~/isaacsim
```

### Step 4 – Navigate to Installation Folder

```bash
cd ~/isaacsim
```

### Step 5 – Run Post Install Script

```bash
./post_install.sh
```

This creates symbolic links and prepares example extensions.

### Step 6 – Launch App Selector

```bash
./isaac-sim.selector.sh
```
<img width="502" height="461" alt="isim_4 5_base_ref_gui_ui_app_selector" src="https://github.com/user-attachments/assets/7b0c395c-fccd-4432-9ed9-220cd65fe2f0" />
<img width="503" height="497" alt="Screenshot from 2026-02-26 11-27-10" src="https://github.com/user-attachments/assets/ba22d7a5-5b89-4dad-a5bb-83d95549c1ea" />


In the popup window:

* Select **Isaac Sim Full**
* Keep the configuration as shown in the second image.
* Click **START**
<img width="1850" height="1036" alt="Screenshot from 2026-02-24 05-21-08" src="https://github.com/user-attachments/assets/6d938959-4d69-42d3-ac30-5539df6cdc8e" />

> Note: First launch may take 5–10 minutes due to shader cache generation.

---

# 6. Python Environment Setup (For Pip-Based Installation)

### Important Clarification

For the **standalone workstation (ZIP) installation**, a built-in Python runtime is already included. Therefore, creating a separate Conda environment is **not mandatory**.

However, creating a dedicated Conda environment is recommended if you:

* Plan to develop custom Python scripts
* Intend to integrate Isaac Sim with external libraries
* Require an isolated and reproducible development environment
* Plan to integrate with Isaac Lab

Using a separate environment improves dependency management and helps prevent conflicts with system-level Python packages.

---

## 6.1 Create Conda Environment

Isaac Sim 5.1 requires Python 3.11.

```bash
conda create -n isaacsim python=3.11
conda activate isaacsim
```

Upgrade pip:

```bash
pip install --upgrade pip
```

---

## 6.2 Install Isaac Sim Python Package

```bash
pip install isaacsim[all,extscache]==5.1.0 --extra-index-url https://pypi.nvidia.com
```

This installs:

* Core simulation components
* Extensions
* Cached dependencies
* Python APIs

---

# 7. Launching Isaac Sim from Terminal

When installed via pip, a global command called `isaacsim` is registered.

Instead of navigating to a folder and running:

```bash
./isaac-sim.sh
```

You can launch from any directory:

```bash
isaacsim
```

---

