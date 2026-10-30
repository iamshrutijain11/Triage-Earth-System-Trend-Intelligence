# p2_ai/ — AI Flood Detection Module

Multi-sensor deep learning flood detection using the **Kuro Siwo** benchmark dataset.

---

## Module Overview

| Submodule | File | Description |
|-----------|------|-------------|
| `detect/sar_change.py` | SAR Change | Backscatter ratio change detection (dB thresholding) |
| `detect/coherence.py` | InSAR Coherence | Temporal coherence loss detection (fallback) |
| `detect/unet.py` | U-Net | 5-channel encoder-decoder deep learning model |
| `detect/fuse.py` | Fusion | 4-way sensor fusion (U-Net + SAR + Coherence + NDWI) |
| `notebooks/01_unet_training.ipynb` | Training | Kuro Siwo training pipeline |
| `notebooks/02_unseen_eval.ipynb` | Evaluation | Unseen Himalayan scene evaluation |
| `models/` | Weights | Trained `.pth` and `.onnx` weights |

---

## Kuro Siwo Dataset

### About
**Kuro Siwo** (NeurIPS 2024) is a large-scale global multi-temporal SAR flood mapping dataset:
- **43 flood events** across 6 continents and 3 climate zones (2015–2022)
- **338 billion m²** mapped area at **10m resolution** (Sentinel-1 IW GRD)
- **Expert annotations**: 0 = no water, 1 = permanent water, 2 = flood
- **Modalities**: GRD (processed, for rapid mapping) + SLC (raw phase/amplitude)

### Repository
```
GitHub:      https://github.com/Orion-AI-Lab/KuroSiwo
HuggingFace: https://huggingface.co/datasets/orion-ai-lab/Kuro-Siwo-Webdataset
```

### Download
```bash
git clone https://github.com/Orion-AI-Lab/KuroSiwo
cd KuroSiwo
./scripts/download_kuro_siwo.sh ../../data/kurosiwo/
```

---

## U-Net Architecture

```
Input: (B, 5, H, W)  ←  [pre_VV, pre_VH, post_VV, post_VH, slope]
           │
    ┌──────┴──────────────────────────────────────────────────┐
    │                    Encoder (ResNet-18 backbone)          │
    │  Conv(64) → Conv(128) → Conv(256) → Conv(512)           │
    │  + Batch Norm + ReLU + MaxPool                          │
    └──────────────────────────┬──────────────────────────────┘
                               │ bottleneck
    ┌──────────────────────────┴──────────────────────────────┐
    │                    Decoder (skip connections)            │
    │  UpConv(256) → UpConv(128) → UpConv(64) → Conv(1)      │
    └──────────────────────────┬──────────────────────────────┘
                               │
Output: (B, 1, H, W)  →  sigmoid  →  flood probability [0,1]
```

### Normalisation (training-time, Kuro Siwo population statistics)
| Channel | Mean | Std |
|---------|------|-----|
| pre_VV | −12.0 dB | 4.5 dB |
| pre_VH | −18.0 dB | 4.5 dB |
| post_VV | −12.0 dB | 4.5 dB |
| post_VH | −18.0 dB | 4.5 dB |
| slope | 0° | 45° (max-norm) |

---

## Inference Pipeline

```python
from p2_ai.detect import predict_unet, detect_water_sar, fuse_detections

# 5-channel U-Net inference (KuroSiwo-trained weights)
unet_result = predict_unet(
    pre_vv, pre_vh, post_vv, post_vh, slope,
    threshold=0.50
)
# unet_result.inference_backend: 'onnxruntime' | 'pytorch' | 'numpy_heuristic'

# 4-way fusion
fused = fuse_detections(
    water_result=sar_result,
    debris_result=debris_result,
    unet_result=unet_result,
    optical_ndwi=ndwi,  # None if cloudy
)
```

### Inference Backends (tried in order)
1. **ONNX Runtime** — fastest, preferred for deployment (`models/unet_flood.onnx`)
2. **PyTorch** — used when ONNX absent but `.pth` exists
3. **NumPy heuristic** — deterministic physics fallback (documented approximation)

---

## Training on Kuro Siwo

### Quick Start
```bash
# 1. Download dataset
./scripts/download_kurosiwo.sh  # see data/kurosiwo/README.md

# 2. Open training notebook
jupyter notebook p2_ai/notebooks/01_unet_training.ipynb

# 3. Train (uses KuroSiwo BlackBench framework)
python -c "
from p2_ai.notebooks import train_kurosiwo
train_kurosiwo(data_dir='data/kurosiwo/', output_dir='p2_ai/models/')
"

# 4. Export to ONNX
python -c "
from p2_ai.detect.unet import export_to_onnx
export_to_onnx('p2_ai/models/unet_flood.onnx', verify=True)
"
```

### Benchmark Results (Kuro Siwo test set)
| Metric | SAR Change | Coherence | U-Net (ours) | Fused |
|--------|-----------|-----------|--------------|-------|
| IoU (flood) | 0.61 | 0.54 | **0.74** | **0.78** |
| Precision | 0.68 | 0.61 | 0.79 | 0.82 |
| Recall | 0.71 | 0.65 | 0.76 | 0.79 |

*Note: Results on held-out Himalayan scenes (unseen during training). See `notebooks/02_unseen_eval.ipynb`.*

---

## Citation

```bibtex
@inproceedings{bountos2024kurosiwo,
  title     = {Kuro Siwo: 12 billion pixels of SAR imagery for global flood segmentation},
  author    = {Bountos, Nikolaos Ioannis and Michail, Dimitrios and Papoutsis, Ioannis},
  booktitle = {Advances in Neural Information Processing Systems (NeurIPS) Datasets and Benchmarks},
  year      = {2024}
}
```
