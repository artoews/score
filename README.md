# SCORE: Shear-based Correction of Off-Resonance 

## Overview

This code base serves to reproduce the basic results from [this MRM article](). If you use any materials from this repository please acknowledge our work with the following citation.

> Toews AR, Hargreaves BA. Retrospective shear-based correction of in-plane distortion from off-resonance in 3D imaging. Magn Reson Med. 202X;XX-XX. doi: XX.XXXX/mrm.XXXXX

## Getting Started

### Requirements

The code was tested on an Ubuntu workstation with 8 CPU cores, 48GB RAM, and 12GB VRAM (NVIDIA TITAN Xp). All timing estimates are based on this environment.

It is recommended to have at least 100GB storage available for saving intermediate reconstruction outputs. With less available storage it will be necessary to remove intermediate outputs after each reconstruction (each call to main_recon.sh). At a minimum, 30GB is needed to store the final reconstruction outputs used for plotting (main_plotting.sh).

A GPU is required to run the image reconstruction code.

### Setup

1. Download the data

The supporting dataset is pending upload to Zenodo at [10.5281/zenodo.22942186](10.5281/zenodo.22942186), but Zenodo is currently experiencing technical issues.
In the meantime the dataset is readily available [here](https://drive.google.com/file/d/1jwp15IqCrSBy-v_DDs32Dt0-KdS32BUL/view?usp=sharing) on Google Drive.

The dataset includes photographs, coil-compressed k-space data, and sequence metadata necessary to reproduce the phantom results presented in the article.

2. Install BART toolbox

Installation page is [here](https://mrirecon.codeberg.page/installation.html). The code was tested using BART 1.0.00. Other versions of BART may also work.

Make sure the BART toolbox's python/ directory is on your Python path.

```
export PYTHONPATH=$TOOLBOX_PATH/python:$PYTHONPATH
```

3. Create conda environment

```
cd path/to/score
conda env create -f environment.yml
conda activate score
```

## Basic Usage

1. Reconstruct images from raw k-space data

```
conda activate score
cd path/to/score
bash main_recon.sh path/to/scan_dir
```

Repeat the last command for each of the three phantom scan subdirectories (gz-off, gz-on, and gz-on-plastic-replica). Expected run time is about 1 hour per scan directory.

Note that gradient non-linearity correction is disabled by default because it relies on proprietary software (GERecon module) from GE Healthcare.

Optional: after each call to main_recon.sh, you may delete all files in scan_dir except the final reconstruction outputs (im_post.{cfl.hdr}) to free up storage.

```
find path/to/scan_dir -type f ! -name 'im_post.*' -print   # dry run (always a good idea!)
find path/to/scan_dir -type f ! -name 'im_post.*' -delete
```

2. Plot figures from paper

After running the above reconstruction, you may reproduce figures 1-5 and A1 with the following commands. Expected run time is 1 minute.

```
conda activate score
cd path/to/score
bash main_plotting.sh path/to/data_dir path/to/save_dir
```

Reference outputs for figures 1-5 and A1 are provided [here](figures-mrm).

## Acknowledgements

The authors thank the ISMRM Reproducible Research Study Group for conducting a code review of this work. The scope of the code review covered only the code’s ease of download, quality of documentation, and ability to run, but did not consider scientific accuracy or code efficiency.

## Correspondence

Please direct any questions to the paper's corresponding author, Alex Toews (artoews@stanford.edu).

## Disclaimer

The code is intended for research use only and NOT FOR DIAGNOSTIC USE. It comes without any warranty.