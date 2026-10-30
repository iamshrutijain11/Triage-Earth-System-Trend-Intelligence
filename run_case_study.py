"""Case study execution script: Bhote Koshi – Trishuli River Corridor, Nepal (26 Aug 2026).

Executes the complete Triage pipeline on the disaster scene, followed by
post-hoc validation against Copernicus EMS EMSR927.

KuroSiwo Dataset Integration
-----------------------------
The U-Net flood detector (p2_ai/detect/unet.py) is trained on the **Kuro Siwo**
benchmark (NeurIPS 2024):
    Repo:   https://github.com/Orion-AI-Lab/KuroSiwo
    HF:     https://huggingface.co/datasets/orion-ai-lab/Kuro-Siwo-Webdataset
    Paper:  Bountos et al. 2024 — 43 flood events, 338B m², 10m GRD Sentinel-1

To train with KuroSiwo data before running this script:
    1. Download:  see data/kurosiwo/README.md
    2. Train:     jupyter notebook p2_ai/notebooks/01_unet_training.ipynb
    3. Export:    python -c "from p2_ai.detect.unet import export_to_onnx; export_to_onnx('p2_ai/models/unet_flood.onnx')"

Usage
-----
    python run_case_study.py [--offline] [--output-dir PATH] [--skip-eval]

Without trained weights the pipeline falls back to a documented numpy physics
heuristic (clearly flagged in all outputs).
"""

import argparse
import json
import logging
import shutil
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from p1_data.pipeline import run
from p4_app.eval.compare_emsr927 import compare_with_emsr927

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("case_study")

# ─── KuroSiwo model availability check ───────────────────────────────────────
_MODELS_DIR = repo_root / "p2_ai" / "models"
_ONNX_PATH = _MODELS_DIR / "unet_flood.onnx"
_PTH_PATH = _MODELS_DIR / "unet_flood_best.pth"


def _check_kurosiwo_model() -> str:
    """Return inference backend that will be used; warn if falling back."""
    if _ONNX_PATH.exists():
        return "onnxruntime"
    if _PTH_PATH.exists():
        return "pytorch"
    logger.warning(
        "No trained KuroSiwo weights found in p2_ai/models/. "
        "Using numpy physics heuristic fallback. "
        "Train with p2_ai/notebooks/01_unet_training.ipynb for real predictions."
    )
    return "numpy_heuristic (fallback)"


def _mirror_to_runs_folder(processed_dir: Path, runs_dir: Path) -> None:
    """Copy key outputs from processed/ into the canonical data/runs/ layout.

    The CONTRACT.md specifies exact filenames in data/runs/{event}/  which
    differ slightly from the internal processed/ layout.  This function
    produces the canonical structure expected by the project spec.
    """
    runs_dir.mkdir(parents=True, exist_ok=True)

    # GeoJSON outputs
    geojson_src = processed_dir / "geojson"
    if geojson_src.exists():
        for src_file, dst_name in [
            ("damaged_buildings.geojson", "osm_buildings.geojson"),
            ("damaged_roads.geojson", "osm_roads.geojson"),
            ("damaged_bridges.geojson", "osm_bridges.geojson"),
            ("landing_zones.geojson", "landing_zones.geojson"),
            ("downstream_trace.json", "flowpath.geojson"),
            ("damage_summary.json", "damage_summary.json"),
            ("assets_damage.geojson", "assets_damage.geojson"),
            ("cutoff_settlements.geojson", "cutoff_settlements.geojson"),
        ]:
            src = geojson_src / src_file
            if src.exists():
                shutil.copy2(src, runs_dir / dst_name)

    # Top-level summary & reports
    for src_file in ["summary.json", "cutoff.csv"]:
        src = processed_dir / src_file
        if src.exists():
            shutil.copy2(src, runs_dir / src_file)

    # Reports → report.pdf + sms.txt
    reports_src = processed_dir / "reports"
    if reports_src.exists():
        for src_file, dst_name in [
            ("sitrep_en.pdf", "report.pdf"),
            ("sitrep_sms.txt", "sms.txt"),
        ]:
            src = reports_src / src_file
            if src.exists():
                shutil.copy2(src, runs_dir / dst_name)

    # EMSR927 validation
    emsr_src = processed_dir / "eval_emsr927"
    if emsr_src.exists():
        emsr_dst = runs_dir / "emsr927_comparison"
        emsr_dst.mkdir(exist_ok=True)
        for f in emsr_src.glob("*"):
            shutil.copy2(f, emsr_dst / f.name)

    logger.info("Canonical run folder populated at: %s", runs_dir)


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Triage case study: Bhote Koshi – Trishuli, Nepal 2026-08-26"
    )
    parser.add_argument(
        "--offline", action="store_true",
        help="Operate strictly from cached data (no satellite API calls)."
    )
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help="Override output directory (default: data/processed/trishuli_case_study_20260826)."
    )
    parser.add_argument(
        "--skip-eval", action="store_true",
        help="Skip EMSR927 post-hoc validation step."
    )
    parser.add_argument(
        "--runs-dir", type=str, default=None,
        help="Override canonical runs folder (default: data/runs/trishuli_2026-08-26)."
    )
    parsed = parser.parse_args(args)

    logger.info("=================================================================")
    logger.info("TRIAGE CASE STUDY: Bhote Koshi – Trishuli Corridor (26 Aug 2026)")
    logger.info("=================================================================")

    # ── Model check ──────────────────────────────────────────────────────────
    backend = _check_kurosiwo_model()
    logger.info("Flood detection backend: %s", backend)

    # ── Pipeline parameters ───────────────────────────────────────────────────
    bbox = (85.20, 27.80, 85.45, 28.15)   # Bhote Koshi – Trishuli corridor, Nepal
    flood_date = "2026-08-26"
    output_dir = Path(parsed.output_dir) if parsed.output_dir else \
        Path("data/processed/trishuli_case_study_20260826")
    runs_dir = Path(parsed.runs_dir) if parsed.runs_dir else \
        Path("data/runs/trishuli_2026-08-26")

    # ── Step 1: End-to-end pipeline ───────────────────────────────────────────
    logger.info("[1/3] Running end-to-end Triage pipeline...")
    results = run(
        bbox=bbox,
        flood_date=flood_date,
        offline=parsed.offline,
        output_dir=output_dir,
    )

    logger.info("=================================================================")
    logger.info("PIPELINE EXECUTION COMPLETE")
    logger.info("=================================================================")

    damage_summary = results["damage"].summary
    print("\n" + "="*65)
    print("  TRIAGE CASE STUDY RESULTS — Trishuli Corridor, Nepal 2026-08-26")
    print("="*65)
    print(f"\n  Flood detection backend:  {results.get('inference_backend', backend)}")
    print(f"\n  INFRASTRUCTURE DAMAGE IMPACTS")
    print(f"  {'Damaged Buildings:':<30} {damage_summary.get('damaged_buildings_count', 0)}")
    print(f"  {'Damaged Roads:':<30} {damage_summary.get('damaged_roads_km', 0.0):.1f} km")
    print(f"  {'Impassable Road Cuts:':<30} {damage_summary.get('impassable_roads_count', 0)}")
    print(f"  {'Damaged Bridges:':<30} {damage_summary.get('damaged_bridges_count', 0)}")
    print(f"  {'Dry Islands Identified:':<30} {results['dry_islands_count']}")

    print(f"\n  TOP RESCUE PRIORITIES")
    for item in results["rescue_priorities"][:5]:
        print(
            f"  Rank #{item.rank}: {item.settlement_name} ({item.place_type})\n"
            f"    Cut-off: {item.cutoff_prob*100:.1f}% | "
            f"Trapped Risk: {item.trapped_risk*100:.1f}% | "
            f"At-Risk Bldgs: {item.buildings_at_risk} | "
            f"~{item.stranded_population_estimate} persons\n"
            f"    Action: {item.recommended_action}"
        )

    print(f"\n  REPORTS SAVED TO: {output_dir}/reports/")

    # ── Step 2: Mirror to canonical data/runs/ layout ─────────────────────────
    logger.info("[2/3] Populating canonical data/runs/ folder...")
    _mirror_to_runs_folder(output_dir, runs_dir)
    print(f"\n  CANONICAL RUN FOLDER: {runs_dir}")

    # ── Step 3: EMSR927 post-hoc validation ───────────────────────────────────
    if not parsed.skip_eval:
        logger.info("[3/3] Post-hoc validation against Copernicus EMS EMSR927...")
        eval_dir = output_dir / "eval_emsr927"
        eval_res = compare_with_emsr927(
            pipeline_class_map=results["class_map"],
            pipeline_confidence=results["confidence"],
            output_dir=eval_dir,
            threshold=0.35,
        )

        print(f"\n  COPERNICUS EMS (EMSR927) VALIDATION METRICS")
        print(f"  {'IoU (Intersection-over-Union):':<35} {eval_res.iou:.4f}")
        print(f"  {'Precision:':<35} {eval_res.precision:.4f}")
        print(f"  {'Recall:':<35} {eval_res.recall:.4f}")
        print(f"  {'F1 Score:':<35} {eval_res.f1_score:.4f}")
        print(f"  Plot: {eval_res.side_by_side_plot_path}")
        print(f"  JSON: {eval_res.metrics_json_path}")

        # Copy eval outputs to canonical runs folder
        emsr_runs = runs_dir / "emsr927_comparison"
        emsr_runs.mkdir(exist_ok=True)
        if eval_dir.exists():
            for f in eval_dir.glob("*"):
                shutil.copy2(f, emsr_runs / f.name)
    else:
        logger.info("[3/3] EMSR927 validation skipped (--skip-eval).")

    print("\n" + "="*65)
    print("  KuroSiwo Dataset: https://github.com/Orion-AI-Lab/KuroSiwo")
    print("  Train weights:    jupyter notebook p2_ai/notebooks/01_unet_training.ipynb")
    print("="*65 + "\n")


if __name__ == "__main__":
    main()
