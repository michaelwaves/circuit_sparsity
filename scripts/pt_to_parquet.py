#!/usr/bin/env python3
"""
Convert viz_data.pt files to parquet format for web visualization.

Converts PyTorch tensors to efficient, browser-compatible Parquet tables.
Preserves float precision and enables efficient querying.

Usage:
    python scripts/pt_to_parquet.py --input-dir data/viz --output-dir data/viz_parquet
    python scripts/pt_to_parquet.py --input-file data/viz/csp_yolo1/single_double_quote/prune_v2/64/viz_data.pt
"""

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import torch


def tensor_to_json(t: torch.Tensor) -> str:
    """Convert tensor to JSON string, handling various dtypes."""
    if isinstance(t, torch.Tensor):
        return json.dumps(t.tolist())
    return json.dumps(t)


def convert_single_file(viz_data_path: str, output_dir: str) -> None:
    """
    Convert a single viz_data.pt file to parquet tables.

    Args:
        viz_data_path: Path to viz_data.pt
        output_dir: Directory to write parquet files
    """
    print(f"\n{'='*70}")
    print(f"Converting: {viz_data_path}")
    print(f"Output: {output_dir}")
    print('='*70)

    # Load data
    print("Loading viz_data.pt...")
    viz_data = torch.load(viz_data_path, weights_only=False, map_location='cpu')

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Extract metadata
    print("Processing metadata...")
    _save_metadata(viz_data, output_dir)

    # Extract nodes
    print("Processing nodes...")
    _save_nodes(viz_data, output_dir)

    # Extract edges
    print("Processing edges...")
    _save_edges(viz_data, output_dir)

    # Extract samples
    print("Processing samples...")
    _save_samples(viz_data, output_dir)

    # Extract task samples
    print("Processing task samples...")
    _save_task_samples(viz_data, output_dir)

    # Extract layer importance
    print("Processing layer importance...")
    _save_layer_importance(viz_data, output_dir)

    print(f"✓ Successfully converted to {output_dir}")


def _save_metadata(viz_data: Dict[str, Any], output_dir: str) -> None:
    """Save global metadata as parquet (single row)."""
    importances = viz_data["importances"]
    config = importances["beeg_model_config"]

    # Extract loss curve
    all_loss = viz_data.get("all_loss", [])
    loss_curve_json = json.dumps(
        [[float(step), float(loss)] for step, loss in all_loss]
    )

    # Serialize config (handle both object and dict)
    if isinstance(config, dict):
        config_dict = config
    else:
        config_dict = {
            "n_layer": config.n_layer,
            "d_model": config.d_model,
            "d_mlp": config.d_mlp,
            "n_head": config.n_head,
            "d_head": config.d_head,
            "tokenizer_name": getattr(config, "tokenizer_name", "gpt2"),
        }
    config_json = json.dumps(config_dict)

    metadata = pd.DataFrame(
        [
            {
                "baseline_loss": float(importances["loss"]),
                "loss_after_pruning": float(importances["interv_loss"]),
                "num_total_nodes": int(viz_data["num_total_nodes"]),
                "loss_curve": loss_curve_json,
                "model_config": config_json,
            }
        ]
    )

    metadata.to_parquet(os.path.join(output_dir, "metadata.parquet"))


def _save_nodes(viz_data: Dict[str, Any], output_dir: str) -> None:
    """Save circuit nodes as parquet."""
    circuit_data = viz_data["circuit_data"]
    importances = viz_data["importances"]
    ch_interv_losses = importances["ch_interv_losses"]

    # Compute node importance: normalize channel intervention losses per location
    node_importance_by_loc = {}
    for location, losses in ch_interv_losses.items():
        if isinstance(losses, torch.Tensor):
            losses_list = losses.tolist()
        else:
            losses_list = list(losses)

        if len(losses_list) > 0:
            max_loss = max(losses_list)
            if max_loss > 0:
                node_importance_by_loc[location] = [
                    float(l) / max_loss for l in losses_list
                ]
            else:
                node_importance_by_loc[location] = [0.0] * len(losses_list)
        else:
            node_importance_by_loc[location] = []

    nodes = []
    node_id = 0
    node_id_map = {}  # Maps (location, neuron_idx) -> node_id

    for location, neuron_indices_tensor in circuit_data.items():
        # neuron_indices_tensor contains the selected neuron indices
        if isinstance(neuron_indices_tensor, torch.Tensor):
            neuron_indices = neuron_indices_tensor.tolist()
        else:
            neuron_indices = list(neuron_indices_tensor)

        # Get location metadata
        parts = location.split(".")

        # Handle special case: "final_resid"
        if location == "final_resid":
            layer = -1
            component = "final"
            subloc = "resid"
        else:
            layer = int(parts[0])
            component = parts[1]  # "attn" or "mlp"
            # Determine sublocation
            if len(parts) > 2:
                subloc = parts[2]
            else:
                subloc = "unknown"

        # Get importance scores for this location
        importances_for_loc = node_importance_by_loc.get(location, [])

        for idx, neuron_idx in enumerate(neuron_indices):
            neuron_idx_int = int(neuron_idx) if isinstance(neuron_idx, torch.Tensor) else neuron_idx

            # Get importance (normalized)
            importance = (
                importances_for_loc[idx] if idx < len(importances_for_loc) else 0.0
            )

            node_id_map[(location, neuron_idx_int)] = node_id

            nodes.append(
                {
                    "node_id": node_id,
                    "location": location,
                    "layer": layer,
                    "component": component,
                    "subloc": subloc,
                    "neuron_idx": neuron_idx_int,
                    "importance": importance,
                }
            )
            node_id += 1

    nodes_df = pd.DataFrame(nodes)
    nodes_df.to_parquet(os.path.join(output_dir, "nodes.parquet"), index=False)

    # Save node ID mapping for edges processing
    with open(os.path.join(output_dir, "_node_id_map.json"), "w") as f:
        json.dump({f"{k[0]}:{k[1]}": v for k, v in node_id_map.items()}, f)


def _save_edges(viz_data: Dict[str, Any], output_dir: str) -> None:
    """Save circuit edges as parquet."""
    importances = viz_data["importances"]
    pair_data_connections = importances["pair_data_connections"]

    # Load node ID mapping
    with open(os.path.join(output_dir, "_node_id_map.json"), "r") as f:
        node_id_map_loaded = json.load(f)
        node_id_map = {
            tuple(k.split(":")): v
            for k, v in node_id_map_loaded.items()
        }
        node_id_map = {
            (k[0], int(k[1])): v for k, v in node_id_map.items()
        }

    edges = []
    edge_id = 0

    for edge_entry in pair_data_connections:
        if not isinstance(edge_entry, list) or len(edge_entry) < 4:
            continue

        edge_weights, src_indices, tgt_indices, (src_loc, tgt_loc) = edge_entry

        # Convert to numpy/list for easier handling
        if isinstance(edge_weights, torch.Tensor):
            weights_matrix = edge_weights.cpu().numpy()
        else:
            weights_matrix = np.array(edge_weights)

        if isinstance(src_indices, torch.Tensor):
            src_indices_list = src_indices.tolist()
        else:
            src_indices_list = list(src_indices)

        if isinstance(tgt_indices, torch.Tensor):
            tgt_indices_list = tgt_indices.tolist()
        else:
            tgt_indices_list = list(tgt_indices)

        # Handle bias term
        has_bias = src_indices_list and src_indices_list[-1] == "bias"
        if has_bias:
            src_indices_list = src_indices_list[:-1]

        # Create edges from weight matrix
        if weights_matrix.size == 0:
            continue

        if weights_matrix.ndim == 2:
            src_indices_arr, tgt_indices_arr = np.nonzero(weights_matrix)
            for i, j in zip(src_indices_arr, tgt_indices_arr):
                src_neuron = src_indices_list[i] if i < len(src_indices_list) else None
                tgt_neuron = tgt_indices_list[j] if j < len(tgt_indices_list) else None

                if src_neuron is None or tgt_neuron is None:
                    continue

                weight = float(weights_matrix[i, j])

                # Look up node IDs
                src_node_id = node_id_map.get((src_loc, src_neuron), None)
                tgt_node_id = node_id_map.get((tgt_loc, tgt_neuron), None)

                # Only include edges if both nodes are in circuit
                if src_node_id is not None and tgt_node_id is not None:
                    edges.append(
                        {
                            "edge_id": edge_id,
                            "source_node_id": src_node_id,
                            "target_node_id": tgt_node_id,
                            "weight": weight,
                            "src_location": src_loc,
                            "tgt_location": tgt_loc,
                        }
                    )
                    edge_id += 1

    edges_df = pd.DataFrame(edges)
    edges_df.to_parquet(os.path.join(output_dir, "edges.parquet"), index=False)

    # Clean up temporary mapping file
    os.remove(os.path.join(output_dir, "_node_id_map.json"))


def _save_samples(viz_data: Dict[str, Any], output_dir: str) -> None:
    """Save code samples as parquet."""
    samples_dict = viz_data["samples"]

    samples = []
    sample_id = 0

    for location, neuron_dict in samples_dict.items():
        for neuron_id, quantile_dict in neuron_dict.items():
            neuron_id_int = (
                int(neuron_id) if isinstance(neuron_id, torch.Tensor) else neuron_id
            )

            for quantile, sample_list in quantile_dict.items():
                # sample_list = ([list of samples], [list of more samples])
                # Each sample is a tuple of (token_ids_tensor, activations_tensor, position_tensor)
                all_sample_lists = sample_list if isinstance(sample_list, tuple) else [sample_list]

                for sample_source_list in all_sample_lists:
                    if not isinstance(sample_source_list, (list, tuple)):
                        continue

                    for sample_idx, sample_data in enumerate(sample_source_list):
                        if not isinstance(sample_data, (list, tuple)) or len(sample_data) < 2:
                            continue

                        token_ids = sample_data[0]
                        activations = sample_data[1]
                        position = sample_data[2] if len(sample_data) > 2 else 0

                        # Convert tensors to JSON-serializable format
                        if isinstance(token_ids, torch.Tensor):
                            token_ids_json = json.dumps(token_ids.tolist())
                        else:
                            token_ids_json = json.dumps(list(token_ids))

                        if isinstance(activations, torch.Tensor):
                            activations_json = json.dumps(activations.tolist())
                        else:
                            activations_json = json.dumps(list(activations))

                        position_int = (
                            int(position.item())
                            if isinstance(position, torch.Tensor)
                            else int(position)
                        )

                        samples.append(
                            {
                                "sample_id": sample_id,
                                "location": location,
                                "neuron_id": neuron_id_int,
                                "quantile": float(quantile),
                                "token_ids": token_ids_json,
                                "activations": activations_json,
                                "position": position_int,
                                "sample_idx": sample_idx,
                            }
                        )
                        sample_id += 1

    samples_df = pd.DataFrame(samples)
    samples_df.to_parquet(os.path.join(output_dir, "samples.parquet"), index=False)


def _save_task_samples(viz_data: Dict[str, Any], output_dir: str) -> None:
    """Save task dataset samples as parquet."""
    importances = viz_data["importances"]
    task_samples = importances["task_samples"]

    if not isinstance(task_samples, (list, tuple)) or len(task_samples) < 1:
        print("  Warning: task_samples not found or empty")
        return

    token_ids_tensor = task_samples[0]
    labels_dict = task_samples[1] if len(task_samples) > 1 else {}

    # Convert token IDs to list
    if isinstance(token_ids_tensor, torch.Tensor):
        all_token_ids = token_ids_tensor.tolist()
    else:
        all_token_ids = list(token_ids_tensor)

    task_samples_list = []

    for doc_idx, token_ids in enumerate(all_token_ids):
        # Get label for this doc
        label = labels_dict.get(doc_idx, None) if isinstance(labels_dict, dict) else None

        task_samples_list.append(
            {
                "doc_id": doc_idx,
                "label": label,
                "token_ids": json.dumps(token_ids),
                "length": len(token_ids),
            }
        )

    task_samples_df = pd.DataFrame(task_samples_list)
    task_samples_df.to_parquet(
        os.path.join(output_dir, "task_samples.parquet"), index=False
    )


def _save_layer_importance(viz_data: Dict[str, Any], output_dir: str) -> None:
    """Save per-layer importance metrics as parquet."""
    importances = viz_data["importances"]
    layer_interv_losses = importances.get("layer_interv_losses", {})
    circuit_data = viz_data["circuit_data"]

    layer_stats = []

    for layer_name, loss_value in layer_interv_losses.items():
        loss_float = float(loss_value) if isinstance(loss_value, torch.Tensor) else float(loss_value)

        # Count nodes in this layer
        num_nodes = sum(
            len(indices)
            for location, indices in circuit_data.items()
            if location.startswith(layer_name)
        )

        layer_stats.append(
            {
                "layer_name": layer_name,
                "importance_score": loss_float,
                "num_nodes": num_nodes,
            }
        )

    layer_df = pd.DataFrame(layer_stats)
    layer_df.to_parquet(
        os.path.join(output_dir, "layer_importance.parquet"), index=False
    )


def find_all_viz_data_files(input_dir: str) -> List[Tuple[str, str]]:
    """
    Recursively find all viz_data.pt files and compute output paths.

    Returns list of (input_path, output_dir) tuples.
    """
    results = []
    input_path = Path(input_dir)

    for viz_file in input_path.rglob("viz_data.pt"):
        # Compute relative path
        rel_path = viz_file.parent.relative_to(input_path)

        # Replace 'viz' with 'viz_parquet' in the path
        output_path = Path(input_dir.replace("/viz", "/viz_parquet")) / rel_path

        results.append((str(viz_file), str(output_path)))

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Convert viz_data.pt files to parquet format"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        help="Directory containing viz_data.pt files (will recurse)",
    )
    parser.add_argument(
        "--input-file",
        type=str,
        help="Single viz_data.pt file to convert",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory (only used with --input-file)",
    )

    args = parser.parse_args()

    if args.input_file:
        if not args.output_dir:
            print("Error: --output-dir required when using --input-file")
            return 1
        convert_single_file(args.input_file, args.output_dir)

    elif args.input_dir:
        files_to_convert = find_all_viz_data_files(args.input_dir)

        if not files_to_convert:
            print(f"No viz_data.pt files found in {args.input_dir}")
            return 1

        print(f"\nFound {len(files_to_convert)} viz_data.pt files")

        for input_path, output_path in files_to_convert:
            try:
                convert_single_file(input_path, output_path)
            except Exception as e:
                print(f"✗ Error converting {input_path}: {e}")
                import traceback
                traceback.print_exc()

        print(f"\n{'='*70}")
        print(f"✓ Conversion complete! All files saved to viz_parquet/")
        print('='*70)

    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
