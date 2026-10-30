# p1_data/ — Data Ingestion Module

Owns satellite and vector data ingestion for the Triage pipeline.

---

## Module Overview

| Submodule | File | Description |
|-----------|------|-------------|
| `fetch/s1.py` | Sentinel-1 | Sentinel-1 IW GRD pre/post-event acquisition (VV/VH) |
| `fetch/s2.py` | Sentinel-2 | Sentinel-2 L2A optical imagery + NDWI cloud masking |
| `fetch/dem.py` | DEM | Copernicus WorldDEM-30 / GLO-30 elevation model |
| `fetch/osm.py` | OSM | OpenStreetMap buildings, roads, bridges, places, hospitals |
| `fetch/cache.py` | Cache | Disk-based tile caching with hash-keyed directories |
| `offline/prefetch.py` | Prefetch | Pre-download all assets for offline operation |
| `offline/export_bundle.py` | Bundle | Export MBTiles + GeoJSON + PDF + SMS offline pack |
| `pipeline.py` | Orchestrator | End-to-end `run()` entrypoint — calls all 7 stages |

---

## Pipeline Orchestrator (`pipeline.py`)

The main `run()` function orchestrates all pipeline stages:

```python
from p1_data.pipeline import run

results = run(
    bbox=(85.20, 27.80, 85.45, 28.15),  # (min_lon, min_lat, max_lon, max_lat)
    flood_date="2026-08-26",
    offline=False,         # True = cached assets only
    output_dir=None,       # defaults to data/processed/{date}_{lon}_{lat}/
)
```

### 7-Stage Pipeline
```
1. Fetch (P1)      → Sentinel-1, Sentinel-2, DEM, OSM
2. Detect (P2)     → SAR change + KuroSiwo U-Net + coherence + NDWI fusion
3. Terrain (P3)    → Slope filter + HAND drainage + radar shadow mask
4. Damage (P4)     → OSM asset intersection + hit_prob
5. Cut-off (P4)    → Road graph Monte Carlo (N=200 edge failures)
6. Rescue (P3/P4)  → D8 flowpath + HLZ detection + priority ranking
7. Report (P4)     → Bilingual PDF SitRep + SMS/VHF broadcast
```

---

## Data Outputs (per run)

### Canonical Run Folder: `data/runs/{event}_{date}/`

| File | Description |
|------|-------------|
| `grid.json` | Raster grid metadata (bbox, CRS, resolution, shape, transform) |
| `s1_pre.tif`, `s1_post.tif` | Sentinel-1 VV/VH GeoTIFFs (pre and post event) |
| `s2_pre.tif`, `s2_post.tif` | Sentinel-2 RGB GeoTIFFs |
| `dem.tif` | Copernicus DEM GeoTIFF |
| `osm_buildings.geojson` | OSM building footprints |
| `osm_roads.geojson` | OSM road network |
| `osm_bridges.geojson` | OSM bridge points |
| `osm_places.geojson` | OSM populated places |
| `osm_hospitals.geojson` | OSM health facilities |
| `settlements.geojson` | Named settlements |

### Cache Directory: `data/cache/`
Hash-keyed cache preventing redundant satellite API calls.

---

## Offline Mode

```bash
# Pre-download all assets for a bbox+date (before going into the field)
python -m p1_data.offline.prefetch --bbox 85.20 27.80 85.45 28.15 --date 2026-08-26

# Export offline bundle (MBTiles + GeoJSON + PDF + SMS)
python -m p1_data.offline.export_bundle --run-dir data/runs/trishuli_2026-08-26/
```

---

## Data Sources & Attributions

| Source | Product | License |
|--------|---------|---------|
| ESA / Copernicus | Sentinel-1 IW GRD | Modified Copernicus Sentinel data 2026 |
| ESA / Copernicus | Sentinel-2 L2A | Modified Copernicus Sentinel data 2026 |
| DLR / Airbus | Copernicus WorldDEM-30 | Copernicus DEM, see ATTRIBUTIONS.md |
| OpenStreetMap | Buildings/Roads/POIs | © OpenStreetMap contributors, ODbL |

---

## Testing

```bash
pytest tests/p1_data/ -v
```
