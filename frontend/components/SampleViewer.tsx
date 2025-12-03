'use client';

import React, { useState, useMemo } from 'react';
import { Sample } from '@/lib/types';

interface SampleViewerProps {
  samples: Sample[];
  taskSamples?: { tokens: number[]; label?: string }[];
}

export function SampleViewer({ samples, taskSamples = [] }: SampleViewerProps) {
  const [activeTab, setActiveTab] = useState<'top' | 'bottom'>('top');

  const { topSamples, bottomSamples } = useMemo(() => {
    return {
      topSamples: samples.filter((s) => s.quantile >= 0.5).slice(0, 5),
      bottomSamples: samples.filter((s) => s.quantile < 0.5).slice(0, 5),
    };
  }, [samples]);

  const displaySamples = activeTab === 'top' ? topSamples : bottomSamples;

  return (
    <div className="flex-1 bg-white rounded-lg shadow-sm border border-gray-200 p-6 overflow-y-auto">
      <div className="space-y-6">
        <div>
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Activation Examples</h3>

          {/* Tab switcher */}
          <div className="flex gap-2 mb-4 border-b border-gray-200">
            <button
              onClick={() => setActiveTab('top')}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition ${
                activeTab === 'top'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              Top Activations ({topSamples.length})
            </button>
            <button
              onClick={() => setActiveTab('bottom')}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition ${
                activeTab === 'bottom'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              Bottom Activations ({bottomSamples.length})
            </button>
          </div>

          {/* Samples */}
          <div className="space-y-3">
            {displaySamples.length === 0 ? (
              <p className="text-gray-400 text-sm">No samples available</p>
            ) : (
              displaySamples.map((sample, idx) => (
                <div key={idx} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-gray-500">
                      {activeTab === 'top' ? 'Top' : 'Bottom'} {idx + 1}
                    </span>
                    <span className="text-xs text-gray-400">
                      Position: {sample.position}
                    </span>
                  </div>
                  <SamplePreview sample={sample} activeTab={activeTab} />
                </div>
              ))
            )}
          </div>
        </div>

        {taskSamples.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Task Dataset Preview</h3>
            <div className="space-y-2 text-sm text-gray-600">
              <p>Total task samples: {taskSamples.length}</p>
              <p className="text-xs">Task samples show the distribution of data used for evaluation</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function SamplePreview({ sample, activeTab }: { sample: Sample; activeTab: 'top' | 'bottom' }) {
  let tokenIds: number[] = [];
  let activations: number[] = [];

  try {
    tokenIds = JSON.parse(sample.token_ids);
    activations = JSON.parse(sample.activations);
  } catch (e) {
    return <div className="text-gray-400 text-xs">Invalid sample data</div>;
  }

  if (tokenIds.length === 0) {
    return <div className="text-gray-400 text-xs">No token data</div>;
  }

  // Simple token visualization: show tokens with background color intensity based on activation
  const maxActivation = Math.max(...activations, 1);
  const minActivation = Math.min(...activations, 0);

  return (
    <div className="flex flex-wrap gap-1">
      {tokenIds.slice(0, 20).map((tokenId, idx) => {
        const activation = activations[idx] || 0;
        const normalized = (activation - minActivation) / (maxActivation - minActivation);
        const alpha = Math.max(0.1, Math.min(1, normalized));

        return (
          <span
            key={idx}
            className="px-2 py-1 text-xs rounded font-mono text-gray-900"
            style={{
              backgroundColor: activeTab === 'top'
                ? `rgba(59, 130, 246, ${alpha * 0.5})`
                : `rgba(239, 68, 68, ${alpha * 0.5})`,
            }}
            title={`Token ${tokenId}, activation: ${activation.toFixed(3)}`}
          >
            {tokenId}
          </span>
        );
      })}
      {tokenIds.length > 20 && (
        <span className="px-2 py-1 text-xs text-gray-500">+{tokenIds.length - 20} more</span>
      )}
    </div>
  );
}
