# data/runs — Per-Event Run Outputs

Each subdirectory corresponds to one pipeline execution.

## Naming Convention

```
{event_name}_{YYYY-MM-DD}/
```

Example: `trishuli_2026-08-26/`

## Contents (from CONTRACT.md)

| File | Phase | Description |
|------|-------|-------------|
| `grid.json` | P1 | Raster grid metadata |
| `s1_pre.tif`, `s1_post.tif` | P1 | Sentinel-1 VV/VH GeoTIFFs |
| `s2_pre.tif`, `s2_post.tif` | P1 | Sentinel-2 RGB GeoTIFFs |
| `dem.tif` | P1 | Copernicus DEM GeoTIFF |
| `osm_buildings.geojson` | P1 | OSM building footprints |
| `osm_roads.geojson` | P1 | OSM road network |
| `osm_bridges.geojson` | P1 | OSM bridge points |
| `osm_places.geojson` | P1 | OSM populated places |
| `osm_hospitals.geojson` | P1 | OSM health facilities |
| `settlements.geojson` | P1 | Named settlements |
| `flood_raw_conf.tif` | P2 | Raw flood confidence (pre-terrain filter) |
| `class.tif` | P2 | Classified map (0=bg, 1=water, 2=debris) |
| `slope.tif` | P3 | DEM slope (degrees) |
| `hand.tif` | P3 | Height Above Nearest Drainage (m) |
| `cant_see.tif` | P3 | Radar shadow/layover mask |
| `flood_conf.tif` | P3 | Terrain-filtered flood confidence |
| `flowpath.geojson` | P3 | D8 downstream flow path |
| `landing_zones.geojson` | P3 | Helicopter landing zone candidates |
| `trapped.csv` | P3 | Trapped settlement list with escape times |
| `assets_damage.geojson` | P4 | OSM assets with hit_prob |
| `damage_summary.json` | P4 | Damage statistics |
| `cutoff.csv` | P4 | Cut-off probability per settlement |
| `summary.json` | P4 | Full run summary |
| `report.pdf` | P4 | Bilingual situation report |
| `sms.txt` | P4 | VHF/SMS broadcast text |
| `bundle/` | P1 | Offline kit (MBTiles, GeoJSON, PDF, txt) |
| `emsr927_comparison/` | P4 | EMSR927 validation outputs |

> **Gitignored**: Run outputs are excluded from version control.
> Use `run_case_study.py` to regenerate.
