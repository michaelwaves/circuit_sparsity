'use client';

import { useState, useMemo } from 'react';
import { useCircuitData } from '@/hooks/useCircuitData';
import { useDatasets } from '@/hooks/useDatasets';
import { CircuitGraph } from '@/components/CircuitGraph';
import { NodeDetails } from '@/components/NodeDetails';
import { SampleViewer } from '@/components/SampleViewer';
import { LossCurve } from '@/components/LossCurve';

export default function Home() {
  const { datasets, loading: datasetsLoading } = useDatasets();
  const [selectedDatasetIdx, setSelectedDatasetIdx] = useState(0);
  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null);
  const [edgeThreshold, setEdgeThreshold] = useState(0.05);

  const selectedDataset = datasets[selectedDatasetIdx];
  const dataPath = selectedDataset ? selectedDataset.path : null;
  const { data, loading, error } = useCircuitData(dataPath);

  // Get selected node details
  const selectedNode = useMemo(() => {
    if (!data || selectedNodeId === null) return null;
    return data.nodes.find((n) => n.node_id === selectedNodeId) || null;
  }, [data, selectedNodeId]);

  // Get edges connected to selected node
  const { inEdges, outEdges } = useMemo(() => {
    if (!data || !selectedNode) return { inEdges: [], outEdges: [] };
    return {
      inEdges: data.edges.filter((e) => e.target_node_id === selectedNodeId),
      outEdges: data.edges.filter((e) => e.source_node_id === selectedNodeId),
    };
  }, [data, selectedNodeId, selectedNode]);

  // Get samples for selected node
  const nodeSamples = useMemo(() => {
    if (!data || !selectedNode) return [];
    return data.samples.filter((s) => s.neuron_id === selectedNodeId);
  }, [data, selectedNodeId, selectedNode]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-40">
        <div className="max-w-full mx-auto px-6 py-4">
          <div className="flex items-center justify-between gap-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Circuit Explorer</h1>
              <p className="text-sm text-gray-500 mt-1">Interactive neural network circuit visualization</p>
            </div>

            {/* Dataset selector */}
            {!datasetsLoading && datasets.length > 0 && (
              <div className="flex items-center gap-4 bg-gray-50 rounded-lg p-4 border border-gray-200">
                <label className="text-sm font-medium text-gray-700">Dataset:</label>
                <select
                  value={selectedDatasetIdx}
                  onChange={(e) => {
                    setSelectedDatasetIdx(parseInt(e.target.value));
                    setSelectedNodeId(null);
                  }}
                  className="text-sm px-3 py-2 rounded border border-gray-300 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {datasets.map((ds, idx) => (
                    <option key={idx} value={idx}>
                      {ds.model} / {ds.task} / k={ds.k}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-full mx-auto px-6 py-6">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700">
              <strong>Error:</strong> {error}
            </p>
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mb-4"></div>
              <p className="text-gray-600">Loading circuit data...</p>
            </div>
          </div>
        )}

        {data && (
          <div className="space-y-6">
            {/* Graph and details row */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Circuit graph - 3 columns */}
              <div className="lg:col-span-3">
                <CircuitGraph
                  nodes={data.nodes}
                  edges={data.edges}
                  selectedNodeId={selectedNodeId}
                  onNodeSelect={setSelectedNodeId}
                  edgeThreshold={edgeThreshold}
                />
              </div>

              {/* Node details - 1 column */}
              <div>
                <NodeDetails
                  node={selectedNode}
                  inEdges={inEdges}
                  outEdges={outEdges}
                  samples={nodeSamples}
                />
              </div>
            </div>

            {/* Edge threshold slider */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <label className="block text-sm font-medium text-gray-900 mb-4">
                Edge strength threshold: {edgeThreshold.toFixed(3)}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={edgeThreshold}
                onChange={(e) => setEdgeThreshold(parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
              <p className="text-xs text-gray-500 mt-2">
                Showing {data.edges.filter((e) => Math.abs(e.weight) > edgeThreshold).length} of{' '}
                {data.edges.length} edges
              </p>
            </div>

            {/* Sample viewer - full width */}
            {selectedNode && (
              <SampleViewer
                samples={nodeSamples}
                taskSamples={data.taskSamples.map((ts) => ({
                  tokens: JSON.parse(ts.token_ids),
                  label: ts.label?.toString(),
                }))}
              />
            )}

            {/* Loss curve */}
            <LossCurve
              lossCurveJson={data.metadata.loss_curve}
              baselineLoss={data.metadata.baseline_loss}
              finalLoss={data.metadata.loss_after_pruning}
            />

            {/* Circuit stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <p className="text-xs text-gray-600 mb-1">Circuit Nodes</p>
                <p className="text-2xl font-bold text-gray-900">{data.nodes.length}</p>
              </div>
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <p className="text-xs text-gray-600 mb-1">Connections</p>
                <p className="text-2xl font-bold text-gray-900">{data.edges.length}</p>
              </div>
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <p className="text-xs text-gray-600 mb-1">Total Nodes</p>
                <p className="text-2xl font-bold text-gray-900">{data.metadata.num_total_nodes}</p>
              </div>
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <p className="text-xs text-gray-600 mb-1">Activation Samples</p>
                <p className="text-2xl font-bold text-gray-900">{data.samples.length}</p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
