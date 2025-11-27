import blobfile as bf
from circuit_sparsity.registries import MODEL_BASE_DIR
from clone_data_locally import download_file
import torch

blob_path = f"{MODEL_BASE_DIR}/viz/csp_yolo2/bracket_counting_beeg/prune_v4/k_optim"
items = bf.listdir(blob_path)
for item in items:
    print(item)

download_file(blob_path=f"{blob_path}/viz_data.pt",
              local_path="./viz/viz_data.pt")


data = torch.load("viz/viz_data.pt")
print(type(data))
print(data.keys())
print(data["circuit_data"])
print(f"Total nodes: {data["num_total_nodes"]}")
