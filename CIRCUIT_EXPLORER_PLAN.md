# Circuit Explorer - Next.js App Architecture Plan

## Overview
A modern web-based circuit visualization tool to replace the janky Streamlit app. Users can explore circuits (neural network sub-graphs), understand which neurons matter, and see what patterns they detect in training data.

---

## Part 1: Understanding Current Data Structure

### What is Circuit Data?

The viz_data.pt files contain complete circuit information:

```
viz_data = {
    # Which neurons/channels are in the circuit (boolean masks per location)
    "circuit_data": {
        "0.attn.act_in": Tensor[0],      # Empty for this layer
        "0.mlp.post_act": Tensor[64],    # 64 neurons selected
        "1.attn.q": Tensor[48],          # 48 attention heads
        ...
    },

    # Example activations showing what patterns these neurons detect
    "samples": {
        "0.attn.resid_delta": {
            455: {  # neuron ID
                0.001: [[token_ids], [activations], [position]],  # bottom 0.1%
                0.01: [...],   # bottom 1%
                0.1: [...],    # bottom 10%
                0.5: [...],    # bottom 50%
            },
            ...
        }
    },

    # Importance scores and model architecture
    "importances": {
        "ch_interv_losses": {...},      # Per-neuron importance scores
        "layer_interv_losses": {...},   # Per-layer importance
        "pair_data": [                  # Edge weight matrices
            [weights_matrix, src_indices, tgt_indices, (src_loc, tgt_loc)],
            ...
        ],
        "pair_data_connections": [...], # Same structure, different format
        "task_samples": (token_ids_tensor, label_dict),  # All task examples
        "beeg_model_config": GPTConfig, # Model architecture
    },

    "all_loss": [[step, loss], ...],   # Loss curve during pruning
    "num_total_nodes": 136192,         # Total params in circuit
}
```

### Data Characteristics

- **Circuit size**: ~60-256 nodes (depending on k parameter)
- **Total model neurons**: ~136k (but circuit is sparse)
- **Layers**: 12 transformer layers, each with attn + mlp
- **Tasks**: Simple coding (e.g., "predict quote type")
- **File size**: ~5-20MB per viz_data.pt

---

## Part 2: Core Data Structures for Next.js

### Parquet Schema Design

We need to convert PyTorch tensors → Parquet for efficient loading and querying.

#### 1. **nodes.parquet** - Circuit nodes (neurons/channels)
```
node_id: int (unique ID per location)
location: string (e.g. "0.mlp.post_act", "2.attn.v")
layer: int (0-11)
component: string (attn|mlp)
subloc: string (act_in|post_act|resid_delta|q|k|v|...)
neuron_idx: int (within that location)
importance: float (0-1, normalized)
num_inputs: int (how many neurons feed into this)
num_outputs: int (how many neurons this feeds into)
```

#### 2. **edges.parquet** - Connections between nodes
```
edge_id: int (unique)
source_node_id: int
target_node_id: int
weight: float (importance/strength, can be negative)
src_location: string
tgt_location: string
```

#### 3. **samples.parquet** - Code examples that activate neurons
```
sample_id: int (unique)
neuron_id: int (which neuron activated)
quantile: float (0.001, 0.01, 0.1, 0.5)
token_ids: string (JSON array, e.g. "[220, 15, 11, ...]")
activations: string (JSON array of floats)
position: int (which position in doc)
label: string|int (task label, e.g. "single_quote" | 0|1)
```

#### 4. **task_samples.parquet** - Task dataset examples
```
doc_id: int
label: string|int
token_ids: string (JSON array)
length: int
```

#### 5. **metadata.parquet** - Single row with global info
```
model_name: string (csp_yolo1)
dataset_name: string (single_double_quote)
sweep_name: string (prune_v2)
k: int (128, 256, etc.)
num_total_nodes: int
num_circuit_nodes: int
baseline_loss: float
loss_after_pruning: float
all_loss_curve: string (JSON)
model_config_json: string (full GPT config as JSON)
```

#### 6. **layer_importance.parquet** - Per-layer metrics
```
layer_id: int
layer_name: string (e.g. "1.mlp")
importance_score: float
num_nodes: int
num_edges: int
```

---

## Part 3: MVP Tech Stack

### Frontend (Next.js)
- **Next.js 14+** - React framework
- **D3.js** - Circuit graph visualization (force-directed or hierarchical layout)
  - Alternative: **Cytoscape.js** - simpler, better for large graphs
- **Plotly.js** - Loss curves, heatmaps
- **TailwindCSS** - Styling
- **Zustand** - Client state (selected node, layer filter, etc.)
- **TanStack Query** - Caching parquet data

### Backend (Python)
- **Conversion script** (`pt_to_parquet.py`)
  - Load viz_data.pt
  - Convert tensors → Parquet format
  - Run once per dataset

### Data Storage
- **Local**: Parquet files in `/public/data/` (for development)
- **Production**: Cloud storage (S3, GCS, or Azure Blob)

### Serialization
- Use **Apache Arrow** / **Parquet** format:
  - ✅ Columnar (efficient querying)
  - ✅ Browser-compatible with `arrow-js`
  - ✅ Smaller than JSON
  - ✅ No serialization loss (unlike JSON which loses precision on floats)
  - ✅ Can be streamed/chunked

---

## Part 4: Data Conversion Strategy

### Why not use PT directly?
- PyTorch tensors are not browser-compatible
- JSON loses float precision
- .pt files are large

### Conversion Pipeline

**Step 1: Create conversion script**
```python
# pt_to_parquet.py
import torch
import pandas as pd
from pathlib import Path

def convert_viz_data_to_parquet(viz_data_path: str, output_dir: str):
    viz_data = torch.load(viz_data_path)

    # 1. Create nodes.parquet from circuit_data
    nodes = []
    node_id = 0
    for location, tensor in viz_data['circuit_data'].items():
        for neuron_idx in range(len(tensor)):
            nodes.append({
                'node_id': node_id,
                'location': location,
                'neuron_idx': neuron_idx,
                'importance': float(tensor[neuron_idx]),
                ...
            })
            node_id += 1
    pd.DataFrame(nodes).to_parquet(f'{output_dir}/nodes.parquet')

    # 2. Create edges.parquet from pair_data + pair_data_connections
    edges = []
    for edge_weights, src_indices, tgt_indices, (src_loc, tgt_loc) in viz_data['importances']['pair_data_connections']:
        # Build sparse edge list
        ...
    pd.DataFrame(edges).to_parquet(f'{output_dir}/edges.parquet')

    # 3. Create samples.parquet from samples dict
    samples = []
    for location, neuron_dict in viz_data['samples'].items():
        for neuron_id, fracs_dict in neuron_dict.items():
            for frac, sample_list in fracs_dict.items():
                for doc, activations, pos in sample_list:
                    samples.append({
                        'neuron_id': int(neuron_id),
                        'quantile': frac,
                        'token_ids': json.dumps(doc.tolist()),
                        'activations': json.dumps(activations.tolist()),
                        'position': int(pos),
                    })
    pd.DataFrame(samples).to_parquet(f'{output_dir}/samples.parquet')

    # 4. Metadata & task samples similarly
```

**Step 2: Generate all parquets**
```bash
python pt_to_parquet.py \
  --input data/viz/csp_yolo1/single_double_quote/prune_v2/64/viz_data.pt \
  --output public/data/csp_yolo1/single_double_quote/prune_v2/64/
```

**Step 3: Deploy parquets**
- Check into git (if small) or upload to S3
- Serve from `/public/data/` in Next.js

---

## Part 5: Next.js App Structure

```
circuit-explorer/
├── public/
│   └── data/
│       └── csp_yolo1/single_double_quote/prune_v2/64/
│           ├── nodes.parquet
│           ├── edges.parquet
│           ├── samples.parquet
│           ├── task_samples.parquet
│           ├── metadata.parquet
│           └── layer_importance.parquet
├── src/
│   ├── app/
│   │   ├── page.tsx              # Main explorer
│   │   ├── layout.tsx
│   │   └── api/
│   │       └── datasets/          # List available datasets
│   ├── components/
│   │   ├── CircuitGraph.tsx       # D3/Cytoscape visualization
│   │   ├── NodeDetails.tsx        # Info panel for selected node
│   │   ├── SampleViewer.tsx       # Code samples with highlights
│   │   ├── LossPlot.tsx           # Pruning loss curve
│   │   └── Sidebar.tsx            # Model/dataset selectors
│   ├── hooks/
│   │   ├── useParquetData.ts      # Load & parse parquets
│   │   ├── useSelectedNode.ts     # Zustand store
│   │   └── useGraphLayout.ts      # D3 force simulation
│   ├── lib/
│   │   ├── parquet-loader.ts      # Arrow.js wrapper
│   │   ├── types.ts               # TypeScript definitions
│   │   └── utils.ts
│   └── styles/
│       └── globals.css
├── scripts/
│   ├── pt_to_parquet.py           # Conversion script
│   └── generate_test_data.py      # Mock data for dev
└── package.json
```

---

## Part 6: Key Features for MVP

### Must Have
1. **Dataset selector** - Choose model/task/k
2. **Circuit graph visualization** - Interactive D3/Cytoscape
   - Click nodes to select
   - Color by importance
   - Edge thickness by weight
   - Zoom/pan controls
3. **Node details panel** - Show when node clicked
   - Node ID, location, importance
   - Number of connections
4. **Code samples viewer**
   - Show top/bottom activations
   - Highlight activated tokens
   - Color intensity = activation strength
5. **Loss curve** - Pruning optimization trajectory

### Nice to Have (Phase 2)
- Edge strength threshold slider
- Filter by layer
- Attention head visualization (query→key patterns)
- Export circuit as JSON/CSV
- Side-by-side comparison of two circuits
- Search by neuron function (NLP on code samples)

---

## Part 7: Data Generation Questions & Answers

### Q: Do I have to generate my own circuit data?
**A:** No. You already have example data in `data/viz/csp_yolo1/single_double_quote/prune_v2/`. Use that to:
1. Write the conversion script (pt_to_parquet.py)
2. Generate initial parquets for the app
3. Verify the app works

Later, when you have new circuits from pruning, re-run the conversion script.

### Q: What should I use for libraries?
**A:** MVP recommendations:
- **Graph viz**: Cytoscape.js (simpler than D3, better for this use case)
  - Alternative: D3.js if you want fine-grained control
- **Parquet loading**: `arrow-js` (browser-compatible, Apache Arrow)
- **State**: Zustand (lightweight)
- **Styling**: TailwindCSS
- **HTTP**: TanStack Query + fetch

### Q: How do I convert PT to Parquet?
**A:** See Part 4 above. Use PyArrow/Pandas:
```bash
pip install pyarrow pandas torch
python scripts/pt_to_parquet.py \
  --input-dir data/viz/ \
  --output-dir public/data/
```

The script:
- Loads each viz_data.pt
- Converts tensors → CSV/Parquet
- Handles JSON serialization for lists
- Outputs ready-to-serve files

---

## Part 8: Implementation Roadmap (No Timelines)

1. **Conversion Layer**
   - Write `pt_to_parquet.py`
   - Test on 1 example dataset
   - Generate parquets to `/public/data/`

2. **Data Loading**
   - Create `useParquetData` hook with arrow-js
   - Fetch & parse metadata, nodes, edges, samples
   - Test in browser console

3. **Graph Visualization**
   - Set up Cytoscape.js canvas
   - Load nodes + edges from parquet
   - Implement click selection, zoom, pan
   - Color nodes by importance, size by degree

4. **UI Components**
   - Dataset selector sidebar
   - Selected node details panel
   - Code sample viewer with highlighting
   - Loss curve plot

5. **Integration**
   - Wire up selections to state
   - Cross-component communication
   - Performance optimization (lazy loading large edges)

6. **Polish**
   - Responsive design
   - Dark/light theme
   - Error handling
   - Loading states

---

## Part 9: Potential Gotchas

1. **Large edge lists**: If k=1024 and full connectivity, could have 1M edges
   - Solution: Client-side filtering, only show edges above threshold

2. **Float precision**: JSON loses precision on neural network activations
   - Solution: Use Parquet + Arrow (preserves float32/bfloat16)

3. **Task samples tokenization**: Need to decode token IDs back to strings
   - Solution: Store tokenizer name in metadata, use Tiktoken (already in viz.py)

4. **Attention head naming**: Heads are indexed differently (h0.ch0 vs flat index)
   - Solution: Store both in nodes.parquet, compute in conversion script

5. **Browser memory**: Parquets are columnar, but still need decompression
   - Solution: Paginate samples, lazy-load edges, use Web Workers

---

## Example Queries After Conversion

Once in Parquet + Arrow, you can easily query:
```typescript
// Get all neurons in layer 2
const layer2Nodes = arrow.filter(nodes, row => row.layer === 2)

// Get edges above importance threshold
const strongEdges = arrow.filter(edges, row => Math.abs(row.weight) > 0.1)

// Get samples activating neuron 42
const neuron42Samples = arrow.filter(samples, row => row.neuron_id === 42)
```

---

## Summary

| Aspect | Decision |
|--------|----------|
| **Data Format** | Parquet (Apache Arrow) |
| **Frontend Framework** | Next.js 14+ |
| **Graph Viz** | Cytoscape.js (or D3.js) |
| **State Management** | Zustand |
| **Data Querying** | Arrow.js |
| **Styling** | TailwindCSS |
| **Hosting** | Vercel (for Next.js) |
| **Data Location** | `/public/data/` (local) or S3 (prod) |

This design gives you:
- ✅ Fast, interactive exploration
- ✅ Easy to add new datasets (just re-run conversion)
- ✅ Scalable to larger circuits
- ✅ No backend required (static deployment)
- ✅ Better UX than current Streamlit app
