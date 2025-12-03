import torch
import os
import numpy as np
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

# Counter for unique file naming (for external arrays/tensors)
_file_counter = 0

def _get_next_filename(prefix: str) -> str:
    """Generate unique filename for external data files."""
    global _file_counter
    _file_counter += 1
    return f"{prefix}_{_file_counter:05d}"


def serialize_viz_data_to_json(viz_path: str, out_dir: str = "viz_export", inline_limit: int = 1000) -> dict:
    """
    Serialize viz_data.pt to JSON-compatible format with external storage for large arrays.

    Args:
        viz_path: Path to viz_data.pt file
        out_dir: Output directory for JSON and external files
        inline_limit: Max elements to inline in JSON (larger arrays go to .npy files)

    Returns:
        Dictionary representation suitable for JSON + manifest

    Data structure:
    - tensors/arrays > inline_limit: saved as .npy files, referenced in manifest
    - tensors/arrays <= inline_limit: converted to lists and inlined in JSON
    - scalar types (int, float, str, bool): directly in JSON
    - GPTConfig objects: converted to dict via asdict()
    - Other objects: best-effort serialization with type hints
    """

    viz_data = torch.load(viz_path, map_location="cpu", weights_only=False)
    os.makedirs(out_dir, exist_ok=True)

    def serialize_item(obj: Any, path_hint: str = "") -> Any:
        """
        Recursively serialize objects to JSON-compatible format.

        For large arrays/tensors:
          - Save to out_dir/{path_hint}_XXXXX.npy
          - Return reference dict with type info

        For small arrays:
          - Convert to nested lists/dicts
          - Keep in JSON
        """

        # TORCH TENSOR
        if isinstance(obj, torch.Tensor):
            arr = obj.detach().cpu().numpy()
            size = arr.size

            if size > inline_limit:
                # Save to external file
                fname = _get_next_filename(path_hint or "tensor")
                filepath = os.path.join(out_dir, f"{fname}.npy")
                np.save(filepath, arr)
                return {
                    "__type__": "tensor",
                    "file": f"{fname}.npy",
                    "shape": list(arr.shape),
                    "dtype": str(arr.dtype),
                }
            else:
                # Inline small tensors as nested lists
                return {
                    "__type__": "tensor_inline",
                    "data": arr.tolist(),
                    "shape": list(arr.shape),
                    "dtype": str(arr.dtype),
                }

        # NUMPY ARRAY
        elif isinstance(obj, np.ndarray):
            size = obj.size

            if size > inline_limit:
                # Save to external file
                fname = _get_next_filename(path_hint or "ndarray")
                filepath = os.path.join(out_dir, f"{fname}.npy")
                np.save(filepath, obj)
                return {
                    "__type__": "ndarray",
                    "file": f"{fname}.npy",
                    "shape": list(obj.shape),
                    "dtype": str(obj.dtype),
                }
            else:
                # Inline small arrays
                return {
                    "__type__": "ndarray_inline",
                    "data": obj.tolist(),
                    "shape": list(obj.shape),
                    "dtype": str(obj.dtype),
                }

        # DICT
        elif isinstance(obj, dict):
            return {
                k: serialize_item(v, f"{path_hint}_{k}" if path_hint else str(k))
                for k, v in obj.items()
            }

        # LIST
        elif isinstance(obj, list):
            return [
                serialize_item(v, f"{path_hint}_{i}" if path_hint else str(i))
                for i, v in enumerate(obj)
            ]

        # TUPLE -> list (JSON doesn't support tuples)
        elif isinstance(obj, tuple):
            return {
                "__type__": "tuple",
                "items": [
                    serialize_item(v, f"{path_hint}_t{i}" if path_hint else f"t{i}")
                    for i, v in enumerate(obj)
                ]
            }

        # DATACLASS (like GPTConfig) -> dict
        elif hasattr(obj, "__dataclass_fields__"):
            try:
                return {
                    "__type__": obj.__class__.__name__,
                    "data": serialize_item(asdict(obj), path_hint)
                }
            except (TypeError, ValueError):
                # Fallback for non-standard dataclasses
                return {
                    "__type__": obj.__class__.__name__,
                    "repr": str(obj),
                }

        # SCALAR TYPES
        elif isinstance(obj, (int, float, bool, str)) or obj is None:
            return obj

        # JSON-serializable numpy scalars
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj) if isinstance(obj, np.floating) else int(obj)

        # Fallback for unknown types
        else:
            # Try to get a string representation
            type_name = type(obj).__name__
            try:
                return {
                    "__type__": type_name,
                    "repr": str(obj),
                }
            except Exception as e:
                return {
                    "__type__": type_name,
                    "error": f"Could not serialize: {e}",
                }

    # Serialize the entire viz_data structure
    serialized = serialize_item(viz_data, "viz_data")

    # Write manifest.json
    manifest_path = os.path.join(out_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(serialized, f, indent=2)

    return {
        "manifest_path": manifest_path,
        "output_dir": out_dir,
        "serialized": serialized,
    }


def load_viz_data_from_json(manifest_path: str, out_dir: str | None = None) -> dict:
    """
    Reconstruct viz_data from JSON manifest and external files.

    Args:
        manifest_path: Path to manifest.json
        out_dir: Directory containing .npy files (defaults to manifest's directory)

    Returns:
        Reconstructed viz_data dictionary
    """

    if out_dir is None:
        out_dir = os.path.dirname(manifest_path)

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    def deserialize_item(obj: Any) -> Any:
        """Recursively reconstruct objects from serialized form."""

        if isinstance(obj, dict):
            # Check for type marker
            type_marker = obj.get("__type__")

            if type_marker == "tensor":
                # Load from external .npy file
                filepath = os.path.join(out_dir, obj["file"])
                arr = np.load(filepath)
                return torch.from_numpy(arr)

            elif type_marker == "tensor_inline":
                # Reconstruct from inlined data
                arr = np.array(obj["data"], dtype=obj["dtype"])
                return torch.from_numpy(arr)

            elif type_marker == "ndarray":
                # Load from external .npy file
                filepath = os.path.join(out_dir, obj["file"])
                return np.load(filepath)

            elif type_marker == "ndarray_inline":
                # Reconstruct from inlined data
                return np.array(obj["data"], dtype=obj["dtype"])

            elif type_marker == "tuple":
                # Reconstruct tuple
                return tuple(deserialize_item(item) for item in obj["items"])

            elif type_marker and type_marker not in ["tensor", "ndarray"]:
                # Other typed objects - reconstruct data field if present
                if "data" in obj:
                    return deserialize_item(obj["data"])
                return obj

            else:
                # Regular dict - recurse
                return {
                    k: deserialize_item(v)
                    for k, v in obj.items()
                }

        elif isinstance(obj, list):
            return [deserialize_item(item) for item in obj]

        else:
            return obj

    return deserialize_item(manifest)


def export_viz_data(path: str, out_dir: str = "viz_export"):
    """
    Export viz_data from .pt to JSON + external files.

    Usage:
        export_viz_data("viz/viz_data.pt", "viz_export")

    This creates:
        - viz_export/manifest.json (main JSON with references)
        - viz_export/tensor_*.npy, ndarray_*.npy (large arrays)

    To reload:
        data = load_viz_data_from_json("viz_export/manifest.json")
    """
    result = serialize_viz_data_to_json(path, out_dir)
    print(f"Serialized viz_data to {result['output_dir']}")
    print(f"Manifest: {result['manifest_path']}")
    return result


# Example usage
if __name__ == "__main__":
    # Check if viz_data.pt exists before running
    if os.path.exists("viz/viz_data.pt"):
        export_viz_data("viz/viz_data.pt")
        print("\nTo reload the data:")
        print("  data = load_viz_data_from_json('viz_export/manifest.json')")
    else:
        print("viz/viz_data.pt not found. Update the path or run explore_data.py first.")
