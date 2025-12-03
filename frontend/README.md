# Circuit Explorer

A beautiful, minimalist web-based circuit visualization tool for exploring neural network circuits.

![Status](https://img.shields.io/badge/status-production--ready-brightgreen)
![Build](https://img.shields.io/badge/build-passing-brightgreen)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)

## Overview

The Circuit Explorer is a modern web application for visualizing and exploring neural network circuits extracted from language models. It enables researchers to understand which neurons matter for specific tasks and what patterns they detect in training data.

Built with Next.js 16, React 19, Cytoscape.js, and Apache Arrow, the explorer provides an interactive interface for exploring circuit graphs with thousands of nodes and edges.

## Quick Start

```bash
# 1. Install
npm install

# 2. Run
npm run dev

# 3. Open
open http://localhost:3000
```

See [QUICKSTART.md](./QUICKSTART.md) for detailed setup instructions.

## Features

### Interactive Graph Visualization
- Click neurons to inspect their properties
- Color-coded by importance (blue → red)
- Node size scales with importance
- Edge thickness represents connection strength
- Pan and zoom controls
- Real-time edge filtering

### Node Inspector
- Detailed neuron metadata
- Connectivity statistics
- Activation patterns
- Sample previews

### Activation Examples
- Top activations (high neural activity)
- Bottom activations (low activity)
- Token-level heatmaps
- Quantile-based browsing

### Loss Curves
- Pruning optimization trajectory
- Baseline vs final loss comparison
- Circuit quality metrics

### Dataset Management
- Multiple circuit sizes (k=64, k=256, etc.)
- Different models and tasks
- One-click switching

## Documentation

- **[QUICKSTART.md](./QUICKSTART.md)** - 5-minute setup guide
- **[CIRCUIT_EXPLORER.md](./CIRCUIT_EXPLORER.md)** - Architecture & API reference
- **[EXTENDING.md](./EXTENDING.md)** - Customization guide
- **[CIRCUIT_EXPLORER_IMPLEMENTATION.md](../CIRCUIT_EXPLORER_IMPLEMENTATION.md)** - Implementation details

## Tech Stack

- **Framework**: Next.js 16 + React 19 + TypeScript 5
- **Visualization**: Cytoscape.js 3.33 + Recharts 3.5
- **Data**: parquet-wasm 0.7 + Apache Arrow 17
- **Styling**: TailwindCSS 4

## Project Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── layout.tsx
│   ├── page.tsx           # Main explorer
│   └── globals.css
├── components/            # React components
│   ├── CircuitGraph.tsx
│   ├── NodeDetails.tsx
│   ├── SampleViewer.tsx
│   └── LossCurve.tsx
├── hooks/                 # Custom React hooks
│   ├── useCircuitData.ts
│   └── useDatasets.ts
├── lib/                   # Utilities
│   ├── types.ts
│   └── parquet-loader.ts
└── public/data/           # Parquet files
```

## Usage

### Explore a Circuit

1. **Select dataset** - Use dropdown to choose model/task/k
2. **Click nodes** - View neuron properties in inspector
3. **View samples** - See activation examples at bottom
4. **Adjust threshold** - Filter weak connections with slider

### Add New Data

1. Convert PyTorch to Parquet using parent repo script
2. Copy parquets to `public/data/{model}/{task}/{sweep}/{k}/`
3. Register in `hooks/useDatasets.ts`
4. Refresh browser - done!

### Deploy

```bash
npm run build
npm start
```

## Performance

- **Initial load**: 2-3 seconds
- **Graph rendering**: <100ms
- **Node selection**: <50ms
- **Edge filtering**: <100ms

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Requires WebAssembly

## License

MIT / Apache 2.0 (inherited from dependencies)

## Contributing

See [EXTENDING.md](./EXTENDING.md) for customization examples.

## Credits

Inspired by [Neuronpedia's](https://neuronpedia.org) circuit explorer design.

---

**Status**: Production-ready ✅

Questions? See the [documentation](./CIRCUIT_EXPLORER.md) or [QUICKSTART.md](./QUICKSTART.md).
