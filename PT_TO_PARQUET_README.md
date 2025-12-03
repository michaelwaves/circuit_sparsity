# PT to Parquet Conversion Script

Converts PyTorch `.pt` files to Apache Parquet format for web visualization in the Next.js circuit explorer.

## What It Does

The script transforms `viz_data.pt` files into 6 optimized Parquet tables:

1. **nodes.parquet** - Circuit nodes (neurons/channels)
   - 64 nodes from the example dataset
   - Fields: node_id, location, layer, component, subloc, neuron_idx, importance

2. **edges.parquet** - Connections between nodes
   - 46 edges from the example dataset
   - Fields: edge_id, source_node_id, target_node_id, weight, src_location, tgt_location

3. **samples.parquet** - Code examples activating neurons
   - 483 samples from the example dataset
   - Fields: sample_id, location, neuron_id, quantile, token_ids (JSON), activations (JSON), position, sample_idx

4. **task_samples.parquet** - Task dataset examples
   - 32 task samples from the example dataset
   - Fields: doc_id, label, token_ids (JSON), length

5. **metadata.parquet** - Global circuit information
   - Single row per circuit
   - Fields: baseline_loss, loss_after_pruning, num_total_nodes, loss_curve (JSON), model_config (JSON)

6. **layer_importance.parquet** - Per-layer importance metrics
   - 24 layers (12 attention + 12 MLP) from the example dataset
   - Fields: layer_name, importance_score, num_nodes

## Usage

### Convert a Single File

```bash
python scripts/pt_to_parquet.py \
  --input-file data/viz/csp_yolo1/single_double_quote/prune_v2/64/viz_data.pt \
  --output-dir data/viz_parquet/csp_yolo1/single_double_quote/prune_v2/64/
```

### Convert All Files in a Directory

```bash
python scripts/pt_to_parquet.py --input-dir data/viz
```

This will:
- Recursively find all `viz_data.pt` files in `data/viz/`
- Convert them to `data/viz_parquet/` with the same directory structure
- Skip the `viz` → `viz_parquet` replacement in paths

## File Sizes (Example: csp_yolo1/single_double_quote/prune_v2/64)

| File | Size |
|------|------|
| nodes.parquet | 5.7 KB |
| edges.parquet | 5.2 KB |
| samples.parquet | 654 KB |
| task_samples.parquet | 10 KB |
| metadata.parquet | 8.3 KB |
| layer_importance.parquet | 2.6 KB |
| **Total** | **~686 KB** |

## Data Structures

### nodes.parquet
```
node_id: int
location: str (e.g. "0.mlp.post_act")
layer: int (0-11, or -1 for "final_resid")
component: str ("attn", "mlp", "final")
subloc: str ("act_in", "post_act", "resid_delta", etc.)
neuron_idx: int (original neuron index)
importance: float (0-1, normalized)
```

### edges.parquet
```
edge_id: int
source_node_id: int (foreign key → nodes.node_id)
target_node_id: int (foreign key → nodes.node_id)
weight: float (can be negative)
src_location: str
tgt_location: str
```

### samples.parquet
```
sample_id: int
location: str
neuron_id: int
quantile: float (0.001, 0.01, 0.1, 0.5)
token_ids: str (JSON array of ints)
activations: str (JSON array of floats)
position: int (position in document)
sample_idx: int (sample index within quantile)
```

### task_samples.parquet
```
doc_id: int
label: optional (int or str)
token_ids: str (JSON array of ints)
length: int (number of tokens)
```

### metadata.parquet
```
baseline_loss: float
loss_after_pruning: float
num_total_nodes: int
loss_curve: str (JSON list of [step, loss] pairs)
model_config: str (JSON dict with model hyperparameters)
```

### layer_importance.parquet
```
layer_name: str (e.g. "0.mlp", "5.attn")
importance_score: float
num_nodes: int (nodes in this layer's circuit)
```

## Benefits Over PyTorch Format

- ✅ **Browser-compatible**: Can be loaded with `arrow-js` in Next.js
- ✅ **Columnar storage**: Efficient for filtering and aggregation
- ✅ **Float precision preserved**: bfloat16 and float32 tensors converted accurately
- ✅ **Smaller files**: Parquet compression reduces file sizes
- ✅ **No library dependencies**: Standard Apache Arrow format
- ✅ **JSON-serializable**: Token IDs and activations stored as JSON strings for easy parsing

## Requirements

```bash
pip install pyarrow pandas torch
```

## Notes

- Handles both `"final_resid"` special location and numbered layers (0.mlp, 0.attn, etc.)
- Robust to both nested tuple structures and list-of-tuples sample formats
- Automatically normalizes importance scores per location
- Preserves all edge connections (non-zero weights only)
- Skips empty tensors and nodes without samples

## Next Steps

Use these Parquet files in the Next.js circuit explorer:
1. Deploy to `/public/data/` directory
2. Load with `arrow-js` in the frontend
3. Query with client-side filtering (e.g., "get all edges above weight threshold")
4. Display in Cytoscape.js or D3.js graph visualization
