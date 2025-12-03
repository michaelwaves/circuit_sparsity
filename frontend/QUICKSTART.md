# Circuit Explorer - Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Verify Data
Parquet files should already be in `public/data/`:
```bash
ls public/data/csp_yolo1/final_kwarg/prune_v2/
```

You should see:
- `nodes.parquet`
- `edges.parquet`
- `samples.parquet`
- `task_samples.parquet`
- `metadata.parquet`
- `layer_importance.parquet`

### 3. Run Development Server
```bash
npm run dev
```

Open browser to **http://localhost:3000**

### 4. Explore!

**Left side**: Click nodes in the circuit graph to select them
**Right side**: Neuron details and statistics
**Bottom**: Activation examples and loss curves
**Slider**: Adjust edge threshold to show/hide weak connections

---

## What You Can Do

### Explore Circuit Structure
- **Click nodes** to see their properties
- **Zoom/pan** the graph to navigate
- **Adjust edge threshold** slider to focus on strong connections
- **View connectivity** - see how many neurons feed into/out of each node

### Understand Neuron Function
- **Top activations**: Examples where the neuron fires strongly
- **Bottom activations**: Examples where it barely fires
- **Token heatmap**: See which tokens activate the neuron
- **Importance score**: How much does this neuron contribute to the circuit?

### Monitor Circuit Quality
- **Loss curve**: How model performance changes as circuit size increases
- **Baseline loss**: Original model accuracy
- **Final loss**: Accuracy of pruned circuit
- **Statistics**: Total nodes, connections, samples

### Compare Datasets
- Use the **dataset selector** at the top to switch between different circuit sizes
- Same model/task, different circuit complexities (k=64 vs k=256)

---

## File Locations

### Source Code
```
frontend/
├── app/page.tsx              # Main explorer component
├── components/               # Visualization components
│   ├── CircuitGraph.tsx      # Graph visualization
│   ├── NodeDetails.tsx       # Node inspector
│   ├── SampleViewer.tsx      # Activation examples
│   └── LossCurve.tsx         # Loss chart
├── hooks/                    # Custom React hooks
│   ├── useCircuitData.ts     # Data loading
│   └── useDatasets.ts        # Dataset list
└── lib/                      # Utilities
    ├── types.ts              # TypeScript interfaces
    └── parquet-loader.ts     # Parquet parsing
```

### Data
```
public/data/
├── csp_yolo1/
│   ├── final_kwarg/
│   │   └── prune_v2/
│   │       ├── 64/
│   │       │   ├── nodes.parquet
│   │       │   ├── edges.parquet
│   │       │   ├── samples.parquet
│   │       │   ├── task_samples.parquet
│   │       │   ├── metadata.parquet
│   │       │   └── layer_importance.parquet
│   │       └── 256/
│   │           └── [same files]
│   └── [other tasks...]
└── [other models...]
```

---

## Adding More Data

### 1. Generate Parquet Files

Use the conversion script (in parent repo):
```bash
python scripts/pt_to_parquet.py \
  --input-dir data/viz \
  --output-dir frontend/public/data
```

### 2. Register Dataset

Edit `frontend/hooks/useDatasets.ts`:

```typescript
const AVAILABLE_DATASETS: Dataset[] = [
  // ... existing datasets
  {
    model: 'csp_yolo2',
    task: 'single_double_quote',
    sweep: 'prune_v2',
    k: 128,
    path: '/data/csp_yolo2/single_double_quote/prune_v2/128',
  },
];
```

### 3. Refresh Browser

No rebuild needed - new datasets appear in the selector immediately!

---

## Understanding the Visualization

### Circuit Graph

**Nodes** (circles):
- **Size** = importance (bigger = more important)
- **Color** = importance (blue = low, red = high)
- **Border** = selected node (click to select)

**Edges** (arrows):
- **Color** = direction (blue = positive influence, red = negative)
- **Thickness** = strength of connection
- **Threshold** = adjust slider to show only strong connections

### Node Details (Right Panel)

Shows when you click a node:
- Location in circuit (e.g., "0.mlp.post_act")
- Neuron index within that location
- Importance percentage (0-100%)
- Number of incoming/outgoing connections
- Sample statistics

### Activation Examples

**Top Activations**:
- Neurons fire strongly on these code examples
- Light blue background = high activation
- Shows position in document where activation occurs

**Bottom Activations**:
- Neurons barely respond to these examples
- Light red background = low activation
- Helps understand what the neuron avoids

**Token Heatmap**:
- Each token (ID number) colored by activation strength
- Hover to see exact activation value
- Helps identify which words trigger this neuron

---

## Keyboard Shortcuts

Currently supported:
- **Click** on node to select
- **Click** on empty space to deselect
- **Scroll** to zoom in/out
- **Drag** to pan the graph

(More shortcuts coming soon!)

---

## Troubleshooting

### "Loading circuit data..." never completes
- Check browser console (F12) for errors
- Verify parquet files exist in `public/data/`
- Check that file paths in `useDatasets.ts` are correct

### Graph appears but is too cluttered
- Adjust edge threshold slider to the right
- Start at 0.3 to see only strong connections
- Click nodes individually to inspect

### Can't click nodes
- Make sure the node is in the visible area
- Try zooming in on the graph first
- Check that node selection isn't showing undefined node

### Slow performance
- Reduce edge threshold to render fewer connections
- Close other browser tabs
- Try clearing browser cache (Cmd+Shift+R / Ctrl+Shift+R)

---

## Next Steps

### For Developers
- Read [CIRCUIT_EXPLORER.md](./CIRCUIT_EXPLORER.md) for architecture details
- Check `lib/types.ts` for data structure documentation
- Explore `components/` for visualization components

### For Researchers
- Hover over nodes to see layer/component names
- Use node inspector to track neuron importance across circuits
- Compare loss curves for circuits of different sizes
- Identify highly-connected "hub" neurons (many edges)

### Future Features
- Attention head visualization
- Multi-circuit comparison
- Export circuits as JSON/CSV
- Full-text search over activation patterns
- Dark mode theme

---

## Performance Tips

1. **Start with larger edge threshold** (0.1-0.3) to reduce visual clutter
2. **Increase threshold gradually** to explore weaker connections
3. **Use small datasets first** (k=64) before exploring large circuits (k=512+)
4. **Close DevTools** while exploring for better graph performance

---

## Support

For issues or questions:
1. Check browser console (F12 → Console tab)
2. Review error messages in the UI
3. See troubleshooting section above
4. Check [CIRCUIT_EXPLORER.md](./CIRCUIT_EXPLORER.md) for technical details
