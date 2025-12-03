import pandas as pd
import json

print("=== METADATA ===")
metadata = pd.read_parquet("/tmp/test_parquet/metadata.parquet")
print(metadata.to_string())
print(f"\nBaseline loss:{metadata['baseline_loss'].values[0]}")
print(f"Loss after pruning:{metadata['loss_after_pruning'].values[0]}")

print("\n=== NODES ===")
nodes = pd.read_parquet("/tmp/test_parquet/nodes.parquet")
print(f"Total nodes: {len(nodes)}")
print(nodes.head(10).to_string())
print(f"\nLayers: {nodes['layer'].unique()}")
print(f"Components:{nodes['component'].unique()}")

print("\n=== EDGES ===")
edges = pd.read_parquet("/tmp/test_parquet/edges.parquet")
print(f"Total edges: {len(edges)}")
print(edges.head(10).to_string())

print("\n=== SAMPLES ===")
samples = pd.read_parquet("/tmp/test_parquet/samples.parquet")
print(f"Total samples: {len(samples)}")
print(samples.head(5).to_string())
if len(samples) > 0:
    first_tokens = json.loads(samples['token_ids'].iloc[0])
    print(
        f"\nFirst sample tokens:{first_tokens[:10]}... (total{len(first_tokens)} tokens)")

print("\n=== TASK SAMPLES ===")
task_samples = pd.read_parquet("/tmp/test_parquet/task_samples.parquet")
print(f"Total task samples:{len(task_samples)}")
print(task_samples.head(10).to_string())

print("\n=== LAYER IMPORTANCE ===")
layer_imp = pd.read_parquet("/tmp/test_parquet/layer_importance.parquet")
print(layer_imp.to_string())
