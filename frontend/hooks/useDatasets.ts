'use client';

import { useState, useEffect } from 'react';
import { Dataset } from '@/lib/types';

// Datasets are hardcoded based on directory structure
// In production, this would be fetched from an API
const AVAILABLE_DATASETS: Dataset[] = [
  {
    model: 'csp_yolo1',
    task: 'final_kwarg',
    sweep: 'prune_v2',
    k: 64,
    path: '/data/csp_yolo1/final_kwarg/prune_v2/64',
  },
  {
    model: 'csp_yolo1',
    task: 'final_kwarg',
    sweep: 'prune_v2',
    k: 256,
    path: '/data/csp_yolo1/final_kwarg/prune_v2/256',
  },
];

export function useDatasets() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate async data loading
    const timer = setTimeout(() => {
      setDatasets(AVAILABLE_DATASETS);
      setLoading(false);
    }, 100);

    return () => clearTimeout(timer);
  }, []);

  return { datasets, loading };
}
