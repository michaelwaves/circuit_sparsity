export interface CircuitNode {
  node_id: number;
  location: string;
  layer: number;
  component: string;
  subloc: string;
  neuron_idx: number;
  importance: number;
}

export interface CircuitEdge {
  edge_id: number;
  source_node_id: number;
  target_node_id: number;
  weight: number;
  src_location: string;
  tgt_location: string;
}

export interface Sample {
  sample_id: number;
  location: string;
  neuron_id: number;
  quantile: number;
  token_ids: string;
  activations: string;
  position: number;
  sample_idx: number;
}

export interface TaskSample {
  doc_id: number;
  label?: string | number;
  token_ids: string;
  length: number;
}

export interface Metadata {
  baseline_loss: number;
  loss_after_pruning: number;
  num_total_nodes: number;
  loss_curve: string;
  model_config: string;
}

export interface LayerImportance {
  layer_name: string;
  importance_score: number;
  num_nodes: number;
}

export interface CircuitData {
  nodes: CircuitNode[];
  edges: CircuitEdge[];
  samples: Sample[];
  taskSamples: TaskSample[];
  metadata: Metadata;
  layerImportance: LayerImportance[];
}

export interface Dataset {
  model: string;
  task: string;
  sweep: string;
  k: number;
  path: string;
}
