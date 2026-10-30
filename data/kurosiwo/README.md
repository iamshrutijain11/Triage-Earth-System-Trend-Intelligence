# data/kurosiwo — Kuro Siwo Training Subset

This directory holds the locally downloaded **Kuro Siwo** SAR flood dataset subset
used for U-Net training and unseen-scene evaluation.

> **Gitignored**: This directory is excluded from version control due to dataset size.

## Dataset Overview

| Property | Value |
|----------|-------|
| **Paper** | Bountos et al., NeurIPS 2024 |
| **Repository** | [Orion-AI-Lab/KuroSiwo](https://github.com/Orion-AI-Lab/KuroSiwo) |
| **HuggingFace** | [orion-ai-lab/Kuro-Siwo-Webdataset](https://huggingface.co/datasets/orion-ai-lab/Kuro-Siwo-Webdataset) |
| **Coverage** | 43 flood events, 6 continents, 2015–2022 |
| **Resolution** | 10m (Sentinel-1 IW GRD) |
| **Size** | ~338 billion m² mapped area |

## Directory Structure (after download)

```
data/kurosiwo/
├── grd/                    # Ground Range Detected products
│   ├── flood_event_*/      # Per-event directories
│   │   ├── post_vv.tif     # Post-event VV band
│   │   ├── post_vh.tif     # Post-event VH band
│   │   ├── pre_vv_*.tif    # Multiple pre-event VV captures
│   │   ├── pre_vh_*.tif    # Multiple pre-event VH captures
│   │   ├── dem.tif         # Digital Elevation Model
│   │   └── mask.tif        # Annotation (0=land, 1=water, 2=flood)
├── slc/                    # Single Look Complex (optional)
└── splits/
    ├── train.txt
    ├── val.txt
    └── test.txt
```

## Download Instructions

```bash
# Option 1: Official download script
git clone https://github.com/Orion-AI-Lab/KuroSiwo
cd KuroSiwo
chmod +x scripts/download_kuro_siwo.sh
./scripts/download_kuro_siwo.sh ../../data/kurosiwo/

# Option 2: HuggingFace Hub (Python)
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="orion-ai-lab/Kuro-Siwo-Webdataset",
    repo_type="dataset",
    local_dir="data/kurosiwo/"
)
```

## Label Schema

| Value | Class | Description |
|-------|-------|-------------|
| 0 | No water | Dry land / background |
| 1 | Permanent water | Rivers, lakes (pre-existing) |
| 2 | Flood | Inundated land (event-specific) |

## Citation

```bibtex
@inproceedings{bountos2024kurosiwo,
  title     = {Kuro Siwo: A multi-sensor, multi-modal SAR and Optical flood mapping benchmark dataset},
  author    = {Bountos, Nikolaos Ioannis and others},
  booktitle = {Advances in Neural Information Processing Systems (NeurIPS)},
  year      = {2024}
}
```
