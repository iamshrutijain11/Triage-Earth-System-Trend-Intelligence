# System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                   TRIAGE SATELLITE FLOOD PIPELINE                   │
│              Bhote Koshi – Trishuli, Nepal | 2026-08-26             │
└─────────────────────────────────────────────────────────────────────┘

INPUT: bbox(min_lon, min_lat, max_lon, max_lat) + flood_date
                            │
            ┌───────────────┼───────────────┐
            │               │               │
    ┌───────▼──────┐ ┌──────▼─────┐ ┌──────▼──────┐
    │ Sentinel-1   │ │ Sentinel-2 │ │Copernicus DEM│
    │ GRD (VV/VH) │ │ (RGB/SWIR) │ │  + OSM data │
    │  pre + post  │ │            │ │             │
    └───────┬──────┘ └──────┬─────┘ └──────┬──────┘
            └───────────────┼───────────────┘
                        P1_DATA
                            │
            ┌───────────────┼───────────────┐
            │               │               │
    ┌───────▼──────┐ ┌──────▼─────┐ ┌──────▼──────┐
    │  SAR Change  │ │  InSAR     │ │  KuroSiwo   │
    │  Detection   │ │ Coherence  │ │  U-Net 5ch  │
    │  (dB ratio)  │ │ (fallback) │ │ + NDWI fuse │
    └───────┬──────┘ └──────┬─────┘ └──────┬──────┘
            └───────────────┼───────────────┘
                        P2_AI → flood_raw_conf.tif
                            │
            ┌───────────────┼───────────────┐
            │               │               │
    ┌───────▼──────┐ ┌──────▼─────┐ ┌──────▼──────┐
    │  DEM Slope   │ │   HAND     │ │Radar Shadow │
    │  Filter      │ │  Drainage  │ │  & Layover  │
    └───────┬──────┘ └──────┬─────┘ └──────┬──────┘
            └───────────────┼───────────────┘
                       P3_TERRAIN → flood_conf.tif
                            │
            ┌───────────────┼───────────────┐
            │               │               │
    ┌───────▼──────┐ ┌──────▼─────┐ ┌──────▼──────┐
    │ OSM Damage   │ │  Road Cut  │ │  D8 Flow   │
    │  Overlay     │ │  Off Monte │ │  Trace +   │
    │ hit_prob     │ │  Carlo N=200│ │  Arrival   │
    └───────┬──────┘ └──────┬─────┘ └──────┬──────┘
            └───────────────┼───────────────┘
                        P4_APP
                            │
            ┌───────────────┼───────────────┐
            │               │               │
    ┌───────▼──────┐ ┌──────▼─────┐ ┌──────▼──────┐
    │  Rescue      │ │ Helicopter │ │  Bilingual  │
    │  Priority    │ │  Landing   │ │  PDF SitRep │
    │  Ranking     │ │  Zones HLZ │ │  + SMS/VHF  │
    └───────┬──────┘ └──────┬─────┘ └──────┬──────┘
            └───────────────┼───────────────┘
                            │
    ┌───────────────────────▼────────────────────────┐
    │              STREAMLIT DASHBOARD               │
    │  Interactive map | KPI panel | Priority table  │
    │  Detail tabs | PDF download | Offline bundle   │
    └────────────────────────────────────────────────┘
```
