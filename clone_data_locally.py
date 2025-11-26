#!/usr/bin/env python3
"""
Download all circuit-sparsity data from Azure blob storage to a local directory.

This script mirrors the complete data structure from:
https://openaipublic.blob.core.windows.net/circuit-sparsity

Data Layout:
- models/<model_name>/
  - beeg_config.json: serialized GPTConfig
  - final_model.pt: checkpoint file
- viz/<experiment>/<model_name>/<task_name>/<sweep>/<k>/
  - viz_data.pkl/pt: primary payload
- train_curves/<model_name>/progress.json
- Other experiment-specific directories

Usage:
    python clone_data_locally.py [--output-dir ./data] [--verbose]

The script can be interrupted and resumed safely; it skips existing files.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

import blobfile as bf


def get_all_blobs(blob_path: str, recursive: bool = True) -> list[str]:
    """
    Recursively list all blobs under a path in Azure blob storage.

    Args:
        blob_path: Path in blob storage (e.g., "https://openaipublic.blob.core.windows.net/circuit-sparsity/models")
        recursive: If True, recursively list all files; if False, only list immediate children

    Returns:
        List of full blob paths
    """
    blobs = []

    try:
        items = bf.listdir(blob_path)
    except Exception as e:
        print(f"Warning: Could not list {blob_path}: {e}")
        return blobs

    for item in items:
        item_path = bf.join(blob_path, item)
        try:
            # Try to check if it's a file or directory
            # Files in blobfile don't have trailing slashes
            if bf.isdir(item_path):
                if recursive:
                    blobs.extend(get_all_blobs(item_path, recursive=True))
            else:
                blobs.append(item_path)
        except Exception:
            # If we can't determine type, assume it's a file
            blobs.append(item_path)

    return blobs


def download_file(blob_path: str, local_path: str, force: bool = False) -> bool:
    """
    Download a single file from blob storage to local disk.

    Args:
        blob_path: Full path to blob
        local_path: Full local file path
        force: If True, overwrite existing files

    Returns:
        True if downloaded, False if skipped
    """
    # Create parent directories if needed
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    # Skip existing files unless force=True
    if os.path.exists(local_path) and not force:
        return False

    try:
        data = bf.read_bytes(blob_path)
        with open(local_path, 'wb') as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"Error downloading {blob_path}: {e}")
        return False


def download_directory_structure(
    blob_base: str,
    local_base: str,
    subdirs: list[str],
    verbose: bool = False,
    force: bool = False,
) -> None:
    """
    Download specific subdirectories from blob storage.

    Args:
        blob_base: Base URL for blob storage
        local_base: Local base directory
        subdirs: List of subdirectories to download (e.g., ["models", "viz", "train_curves"])
        verbose: Print progress information
        force: Overwrite existing files
    """
    total_downloaded = 0
    total_skipped = 0

    for subdir in subdirs:
        blob_path = bf.join(blob_base, subdir)
        local_path = os.path.join(local_base, subdir)

        if verbose:
            print(f"\nDownloading {subdir}...")

        try:
            blobs = get_all_blobs(blob_path, recursive=True)

            if verbose:
                print(f"  Found {len(blobs)} files in {subdir}")

            for blob in blobs:
                # Convert blob path to local path
                # blob format: ".../circuit-sparsity/models/..." -> "models/..."
                rel_path = blob.split("circuit-sparsity/")[-1]
                local_file = os.path.join(local_base, rel_path)

                if download_file(blob, local_file, force=force):
                    total_downloaded += 1
                    if verbose:
                        print(f"  Downloaded: {rel_path}")
                else:
                    total_skipped += 1
                    if verbose:
                        print(f"  Skipped: {rel_path}")

        except Exception as e:
            print(f"Error processing {subdir}: {e}")

    print(f"\nDownload summary:")
    print(f"  Downloaded: {total_downloaded} files")
    print(f"  Skipped (existing): {total_skipped} files")


def main():
    parser = argparse.ArgumentParser(
        description="Download circuit-sparsity data from Azure blob storage"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./data",
        help="Local directory to store downloaded data (default: ./data)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed progress information"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Overwrite existing files"
    )
    parser.add_argument(
        "--models-only",
        action="store_true",
        help="Only download model files (models/ directory)"
    )
    parser.add_argument(
        "--viz-only",
        action="store_true",
        help="Only download visualization data (viz/ directory)"
    )
    parser.add_argument(
        "--train-curves-only",
        action="store_true",
        help="Only download training curves (train_curves/ directory)"
    )

    args = parser.parse_args()

    # Determine which subdirectories to download
    subdirs = []
    if args.models_only:
        subdirs = ["models"]
    elif args.viz_only:
        subdirs = ["viz"]
    elif args.train_curves_only:
        subdirs = ["train_curves"]
    else:
        subdirs = ["models", "viz", "train_curves"]

    # Create output directory
    output_dir = os.path.expanduser(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    if args.verbose:
        print(f"Downloading to: {output_dir}")
        print(f"Directories to download: {', '.join(subdirs)}")

    blob_base = "https://openaipublic.blob.core.windows.net/circuit-sparsity"

    try:
        download_directory_structure(
            blob_base=blob_base,
            local_base=output_dir,
            subdirs=subdirs,
            verbose=args.verbose,
            force=args.force,
        )

        # Update registries to point to local data
        if args.verbose:
            print(f"\nTo use downloaded data, update registries.py:")
            print(f"  Change: MODEL_BASE_DIR = \"https://openaipublic.blob.core.windows.net/circuit-sparsity\"")
            print(f"  To:     MODEL_BASE_DIR = \"{output_dir}\"")

    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user.")
        print(f"Partial data saved to: {output_dir}")
        print("Run the script again to resume downloading.")
        sys.exit(1)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
