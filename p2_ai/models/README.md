# p2_ai/models — Trained Model Weights

This directory holds trained model weights for the Triage flood detection pipeline.

## Files

| File | Description |
|------|-------------|
| `unet_flood_best.pth` | PyTorch checkpoint — best U-Net weights trained on Kuro Siwo GRD subset |
| `unet_flood.onnx` | ONNX export for CPU-only inference (no GPU required) |
| `unet_metadata.json` | Architecture metadata: channel order, normalisation stats, training info |

## Training Data

Weights are trained on the **Kuro Siwo** dataset (NeurIPS 2024):
- **Source**: [Orion-AI-Lab/KuroSiwo](https://github.com/Orion-AI-Lab/KuroSiwo)
- **HuggingFace**: [orion-ai-lab/Kuro-Siwo-Webdataset](https://huggingface.co/datasets/orion-ai-lab/Kuro-Siwo-Webdataset)
- **Subset used**: GRD flood events from South/Southeast Asia (43 global events, 10m resolution)
- **Labels**: 0 = no water, 1 = permanent water, 2 = flood

## Input Specification

```
Input tensor:  (B, 5, H, W)  float32
Channels:
  0  pre_vv   — Pre-event Sentinel-1 VV backscatter (dB)
  1  pre_vh   — Pre-event Sentinel-1 VH backscatter (dB)
  2  post_vv  — Post-event Sentinel-1 VV backscatter (dB)
  3  post_vh  — Post-event Sentinel-1 VH backscatter (dB)
  4  slope    — DEM terrain slope (degrees)

Normalisation (training-time statistics):
  VV: mean = -12.0 dB,  std = 4.5 dB
  VH: mean = -18.0 dB,  std = 4.5 dB
  Slope: clipped at 45°, divided by 45 → [0, 1]
```

## Download

```bash
# From KuroSiwo repo
git clone https://github.com/Orion-AI-Lab/KuroSiwo
cd KuroSiwo
./scripts/download_kuro_siwo.sh data/kurosiwo/

# Train and export
python main.py --method=unet --backbone=resnet18 --dem=True
# then copy trained weights to this directory
```

> **Note**: Weights files (*.pth, *.onnx) are gitignored due to size.
> The `unet.py` module falls back to a numpy physics-based heuristic when weights are absent.
