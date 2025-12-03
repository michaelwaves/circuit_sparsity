'use client';

import { useState, useEffect, useCallback } from 'react';
import { CircuitData } from '@/lib/types';
import { loadCircuitData } from '@/lib/parquet-loader';

export function useCircuitData(dataPath: string | null) {
  const [data, setData] = useState<CircuitData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!dataPath) {
      setData(null);
      setError(null);
      return;
    }

    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const circuitData = await loadCircuitData(dataPath);
        setData(circuitData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load circuit data');
        console.error('Error loading circuit data:', err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [dataPath]);

  return { data, loading, error };
}
