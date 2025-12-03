'use client';

import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

interface LossCurveProps {
  lossCurveJson: string;
  baselineLoss: number;
  finalLoss: number;
  title?: string;
}

export function LossCurve({
  lossCurveJson,
  baselineLoss,
  finalLoss,
  title = 'Loss Curve',
}: LossCurveProps) {
  const chartData = useMemo(() => {
    try {
      const parsed = JSON.parse(lossCurveJson);
      // Assuming format is [[step, loss], ...]
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed.map((item: any, idx: number) => ({
          step: typeof item[0] === 'number' ? item[0] : idx,
          loss: item[1],
        }));
      }
    } catch (e) {
      console.error('Failed to parse loss curve:', e);
    }
    return [];
  }, [lossCurveJson]);

  if (chartData.length === 0) {
    return (
      <div className="w-full h-80 bg-white rounded-lg shadow-sm border border-gray-200 p-6 flex items-center justify-center">
        <p className="text-gray-400 text-sm">No loss curve data available</p>
      </div>
    );
  }

  return (
    <div className="w-full bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">{title}</h3>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="step"
            tick={{ fontSize: 12 }}
            stroke="#9ca3af"
          />
          <YAxis
            tick={{ fontSize: 12 }}
            stroke="#9ca3af"
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#f9fafb',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
            formatter={(value: number) => value.toFixed(4)}
          />
          <Legend wrapperStyle={{ paddingTop: '16px' }} />
          <Line
            type="monotone"
            dataKey="loss"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="mt-6 grid grid-cols-3 gap-4 text-sm">
        <div className="bg-gray-50 rounded p-3">
          <p className="text-gray-600">Baseline Loss</p>
          <p className="text-lg font-semibold text-gray-900">{baselineLoss.toFixed(4)}</p>
        </div>
        <div className="bg-gray-50 rounded p-3">
          <p className="text-gray-600">Final Loss</p>
          <p className="text-lg font-semibold text-gray-900">{finalLoss.toFixed(4)}</p>
        </div>
        <div className="bg-gray-50 rounded p-3">
          <p className="text-gray-600">Change</p>
          <p
            className={`text-lg font-semibold ${
              finalLoss < baselineLoss ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {(finalLoss - baselineLoss).toFixed(4)}
          </p>
        </div>
      </div>
    </div>
  );
}
