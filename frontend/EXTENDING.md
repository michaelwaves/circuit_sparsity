# Extending the Circuit Explorer

This guide shows how to customize and extend the circuit explorer for your needs.

## Adding New Datasets

### 1. Generate Parquet Files

Use the conversion script from the parent repository:

```bash
cd ..
python scripts/pt_to_parquet.py \
  --input-file data/viz/csp_yolo2/single_double_quote/prune_v2/64/viz_data.pt \
  --output-dir frontend/public/data/csp_yolo2/single_double_quote/prune_v2/64/
```

Or batch convert:

```bash
python scripts/pt_to_parquet.py --input-dir data/viz
```

### 2. Register the Dataset

Edit `frontend/hooks/useDatasets.ts`:

```typescript
const AVAILABLE_DATASETS: Dataset[] = [
  // Existing datasets...
  {
    model: 'csp_yolo2',
    task: 'single_double_quote',
    sweep: 'prune_v2',
    k: 64,
    path: '/data/csp_yolo2/single_double_quote/prune_v2/64',
  },
];
```

### 3. Test

1. Rebuild: `npm run build`
2. Refresh browser
3. New dataset appears in selector

No code changes needed - just data!

## Customizing the Visualization

### Change Node Colors

Edit `components/CircuitGraph.tsx`, `stylesheet` array:

```typescript
{
  selector: 'node',
  style: {
    'background-color': (ele: any) => {
      const importance = ele.data('importance');
      // Current: Blue (0%) to Red (100%)
      // Try: Green (0%) to Purple (100%)
      const hue = 270 + (1 - importance) * 120;
      return `hsl(${hue}, 70%, 50%)`;
    },
  }
}
```

### Change Edge Colors

Edit `components/CircuitGraph.tsx`, `stylesheet` array:

```typescript
{
  selector: 'edge',
  style: {
    'line-color': (ele: any) =>
      ele.data('weight') > 0
        ? 'rgba(0, 255, 0, 0.4)'  // Green for positive
        : 'rgba(255, 0, 0, 0.4)',  // Red for negative
  }
}
```

### Change Node Size Scale

Edit `components/CircuitGraph.tsx`:

```typescript
width: (ele: any) => 15 + ele.data('importance') * 50,  // Bigger range
height: (ele: any) => 15 + ele.data('importance') * 50,
```

### Change Graph Layout

Edit `components/CircuitGraph.tsx`:

```typescript
// Current: Grid layout
const layout = {
  name: 'grid',
  rows: Math.ceil(Math.sqrt(nodes.length)),
};

// Alternative: Force-directed (requires cytoscape-cose)
// const layout = { name: 'cose' };

// Alternative: Hierarchical (requires cytoscape-dagre)
// const layout = { name: 'dagre' };
```

## Adding Custom Features

### Add a New Component

1. Create `components/MyComponent.tsx`:

```typescript
'use client';

import React from 'react';
import { CircuitData } from '@/lib/types';

interface MyComponentProps {
  data: CircuitData;
}

export function MyComponent({ data }: MyComponentProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* Your component */}
    </div>
  );
}
```

2. Import in `app/page.tsx`:

```typescript
import { MyComponent } from '@/components/MyComponent';
```

3. Add to layout:

```typescript
{data && (
  <div className="space-y-6">
    {/* existing components */}
    <MyComponent data={data} />
  </div>
)}
```

### Add Layer Importance Chart

Create `components/LayerImportanceChart.tsx`:

```typescript
'use client';

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { LayerImportance } from '@/lib/types';

interface LayerImportanceChartProps {
  layers: LayerImportance[];
}

export function LayerImportanceChart({ layers }: LayerImportanceChartProps) {
  return (
    <div className="w-full bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">Layer Importance</h3>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={layers}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="layer_name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="importance_score" fill="#3b82f6" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
```

Then use in `app/page.tsx`:

```typescript
import { LayerImportanceChart } from '@/components/LayerImportanceChart';

// In render:
{data && <LayerImportanceChart layers={data.layerImportance} />}
```

### Add Node Search

Create `hooks/useNodeSearch.ts`:

```typescript
'use client';

import { useState, useMemo } from 'react';
import { CircuitNode } from '@/lib/types';

export function useNodeSearch(nodes: CircuitNode[], query: string) {
  return useMemo(() => {
    if (!query.trim()) return nodes;

    const lower = query.toLowerCase();
    return nodes.filter(n =>
      n.location.toLowerCase().includes(lower) ||
      n.component.toLowerCase().includes(lower) ||
      n.subloc.toLowerCase().includes(lower) ||
      n.neuron_idx.toString().includes(query)
    );
  }, [nodes, query]);
}
```

Use in `app/page.tsx`:

```typescript
const [searchQuery, setSearchQuery] = useState('');
const filteredNodes = useNodeSearch(data.nodes, searchQuery);

// Add search input to header:
<input
  type="text"
  placeholder="Search neurons..."
  value={searchQuery}
  onChange={(e) => setSearchQuery(e.target.value)}
  className="px-3 py-2 rounded border border-gray-300"
/>

// Use filteredNodes in CircuitGraph:
<CircuitGraph nodes={filteredNodes} {...otherProps} />
```

## Styling Customization

### Change Color Scheme

Edit `app/layout.tsx` and component files:

```typescript
// Current: Blue (#3b82f6)
className="... focus:ring-2 focus:ring-blue-500"

// Change to: Purple
className="... focus:ring-2 focus:ring-purple-500"

// Change to: Green
className="... focus:ring-2 focus:ring-green-500"
```

### Add Dark Mode

Create `contexts/ThemeContext.tsx`:

```typescript
'use client';

import React, { createContext, useState } from 'react';

export const ThemeContext = createContext<{
  isDark: boolean;
  toggle: () => void;
}>({ isDark: false, toggle: () => {} });

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [isDark, setIsDark] = useState(false);

  return (
    <ThemeContext.Provider value={{ isDark, toggle: () => setIsDark(!isDark) }}>
      {children}
    </ThemeContext.Provider>
  );
}
```

Use in `app/layout.tsx`:

```typescript
<ThemeProvider>
  {children}
</ThemeProvider>
```

### Responsive Breakpoints

Edit components to adjust breakpoints:

```typescript
// Current:
<div className="grid grid-cols-1 lg:grid-cols-4 gap-6">

// More aggressive responsive:
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

// Mobile-first:
<div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
```

## Data Enhancements

### Filter Nodes by Importance

Create `hooks/useImportanceFilter.ts`:

```typescript
export function useImportanceFilter(nodes: CircuitNode[], minImportance: number) {
  return useMemo(() =>
    nodes.filter(n => n.importance >= minImportance),
    [nodes, minImportance]
  );
}
```

Add slider to UI:

```typescript
const [minImportance, setMinImportance] = useState(0);
const filteredNodes = useImportanceFilter(data.nodes, minImportance);

<input
  type="range"
  min="0"
  max="1"
  step="0.1"
  value={minImportance}
  onChange={(e) => setMinImportance(parseFloat(e.target.value))}
/>

<CircuitGraph nodes={filteredNodes} {...} />
```

### Add Edge Weight Statistics

In `app/page.tsx`, add to stats grid:

```typescript
const maxEdgeWeight = Math.max(...data.edges.map(e => Math.abs(e.weight)), 0);
const avgEdgeWeight = data.edges.reduce((sum, e) => sum + Math.abs(e.weight), 0) / data.edges.length;

<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
  <p className="text-xs text-gray-600 mb-1">Max Edge Weight</p>
  <p className="text-2xl font-bold text-gray-900">{maxEdgeWeight.toFixed(3)}</p>
</div>

<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
  <p className="text-xs text-gray-600 mb-1">Avg Edge Weight</p>
  <p className="text-2xl font-bold text-gray-900">{avgEdgeWeight.toFixed(3)}</p>
</div>
```

## Performance Optimization

### Lazy Load Samples

Instead of loading all samples, load on-demand:

```typescript
// In useCircuitData.ts
const [loadedSamples, setLoadedSamples] = useState(false);

const lazyLoadSamples = useCallback(async () => {
  if (loadedSamples) return;
  const samples = await loadSamples(basePath);
  // Use samples...
  setLoadedSamples(true);
}, [basePath, loadedSamples]);
```

### Memoize Expensive Computations

```typescript
const nodeImportanceStats = useMemo(() => {
  const importances = data.nodes.map(n => n.importance);
  return {
    min: Math.min(...importances),
    max: Math.max(...importances),
    avg: importances.reduce((a, b) => a + b, 0) / importances.length,
  };
}, [data.nodes]);
```

### Virtualize Long Lists

For large sample lists, use `react-window`:

```bash
npm install react-window
```

```typescript
import { VariableSizeList } from 'react-window';

// Render only visible samples
<VariableSizeList
  height={600}
  itemCount={samples.length}
  itemSize={() => 80}
>
  {({ index, style }) => (
    <div style={style}>
      {/* Render sample at index */}
    </div>
  )}
</VariableSizeList>
```

## Testing Enhancements

### Add Unit Tests

```bash
npm install --save-dev @testing-library/react vitest
```

Create `__tests__/CircuitGraph.test.tsx`:

```typescript
import { render } from '@testing-library/react';
import { CircuitGraph } from '@/components/CircuitGraph';

describe('CircuitGraph', () => {
  it('renders nodes', () => {
    const nodes = [{ node_id: 1, importance: 0.5, /* ... */ }];
    const { container } = render(
      <CircuitGraph nodes={nodes} edges={[]} selectedNodeId={null} onNodeSelect={() => {}} />
    );
    expect(container).toBeTruthy();
  });
});
```

### Add E2E Tests

```bash
npm install --save-dev playwright
```

Create `e2e/explorer.spec.ts`:

```typescript
import { test, expect } from '@playwright/test';

test('can select a node', async ({ page }) => {
  await page.goto('http://localhost:3000');
  await page.waitForSelector('[data-testid="circuit-graph"]');
  // Add test assertions
});
```

## Deployment Customizations

### Custom Domain

Add to `next.config.ts`:

```typescript
export default {
  // ...
  headers: async () => [
    {
      source: '/(.*)',
      headers: [
        { key: 'X-Content-Type-Options', value: 'nosniff' },
        { key: 'X-Frame-Options', value: 'DENY' },
      ],
    },
  ],
};
```

### Analytics Integration

Add to `app/layout.tsx`:

```typescript
<script
  async
  src="https://www.googletagmanager.com/gtag/js?id=GA_ID"
></script>
<script>
  {`
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'GA_ID');
  `}
</script>
```

## Documentation Customization

Update markdown files with your info:

- **CIRCUIT_EXPLORER.md** - Architecture reference
- **QUICKSTART.md** - Getting started guide
- **README.md** (in parent) - Project overview

## Getting Help

Useful resources:
- [Next.js Docs](https://nextjs.org/docs)
- [React Docs](https://react.dev)
- [Cytoscape.js Docs](https://js.cytoscape.org)
- [Recharts Docs](https://recharts.org)
- [TailwindCSS Docs](https://tailwindcss.com/docs)
- [TypeScript Docs](https://www.typescriptlang.org/docs)
