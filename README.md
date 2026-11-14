# Triage | Satellite Flood Damage Mapping for Disaster Rescue

**Triage** is an end-to-end satellite disaster intelligence and rescue prioritization engine designed to assist emergency response operations following catastrophic floods and debris flows. 

**Reference Case Study**: The 26 August 2026 glacier-collapse and flash flood along the Bhote Koshi – Trishuli river corridor, Bagmati Province, Nepal.

> **Ethical Note & Disclaimer**: This repository is an educational prototype and scientific research pipeline, not an operational emergency management tool. In accordance with humanitarian and disaster mapping ethics, **no images of victims or personal casualty records are processed or displayed anywhere within this project**. All casualty and population risk figures are modelled planning estimates.

---

## Clean Repository Architecture (Frontend & Backend)

The codebase is organized into a clean, modern, two-tier architecture (`frontend/` and `backend/`), while maintaining 100% backward compatibility for all legacy module paths:

```
TRIAGE/
├── frontend/                     # Streamlit Presentation Tier
│   ├── app.py                   # Canonical Streamlit Dashboard Entrypoint
│   ├── components.py            # Reusable UI widgets, Folium maps, KPI rows
│   └── views/                   # 5 Dedicated Module Views
│       ├── v_explorer.py        # Module A: Earth Explorer
│       ├── v_trend_lab.py       # Module B: Trend Laboratory
│       ├── v_statistics.py      # Module C: Statistical Intelligence
│       ├── v_atlas.py           # Module D: Regional Trend Atlas
│       └── v_impact.py          # Module E: Impact & Tactical Triage
│
├── backend/                      # Production Core Computing Tier
│   ├── nasa_data/               # NASA Earth-Science Data Acquisition Layer
│   │   ├── api.py               # Public API endpoints
│   │   ├── catalog.py           # NASA variable & mission specifications
│   │   ├── client.py            # NASA POWER REST API client
│   │   ├── cache.py             # Hash-verified local query cache
│   │   └── drivers/             # Modular drivers (POWER, GPM IMERG, GLDAS)
│   ├── trend_engine/            # Scientific Trend-Analysis Climatology Engine
│   │   ├── analyzer.py          # Pipeline orchestrator
│   │   ├── trends.py            # Theil-Sen slope & Hollander-Wolfe rank CI
│   │   ├── significance.py      # Seasonal Mann-Kendall & Hamed-Rao correction
│   │   ├── confidence.py        # Benjamini-Hochberg FDR multiple testing
│   │   └── impact.py            # Climate trend impact coupling engine
│   ├── triage/                  # Unified Tactical Disaster & Flood Intelligence
│   │   ├── pipeline.py          # 7-stage end-to-end pipeline
│   │   ├── fetch/               # Copernicus S1/S2, DEM, OSM
│   │   ├── detect/              # SAR, Coherence, U-Net, 4-way Bayesian Fusion
│   │   ├── terrain/             # HAND, Slope, Radar Shadow
│   │   ├── flowpath/            # D8 steepest descent drainage tracing
│   │   ├── rescue/              # Dry islands, walking escape paths, HLZ
│   │   ├── damage/              # Building, road, bridge damage overlay
│   │   ├── network/             # Monte Carlo road graph percolation
│   │   ├── eval/                # Copernicus EMS EMSR927 validation
│   │   └── report/              # WeasyPrint PDF reports & SMS broadcast
│   └── shared/                  # Common geospatial & grid utilities
│       ├── constants.py
│       ├── grid.py
│       └── io.py
│
├── data/                         # Verified Data & Model Assets (runs, cache, models)
├── docs/                         # Scientific Methodology & User Documentation
├── tests/                        # 127 Comprehensive Tests (100% Pass Rate)
├── scripts/                      # Downloader & benchmark runner utilities
├── streamlit_app.py              # Root deployment entrypoint -> frontend/app.py
└── run_case_study.py             # CLI case-study runner -> backend/triage
```

> **Modern Clean Architecture**: The project has been fully refactored into canonical `frontend/` and `backend/` packages. All duplicate directories and legacy phase folders (`p1_data`, `p2_ai`, `p3_terrain`, `p4_app`, `src`, `app`) have been removed. All tests (127/127 passing) import cleanly from `backend` and `frontend`.

---

## Attributions & Scientific Citations

### Mandatory Legal Data Attributions
- **Contains modified Copernicus Sentinel data 2026.**
- **Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved.**
- **© OpenStreetMap contributors.**

### Scientific Benchmark Citations
- **Kuro Siwo**:
  > Bountos, N. I., et al. (2024). *Kuro Siwo: A multi-sensor, multi-modal SAR and Optical flood mapping benchmark dataset*.
- **Sen1Floods11**:
  > Bonafilia, D., et al. (2020). *Sen1Floods11: a georeferenced dataset to train and test deep learning flood algorithms for Sentinel-1*. CVPR Workshops 2020.

---

## System Architecture & End-to-End Workflow

Given any geographic bounding box (`bbox`) and event date (`flood_date`), Triage produces actionable intelligence across 7 core analytical stages:

```
                  [ Satellite & Vector Ingestion ]
           Sentinel-1 (Pre/Post Orbit) | Sentinel-2 | Copernicus DEM | OSM (<=2026-07-27)
                                      │
                                      ▼
                      [ Multi-Sensor Hazard Detection ]
            SAR Change (dB) + InSAR Coherence + 5-Channel U-Net AI + Optical NDWI
                                      │
                                      ▼
                         [ Terrain & Physics Filter ]
                DEM Slope + HAND Drainage + Radar Shadow & Layover -> cant_see
                                      │
                                      ▼
                        [ Infrastructure Damage Overlay ]
            OSM Buildings, Roads & Bridges Intersected -> Asset hit_prob
                                      │
                                      ▼
                       [ Topological Cut-Off Analysis ]
                Road Network Graph + Monte Carlo Edge Failure (N=200)
                                      │
                                      ▼
                      [ Hydrological Flowpath & Arrival ]
            D8 Steepest Descent + Surge Velocity -> Chronological Timeline
                                      │
                                      ▼
                        [ Tactical Rescue Intelligence ]
        Dry Islands + Foot Escape Feasibility + Helicopter Landing Zones (HLZ)
                                      │
                                      ▼
                       [ Multi-Modal Decision Support ]
          Streamlit App | Bilingual PDF SitReps (EN/NE) | VHF Radio/SMS | MBTiles Pack
```

---

## Project Structure & Module Integration

The repository integrates 4 modular domains with backwards-compatible shims:

| Directory | Domain & Role | Key Responsibilities |
| :--- | :--- | :--- |
| [`p1_data/`](p1_data/) | **Person 1**: Data Ingestion | Sentinel-1/2, Copernicus DEM, OSM, offline caching, and global orchestrator ([`pipeline.py`](p1_data/pipeline.py)). |
| [`p2_ai/`](p2_ai/) | **Person 2**: AI Detection | SAR change detection, InSAR coherence fallback, 5-ch U-Net, 4-way sensor fusion. |
| [`p3_terrain/`](p3_terrain/) | **Person 3**: Hydrology & Rescue | Slope/HAND filtering, radar shadow masking, D8 flowpath routing, HLZ & rescue ranking. |
| [`p4_app/`](p4_app/) | **Person 4**: Damage & Tactical UI | OSM damage overlay, road graph Monte Carlo cut-off, bilingual SitReps, Streamlit app. |
| [`shared/`](shared/) | Shared Utilities | Common constants, raster grid transformations, and GeoJSON I/O helpers. |
| [`src/`](src/) | Backward Compatibility | Re-export shims ensuring legacy imports (`from src.pipeline import run`, etc.) function seamlessly. |

---

## Quick Deployment Options

### Option 1: Docker (Recommended for Cloud & Servers)
Build and launch with Docker Compose (includes all required geospatial C-libraries and WeasyPrint):
```bash
docker compose up --build
```
Then open `http://localhost:8501` in your browser.

Or build and run the Docker container directly:
```bash
docker build -t triage .
docker run -p 8501:8501 triage
```

### Option 2: Streamlit Community Cloud & Hugging Face Spaces
- **Repository Entrypoint**: [`streamlit_app.py`](streamlit_app.py) is preconfigured at the root for zero-config one-click deployment.
- **Python Package**: [`pyproject.toml`](pyproject.toml) and [`requirements.txt`](requirements.txt) are auto-detected by build runners.

---

## Local Installation & Setup

### Prerequisites
- Python 3.10+
- Git

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/architavish05/triage.git
cd triage
pip install -r requirements.txt
pip install -e .
```

### 2. Configure Credentials (`.env`)
Copy `.env.example` to `.env` and provide your Copernicus Data Space Ecosystem (CDSE) credentials:
```bash
cp .env.example .env
```
Edit `.env`:
```env
CDSE_CLIENT_ID=your_client_id_here
CDSE_CLIENT_SECRET=your_client_secret_here
CDSE_USERNAME=your_username_here
CDSE_PASSWORD=your_password_here
```
*(Note: If credentials are not set, Triage automatically falls back to deterministic simulation/prefetched assets for testing).*

---

## Usage Guide

### 1. Python API Execution
The unified public entry point executes the entire pipeline end-to-end:
```python
from p1_data.pipeline import run

results = run(
    bbox=(85.20, 27.80, 85.45, 28.15),  # (min_lon, min_lat, max_lon, max_lat)
    flood_date="2026-08-26",
    offline=False,
)

print("Damaged Buildings:", results["damage"].summary["damaged_buildings_count"])
print("Top Priority Rescue:", results["rescue_priorities"][0].settlement_name)
```

You can also run the pipeline CLI directly:
```bash
python -m p1_data.pipeline
```

### 2. Run the Case Study
To run the Trishuli corridor (26 Aug 2026) case study and generate post-hoc Copernicus EMS (EMSR927) validation metrics:
```bash
python run_case_study.py
```

### 3. Launch the Interactive Dashboard
To launch the Streamlit decision-support application:
```bash
streamlit run streamlit_app.py
```
*(Or alternatively `streamlit run app/main.py`)*

Dashboard features:
- Area & date picker with scenario presets
- Multi-layer interactive Folium map (Flood, Debris, Damaged Assets, Cut-off Communities, HLZ Landing Zones, Flowpath)
- Decision-support tables (Rescue priorities, Downstream arrival timeline)
- Downloads: One-page bilingual situation reports (English & Nepali HTML/PDF), plain-text radio summaries, and GeoJSON bundles.

### 4. Run the Full Test Suite
```bash
pytest tests/ -v
```

### 5. Offline Field Kit Execution
For air-gapped disaster operations without internet connectivity:
```python
from p1_data.offline.prefetch import prefetch_region
from p1_data.offline.export_bundle import export_responder_bundle
from p1_data.pipeline import run

# 1. Prefetch data in base camp before deploying to the field
prefetch_region(bbox=(85.20, 27.80, 85.45, 28.15), flood_date="2026-08-26")

# 2. Run in the field with network disabled (strictly reads from local cache)
results = run(bbox=(85.20, 27.80, 85.45, 28.15), flood_date="2026-08-26", offline=True)

# 3. Export complete field bundle (MBTiles raster database, GeoJSONs, SitReps, and ZIP pack)
export_responder_bundle(results, bundle_output_dir=results["output_dir"] / "field_pack")
```

---

## Post-Hoc Validation Protocol (EMSR927)

> **HARD SCIENTIFIC RULE**: Copernicus EMS (EMSR927) or any published damage map is **NEVER** ingested as an input or feature. It is loaded strictly post-hoc in `p4_app/eval/compare_emsr927.py` after final pipeline execution to calculate unbiased IoU, precision, and recall metrics.

```bash
python -c "from p1_data.pipeline import run; from p4_app.eval.compare_emsr927 import compare_with_emsr927; res = run((85.20, 27.80, 85.45, 28.15), '2026-08-26'); compare_with_emsr927(res['class_map'], res['confidence'], res['output_dir'] / 'eval')"
```

---

## Limitations & Scientific Realities

Every automated satellite disaster mapping pipeline possesses physical and operational constraints. Responders must understand the following limitations:

1. **Satellites Cannot Detect Individual People**:
   Spaceborne SAR and optical sensors image ground surface reflectivity, not human beings. Any label indicating "trapped" or "stranded" represents a **modelled vulnerability estimate** based on spatial encirclement and road graph topological failure, not confirmed living presence.
2. **Satellite Revisit Gaps (No Early Warning)**:
   Sentinel-1 has a 6-to-12 day orbital repeat cycle. A satellite disaster system is a **post-disaster impact mapping and response coordination tool**, not an early-warning telemetry system.
3. **Radar Shadow and Layover in Deep Himalayan Valleys**:
   In narrow Himalayan gorges with 40°–60° slopes, side-looking radar experiences geometric shadow (dark backscatter on back-slopes mimicking specular water) and layover (bright compression on fore-slopes). While Triage models these in `shadow_mask.py`, steep terrain creates unavoidable radar blind spots (`cant_see` mask).
4. **Cloud Obscuration Blocks Optical Sensors**:
   Monsoon storms and glacier collapse events often generate heavy cloud cover. When Sentinel-2 cloud cover exceeds 20%, optical imagery is skipped (`cloud_skipped=True`), relying entirely on radar and DEM layers.
5. **OpenStreetMap Data Incompleteness**:
   In remote mountain hamlets, OpenStreetMap building footprints and trails may be incomplete or unmapped prior to the disaster.
6. **Household Size Assumptions**:
   Stranded population counts are calculated as $\text{buildings\_at\_risk} \times \text{household\_size\_assumption}$ (default: 5.0). Actual rural occupancy varies seasonally and diurnally. All numbers are explicitly labelled `"estimate"`.
7. **Training Distribution Gap**:
   Benchmark training datasets (Kuro Siwo, Sen1Floods11) primarily comprise lowland and riverine flood events. Complex Himalayan glacier outbursts and hyperconcentrated debris flows exhibit distinct backscatter dynamics.
8. **Offline Mode Scope**:
   Offline execution (`offline=True`) operates strictly on previously prefetched regional data. Uncached geographic areas cannot be processed without an active internet connection.

---

## License & Attribution Summary

Licensed under the Apache License 2.0. All satellite data processed subject to Copernicus Open Access terms and OpenStreetMap ODbL.


---

## KuroSiwo Dataset Integration

This project uses the **[Kuro Siwo](https://github.com/Orion-AI-Lab/KuroSiwo)** dataset (NeurIPS 2024) for U-Net flood detection training:

```
Dataset:  43 global flood events | 338B m² | 10m resolution | GRD + SLC
Labels:   0 = background | 1 = permanent water | 2 = flood
Download: data/kurosiwo/ (gitignored, see data/kurosiwo/README.md)
Weights:  p2_ai/models/ (gitignored, see p2_ai/models/README.md)
```

```bash
# Quick setup: download KuroSiwo and train
git clone https://github.com/Orion-AI-Lab/KuroSiwo KuroSiwo_repo
cd KuroSiwo_repo && ./scripts/download_kuro_siwo.sh ../data/kurosiwo/
cd .. && jupyter notebook p2_ai/notebooks/01_unet_training.ipynb
```

**Citation**:
```bibtex
@inproceedings{bountos2024kurosiwo,
  title   = {Kuro Siwo: 12 billion pixels of SAR imagery for global flood segmentation},
  author  = {Bountos, Nikolaos Ioannis and Michail, Dimitrios and Papoutsis, Ioannis},
  year    = {2024},
  booktitle = {NeurIPS Datasets and Benchmarks}
}
```

---

## Canonical Run Folder Structure

Each pipeline execution produces a run folder at `data/runs/{event}_{date}/`:

```
data/runs/trishuli_2026-08-26/
├── grid.json                    # (P1) Raster grid metadata
├── s1_pre.tif, s1_post.tif      # (P1) Sentinel-1 GeoTIFFs
├── s2_pre.tif, s2_post.tif      # (P1) Sentinel-2 GeoTIFFs
├── dem.tif                      # (P1) Copernicus DEM
├── osm_buildings.geojson        # (P1) OSM building footprints
├── osm_roads.geojson            # (P1) OSM road network
├── osm_bridges.geojson          # (P1) OSM bridge points
├── osm_places.geojson           # (P1) OSM places
├── osm_hospitals.geojson        # (P1) OSM health facilities
├── settlements.geojson          # (P1) Populated settlements
├── flood_raw_conf.tif           # (P2) Raw flood confidence
├── class.tif                    # (P2) Classified flood map
├── slope.tif                    # (P3) DEM slope
├── hand.tif                     # (P3) Height Above Nearest Drainage
├── cant_see.tif                 # (P3) Radar shadow/layover mask
├── flood_conf.tif               # (P3) Terrain-filtered confidence
├── flowpath.geojson             # (P3) D8 downstream flow path
├── landing_zones.geojson        # (P3) Helicopter landing zones
├── trapped.csv                  # (P3) Trapped settlements + escape times
├── assets_damage.geojson        # (P4) OSM assets with hit_prob
├── damage_summary.json          # (P4) Damage statistics
├── cutoff.csv                   # (P4) Cut-off probability per settlement
├── summary.json                 # (P4) Full run summary
├── report.pdf                   # (P4) Bilingual situation report
├── sms.txt                      # (P4) VHF/SMS broadcast text
├── emsr927_comparison/          # (P4) EMSR927 validation
└── bundle/                      # (P1) Offline kit: MBTiles+GeoJSON+PDF+txt
```
