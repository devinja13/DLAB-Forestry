import { useOptimizeStore, TreeType } from '../store/useOptimizeStore';
import { useJobPoller } from '../hooks/useJobPoller';
import LayerToggle from './LayerToggle';

const API_BASE = 'http://localhost:8000/api';

const TREE_TYPES: { id: TreeType; label: string; cost: string }[] = [
  { id: '3gal', label: '3-gallon', cost: '$8' },
  { id: '5gal', label: '5-gallon', cost: '$12' },
  { id: '10gal', label: '10-gallon', cost: '$20' },
];

// Houston bounding box (full city)
const HOUSTON_BBOX = {
  west: -95.789,
  south: 29.499,
  east: -94.990,
  north: 30.115,
};

const ControlPanel: React.FC = () => {
  const {
    budget,
    setBudget,
    allowedTreeTypes,
    toggleTreeType,
    jobStatus,
    jobId,
    setJobId,
    setError,
  } = useOptimizeStore();

  // Start polling whenever jobId is set
  useJobPoller();

  const isRunning = jobStatus === 'pending' || jobStatus === 'running';

  const handleSubmit = async () => {
    try {
      const res = await fetch(`${API_BASE}/optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          budget,
          tree_types: allowedTreeTypes,
          region: HOUSTON_BBOX,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const { job_id } = await res.json();
      setJobId(job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit job');
    }
  };

  const handleCancel = async () => {
    if (!jobId) return;
    await fetch(`${API_BASE}/job/${jobId}`, { method: 'DELETE' });
    useOptimizeStore.getState().reset();
  };

  return (
    <aside className="w-72 bg-white border-l border-slate-200 flex flex-col overflow-y-auto shrink-0 z-20">
      <div className="p-4 space-y-5">
        {/* Header */}
        <div>
          <h2 className="text-lg font-semibold text-slate-800">Optimization</h2>
          <p className="text-xs text-slate-500">Configure and run the Gurobi model</p>
        </div>

        {/* Budget */}
        <div className="space-y-1">
          <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Budget
          </label>
          <input
            type="number"
            value={budget}
            onChange={(e) => setBudget(Number(e.target.value))}
            disabled={isRunning}
            className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50"
          />
          <p className="text-xs text-slate-400">${budget.toLocaleString()}</p>
        </div>

        {/* Tree types */}
        <div className="space-y-2">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Tree types
          </p>
          <div className="space-y-2">
            {TREE_TYPES.map((t) => (
              <label key={t.id} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={allowedTreeTypes.includes(t.id)}
                  onChange={() => toggleTreeType(t.id)}
                  disabled={isRunning}
                  className="w-4 h-4 rounded accent-green-600"
                />
                <span className="text-sm text-slate-700 flex-1">{t.label}</span>
                <span className="text-xs text-slate-400">{t.cost}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Layer toggle (shown after result) */}
        {jobStatus === 'complete' && <LayerToggle />}

        {/* Submit / cancel */}
        <div>
          {!isRunning ? (
            <button
              onClick={handleSubmit}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg text-sm transition-colors"
            >
              Run optimization
            </button>
          ) : (
            <button
              onClick={handleCancel}
              className="w-full bg-red-100 hover:bg-red-200 text-red-700 font-semibold py-2 px-4 rounded-lg text-sm transition-colors"
            >
              Cancel
            </button>
          )}
        </div>

        {/* Error state */}
        {jobStatus === 'failed' && (
          <p className="text-xs text-red-600 bg-red-50 rounded p-2">
            {useOptimizeStore.getState().error ?? 'Optimization failed'}
          </p>
        )}
      </div>
    </aside>
  );
};

export default ControlPanel;
