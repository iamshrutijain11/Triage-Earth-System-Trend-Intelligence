"""Kuro Siwo dataset downloader for Triage flood detection training.

Downloads labelled Ground Range Detected (GRD) WebDataset shards from Hugging Face:
    Repo: https://huggingface.co/datasets/orion-ai-lab/Kuro-Siwo-Webdataset
    Paper: Bountos et al., NeurIPS 2024

Usage:
    # Download 1 training shard (~10 GB, thousands of SAR flood patches):
    python scripts/download_kurosiwo.py --shards 1

    # Download all 5 training shards (~43.5 GB):
    python scripts/download_kurosiwo.py --all

    # Download test split shards:
    python scripts/download_kurosiwo.py --split test --shards 1
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from huggingface_hub import hf_hub_download, HfApi

REPO_ID = "orion-ai-lab/Kuro-Siwo-Webdataset"
DEFAULT_DEST = repo_root / "data" / "kurosiwo"


def download_kurosiwo(
    dest_dir: Path = DEFAULT_DEST,
    split: str = "train",
    num_shards: int = 1,
    download_all: bool = False,
) -> None:
    """Download GRD WebDataset tar shards from Hugging Face."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    folder_prefix = f"{split}_GRD"

    print("=" * 65)
    print("  KURO SIWO DATASET DOWNLOADER")
    print(f"  Source:      https://huggingface.co/datasets/{REPO_ID}")
    print(f"  Split:       {folder_prefix}")
    print(f"  Destination: {dest_dir}")
    print("=" * 65)

    api = HfApi()
    all_files = api.list_repo_files(REPO_ID, repo_type="dataset")
    shards = sorted([f for f in all_files if f.startswith(f"{folder_prefix}/shard-") and f.endswith(".tar")])

    if not shards:
        print(f"Error: No shards found for split '{folder_prefix}' in {REPO_ID}")
        return

    to_download = shards if download_all else shards[:num_shards]
    print(f"Found {len(shards)} available shards for {folder_prefix}.")
    print(f"Queued for download: {len(to_download)} shard(s)\n")

    for idx, shard_filename in enumerate(to_download, 1):
        target_local_path = dest_dir / shard_filename
        print(f"[{idx}/{len(to_download)}] Downloading {shard_filename} ...")
        try:
            local_file = hf_hub_download(
                repo_id=REPO_ID,
                filename=shard_filename,
                repo_type="dataset",
                local_dir=str(dest_dir),
                local_dir_use_symlinks=False,
            )
            file_size_gb = Path(local_file).stat().st_size / (1024 ** 3)
            print(f"    --> Successfully downloaded: {local_file} ({file_size_gb:.2f} GB)\n")
        except Exception as e:
            print(f"    --> Error downloading {shard_filename}: {e}\n")

    print("=" * 65)
    print("Download complete!")
    print(f"All files saved in: {dest_dir}")
    print("Train the model using: jupyter notebook p2_ai/notebooks/01_unet_training.ipynb")
    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(description="Download Kuro Siwo SAR flood dataset from Hugging Face")
    parser.add_argument(
        "--dest",
        type=str,
        default=str(DEFAULT_DEST),
        help=f"Destination directory (default: {DEFAULT_DEST})",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="train",
        choices=["train", "test"],
        help="Split to download (default: train)",
    )
    parser.add_argument(
        "--shards",
        type=int,
        default=1,
        help="Number of shards to download (default: 1, ~10 GB)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download all available shards for this split",
    )

    args = parser.parse_args()
    download_kurosiwo(
        dest_dir=Path(args.dest),
        split=args.split,
        num_shards=args.shards,
        download_all=args.all,
    )


if __name__ == "__main__":
    main()
