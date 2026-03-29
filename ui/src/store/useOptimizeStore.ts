import { create } from 'zustand';

export type TreeType = '3gal' | '5gal' | '10gal';
export type LayerType = 'trees' | 'cooling';
export type JobStatus = 'idle' | 'pending' | 'running' | 'complete' | 'failed';

export interface CellResult {
  lng: number;
  lat: number;
  bbox: [number, number, number, number]; // [west, south, east, north]
  trees_3gal: number;
  trees_5gal: number;
  trees_10gal: number;
  total_trees: number;
  total_cost: number;
  cooling_delta: number;
  canopy_gain: number;
  imperviousness: number;
}

export interface OptimizeSummary {
  status: string;
  runtime_s: number;
  total_cells: number;
  total_trees: number;
  budget_used: number;
  budget_remaining: number;
  total_cooling_delta: number;
  trees_by_type: Record<string, number>;
}

export interface OptimizeResult {
  summary: OptimizeSummary;
  cells: CellResult[];
}

interface OptimizeStore {
  // Inputs
  budget: number;
  allowedTreeTypes: TreeType[];
  // Job state
  jobId: string | null;
  jobStatus: JobStatus;
  progress: number;
  error: string | null;
  // Result
  result: OptimizeResult | null;
  // Map
  visibleLayers: Set<LayerType>;
  hoveredCell: CellResult | null;
  // Actions
  setBudget: (b: number) => void;
  toggleTreeType: (t: TreeType) => void;
  setJobId: (id: string) => void;
  setJobStatus: (s: JobStatus) => void;
  setProgress: (p: number) => void;
  setResult: (r: OptimizeResult) => void;
  setError: (e: string) => void;
  toggleLayer: (l: LayerType) => void;
  setHoveredCell: (c: CellResult | null) => void;
  reset: () => void;
}

export const useOptimizeStore = create<OptimizeStore>((set) => ({
  budget: 1_000_000,
  allowedTreeTypes: ['3gal', '5gal', '10gal'],
  jobId: null,
  jobStatus: 'idle',
  progress: 0,
  error: null,
  result: null,
  visibleLayers: new Set<LayerType>(['trees', 'cooling']),
  hoveredCell: null,

  setBudget: (budget) => set({ budget }),

  toggleTreeType: (type) =>
    set((state) => {
      const types = new Set(state.allowedTreeTypes);
      if (types.has(type) && types.size > 1) {
        types.delete(type);
      } else {
        types.add(type);
      }
      return { allowedTreeTypes: Array.from(types) as TreeType[] };
    }),

  setJobId: (jobId) =>
    set({ jobId, jobStatus: 'pending', progress: 0, error: null, result: null }),
  setJobStatus: (jobStatus) => set({ jobStatus }),
  setProgress: (progress) => set({ progress }),
  setResult: (result) => set({ result, jobStatus: 'complete', progress: 100 }),
  setError: (error) => set({ error, jobStatus: 'failed' }),

  toggleLayer: (layer) =>
    set((state) => {
      const layers = new Set(state.visibleLayers);
      if (layers.has(layer)) {
        layers.delete(layer);
      } else {
        layers.add(layer);
      }
      return { visibleLayers: layers };
    }),

  setHoveredCell: (hoveredCell) => set({ hoveredCell }),
  reset: () =>
    set({ jobId: null, jobStatus: 'idle', progress: 0, error: null, result: null }),
}));
