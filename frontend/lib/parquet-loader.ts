import initWasm, { readParquet } from 'parquet-wasm/esm';
import { tableFromIPC } from 'apache-arrow';
import {
  CircuitNode,
  CircuitEdge,
  Sample,
  TaskSample,
  Metadata,
  LayerImportance,
  CircuitData,
} from './types';

let wasmInitialized = false;

async function ensureWasmInit() {
  if (!wasmInitialized) {
    await initWasm();
    wasmInitialized = true;
  }
}

async function fetchParquetAsBuffer(path: string): Promise<ArrayBuffer> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to fetch ${path}: ${response.statusText}`);
  }
  return response.arrayBuffer();
}

async function parseParquetFile<T extends Record<string, any>>(path: string): Promise<T[]> {
  await ensureWasmInit();

  const buffer = await fetchParquetAsBuffer(path);
  const uint8Array = new Uint8Array(buffer);

  const wasmTable = readParquet(uint8Array);
  const ipcStream = wasmTable.intoIPCStream();
  const table = tableFromIPC(ipcStream);

  const rows: T[] = [];
  const numRows = typeof table.numRows === 'number' ? table.numRows : (table.numRows as any).toNumber();

  for (let i = 0; i < numRows; i++) {
    const row: Record<string, any> = {};
    for (const field of table.schema.fields) {
      const column = table.getChild(field.name);
      if (column) {
        row[field.name] = column.get(i);
      }
    }
    rows.push(row as T);
  }

  return rows;
}

export async function loadNodes(basePath: string): Promise<CircuitNode[]> {
  return parseParquetFile<CircuitNode>(`${basePath}/nodes.parquet`);
}

export async function loadEdges(basePath: string): Promise<CircuitEdge[]> {
  return parseParquetFile<CircuitEdge>(`${basePath}/edges.parquet`);
}

export async function loadSamples(basePath: string): Promise<Sample[]> {
  return parseParquetFile<Sample>(`${basePath}/samples.parquet`);
}

export async function loadTaskSamples(basePath: string): Promise<TaskSample[]> {
  return parseParquetFile<TaskSample>(`${basePath}/task_samples.parquet`);
}

export async function loadMetadata(basePath: string): Promise<Metadata> {
  const rows = await parseParquetFile<Metadata>(`${basePath}/metadata.parquet`);
  return rows[0];
}

export async function loadLayerImportance(basePath: string): Promise<LayerImportance[]> {
  return parseParquetFile<LayerImportance>(`${basePath}/layer_importance.parquet`);
}

export async function loadCircuitData(basePath: string): Promise<CircuitData> {
  const [nodes, edges, samples, taskSamples, metadata, layerImportance] = await Promise.all([
    loadNodes(basePath),
    loadEdges(basePath),
    loadSamples(basePath),
    loadTaskSamples(basePath),
    loadMetadata(basePath),
    loadLayerImportance(basePath),
  ]);

  return {
    nodes,
    edges,
    samples,
    taskSamples,
    metadata,
    layerImportance,
  };
}
