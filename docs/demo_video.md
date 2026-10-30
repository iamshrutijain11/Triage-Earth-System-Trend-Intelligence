# Demo Video

## 3-Minute Pipeline Walkthrough

**Title**: Triage — Satellite Flood Damage & Rescue Prioritization Demo  
**Event**: Bhote Koshi–Trishuli Flash Flood, Nepal, 26 August 2026

### What the Demo Shows

1. **Data Ingestion (0:00–0:30)**  
   Sentinel-1 SAR, Sentinel-2 optical, Copernicus DEM, OSM infrastructure loading  
   with automatic caching and offline fallback.

2. **Flood Detection (0:30–1:00)**  
   KuroSiwo U-Net inference (5-channel SAR + slope), SAR change detection,  
   InSAR coherence fallback, 4-way sensor fusion result.

3. **Terrain & Physics Filter (1:00–1:30)**  
   DEM slope mask, HAND drainage filter, radar shadow/layover exclusion,  
   terrain-plausible flood extent.

4. **Damage & Rescue Intel (1:30–2:30)**  
   OSM asset hit probability, Monte Carlo road cut-off, D8 flowpath arrival  
   times, helicopter landing zones, rescue priority ranking.

5. **Dashboard & Reports (2:30–3:00)**  
   Streamlit interactive map, bilingual PDF SitRep (English/Nepali),  
   VHF/SMS broadcast text, offline MBTiles bundle export.

### Recording Instructions

```bash
# Start the Streamlit dashboard
streamlit run p4_app/app/app.py

# Or load the pre-computed case study run
streamlit run p4_app/app/app.py -- data/runs/trishuli_2026-08-26/
```

Use OBS Studio or similar screen recorder. Recommended resolution: 1920×1080.

> **Note**: Actual demo video file or YouTube link to be added here after recording.
