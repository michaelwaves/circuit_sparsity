'use client';

import React from 'react';
import { CircuitNode, CircuitEdge, Sample } from '@/lib/types';

interface NodeDetailsProps {
  node: CircuitNode | null;
  inEdges: CircuitEdge[];
  outEdges: CircuitEdge[];
  samples: Sample[];
}

export function NodeDetails({ node, inEdges, outEdges, samples }: NodeDetailsProps) {
  if (!node) {
    return (
      <div className="w-80 bg-white rounded-lg shadow-sm border border-gray-200 p-6 flex items-center justify-center h-full">
        <p className="text-gray-400 text-sm">Select a neuron to inspect</p>
      </div>
    );
  }

  const nodeSamples = samples.filter((s) => s.neuron_id === node.node_id);
  const topSamples = nodeSamples.filter((s) => s.quantile >= 0.5);
  const bottomSamples = nodeSamples.filter((s) => s.quantile < 0.5);

  return (
    <div className="w-80 bg-white rounded-lg shadow-sm border border-gray-200 p-6 overflow-y-auto h-full">
      <div className="space-y-6">
        {/* Node Info */}
        <div>
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Neuron</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Location:</span>
              <span className="font-mono text-gray-900">{node.location}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Index:</span>
              <span className="font-mono text-gray-900">{node.neuron_idx}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Importance:</span>
              <span className="font-mono text-gray-900">
                {(node.importance * 100).toFixed(1)}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Component:</span>
              <span className="font-mono text-gray-900">{node.component}</span>
            </div>
          </div>
        </div>

        {/* Connectivity */}
        <div>
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Connectivity</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Incoming edges:</span>
              <span className="font-mono text-gray-900">{inEdges.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Outgoing edges:</span>
              <span className="font-mono text-gray-900">{outEdges.length}</span>
            </div>
          </div>
        </div>

        {/* Samples summary */}
        <div>
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Activation Examples</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Top 50% (high activity):</span>
              <span className="font-mono text-gray-900">{topSamples.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Bottom 50% (low activity):</span>
              <span className="font-mono text-gray-900">{bottomSamples.length}</span>
            </div>
          </div>
        </div>

        {/* Top activations preview */}
        {topSamples.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Top Activations</h3>
            <div className="space-y-2">
              {topSamples.slice(0, 2).map((sample, idx) => {
                let tokenIds: number[] = [];
                try {
                  tokenIds = JSON.parse(sample.token_ids);
                } catch (e) {
                  // Invalid JSON
                }
                return (
                  <div key={idx} className="bg-gray-50 rounded p-2 text-xs">
                    <div className="text-gray-500 mb-1">
                      Position: {sample.position} | Top {((1 - sample.quantile) * 100).toFixed(0)}%
                    </div>
                    <div className="font-mono text-gray-700">
                      [...{tokenIds.length > 0 ? tokenIds.length : '?'} tokens...]
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
