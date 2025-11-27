from safetensors.torch import save_file
import torch
import os
import numpy as np
import json
state_dict = torch.load("viz/viz_data.pt")


def export_viz_data(path, out_dir="viz_export"):
    viz = torch.load(path, map_location="cpu")

    os.makedirs(out_dir, exist_ok=True)
    manifest = {}

    def save_item(name, obj):
        # TENSOR
        if isinstance(obj, torch.Tensor):
            arr = obj.numpy()
            np.save(f"{out_dir}/{name}.npy", arr)
            return {"type": "tensor", "file": f"{name}.npy", "shape": arr.shape}

        # LIST
        if isinstance(obj, list):
            return [save_item(f"{name}_{i}", v) for i, v in enumerate(obj)]

        # DICT
        if isinstance(obj, dict):
            return {k: save_item(f"{name}_{k}", v) for k, v in obj.items()}

        # Scalar JSON types
        if isinstance(obj, (int, float, bool, str)) or obj is None:
            return obj

        if isinstance(obj, tuple):
            tup_list = list(obj)
            return {
                "type": "tuple",
                "items": [save_item(f"{name}_t{i}", v) for i, v in enumerate(tup_list)]
            }

        # numpy array
        if isinstance(obj, np.ndarray):
            np.save(f"{out_dir}/{name}.npy", obj)
            return {"type": "ndarray", "file": f"{name}.npy", "shape": obj.shape}

        raise TypeError(f"Unsupported type: {type(obj)} at key {name}")

    manifest = save_item("viz_data", viz)
    json.dump(manifest, open(f"{out_dir}/manifest.json", "w"))


export_viz_data("viz/viz_data.pt")
