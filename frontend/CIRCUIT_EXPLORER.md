# Circuit Explorer - Beautiful Minimalist Circuit Visualization

A modern web-based interactive circuit visualization tool for exploring neural network circuits. Built with Next.js 16, TypeScript, Cytoscape.js, and Apache Arrow.

## Features

### Core Features
- **Interactive Circuit Graph** - Visualize circuit nodes and connections with:
  - Color-coded importance (blue → red gradient)
  - Node size scaled by importance
  - Edge thickness scaled by weight
  - Click to select neurons and inspect details
  - Pan and zoom controls

- **Node Inspector** - Detailed information panel showing:
  - Neuron location and index
  - Importance score
  - Connectivity metrics (incoming/outgoing edges)
  - Activation statistics

- **Sample Viewer** - Code examples showing:
  - Top activations (high neural activity)
  - Bottom activations (low neural activity)
  - Token-level activation heatmap
  - Quantile-based sample browsing

- **Loss Curves** - Visualization of:
  - Pruning optimization trajectory
  - Baseline vs final loss comparison
  - Loss improvement metrics

- **Circuit Statistics** - Overview dashboard with:
  - Circuit node count
  - Total connections
  - Global network metrics

### Interactive Controls
- **Dataset Selector** - Switch between available circuits
- **Edge Threshold Slider** - Filter weak connections dynamically
- **Node Selection** - Click nodes to inspect their properties
- **Responsive Layout** - Works on desktop and tablet

## Architecture

### Data Flow

```
Parquet Files (public/data/)
         ↓
[parquet-wasm + Apache Arrow]
         ↓
CircuitData TypeScript Objects
         ↓
React Components (Cytoscape, Recharts)
         ↓
Interactive Visualization
```

### Component Structure

```
page.tsx (Main Layout)
├── CircuitGraph.tsx          (Cytoscape visualization)
├── NodeDetails.tsx           (Side panel with node info)
├── SampleViewer.tsx          (Token activation examples)
└── LossCurve.tsx             (Loss curve chart)

Hooks:
├── useCircuitData.ts         (Parquet data loading)
└── useDatasets.ts            (Dataset enumeration)

Utilities:
└── lib/parquet-loader.ts     (Apache Arrow integration)
```

## Data Format

### Input: Parquet Files

The explorer loads circuit data from 6 parquet files per circuit:

1. **nodes.parquet** - Circuit neurons
   ```
   node_id, location, layer, component, subloc, neuron_idx, importance
   ```

2. **edges.parquet** - Connections between neurons
   ```
   edge_id, source_node_id, target_node_id, weight, src_location, tgt_location
   ```

3. **samples.parquet** - Activation examples
   ```
   sample_id, location, neuron_id, quantile, token_ids (JSON), activations (JSON)
   ```

4. **task_samples.parquet** - Task dataset samples
   ```
   doc_id, label, token_ids (JSON), length
   ```

5. **metadata.parquet** - Global circuit info
   ```
   baseline_loss, loss_after_pruning, num_total_nodes, loss_curve (JSON)
   ```

6. **layer_importance.parquet** - Per-layer metrics
   ```
   layer_name, importance_score, num_nodes
   ```

### Data Location

Data files should be placed in:
```
public/data/{model}/{task}/{sweep}/{k}/
├── nodes.parquet
├── edges.parquet
├── samples.parquet
├── task_samples.parquet
├── metadata.parquet
└── layer_importance.parquet
```

## Development

### Setup

```bash
npm install
npm run dev
```

Server runs on http://localhost:3000 (or next available port)

### Build for Production

```bash
npm run build
npm start
```

### Adding New Datasets

1. Place parquet files in `public/data/{model}/{task}/{sweep}/{k}/`
2. Update `hooks/useDatasets.ts` with new dataset entry:
   ```typescript
   {
     model: 'my_model',
     task: 'my_task',
     sweep: 'prune_v2',
     k: 64,
     path: '/data/my_model/my_task/prune_v2/64'
   }
   ```

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript 5
- **Graph Viz**: Cytoscape.js 3.33
- **Charts**: Recharts 3.5
- **Parquet Loading**: parquet-wasm 0.7 + Apache Arrow
- **Styling**: TailwindCSS 4
- **React**: React 19

## Key Libraries

### parquet-wasm + Apache Arrow
- Browser-native parquet parsing
- Zero-copy columnar data access
- Efficient memory usage for large circuits

### Cytoscape.js
- Fast, interactive graph visualization
- Customizable styling and layouts
- Touch-friendly pan/zoom

### Recharts
- Lightweight chart library
- Responsive canvas rendering
- Minimal configuration

## Performance Considerations

1. **Lazy Loading**: Parquet files loaded on-demand when dataset selected
2. **Edge Filtering**: Only render edges above threshold to avoid clutter
3. **Memoization**: Heavy computations memoized with `useMemo`
4. **WASM Initialization**: Parquet parsing happens in WebAssembly for speed

## File Structure

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Main explorer page
│   └── globals.css             # Global styles
├── components/
│   ├── CircuitGraph.tsx         # Cytoscape wrapper
│   ├── NodeDetails.tsx          # Node inspector panel
│   ├── SampleViewer.tsx         # Activation examples
│   └── LossCurve.tsx            # Loss visualization
├── hooks/
│   ├── useCircuitData.ts        # Parquet loading hook
│   └── useDatasets.ts           # Dataset enumeration
├── lib/
│   ├── types.ts                 # TypeScript interfaces
│   └── parquet-loader.ts        # Apache Arrow integration
└── public/
    └── data/                    # Parquet files (by path above)
```

## Styling

The explorer uses a minimalist design with:
- Clean white cards with subtle shadows
- Blue accent colors (#3b82f6)
- Gray color palette for neutral elements
- Responsive grid layouts
- Smooth transitions and hover states

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Requires WebAssembly support

## Future Enhancements

- [ ] Attention head pattern visualization
- [ ] Multi-circuit comparison view
- [ ] Circuit export (JSON/CSV)
- [ ] Search by neuron function (NLP)
- [ ] Custom colormap selection
- [ ] Dark mode theme
- [ ] Layer-specific filtering
- [ ] Edge weight statistics

## Troubleshooting

### "Failed to fetch" errors
- Ensure parquet files exist in `public/data/`
- Check file paths in `useDatasets.ts`
- Verify CORS headers if loading from remote storage

### Graph not rendering
- Check browser console for WebAssembly errors
- Ensure Cytoscape CSS is loaded
- Verify nodes/edges have non-zero counts

### Slow loading
- Large sample.parquet files (~600KB) take time to parse
- Consider reducing sample count in conversion script
- Use edge threshold to reduce rendered connections

## License

MIT / Apache 2.0 (inherited from dependencies)
