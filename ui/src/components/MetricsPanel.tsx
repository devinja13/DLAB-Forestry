import { useOptimizeStore } from '../store/useOptimizeStore';

const MetricsPanel: React.FC = () => {
  const { result, jobStatus, progress } = useOptimizeStore();
  const s = result?.summary;

  if (jobStatus === 'pending' || jobStatus === 'running') {
    return (
      <div className="h-16 flex items-center justify-center gap-3 border-t border-slate-200 bg-white px-6">
        <div className="w-4 h-4 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm text-slate-600">
          {jobStatus === 'pending' ? 'Queued...' : `Optimizing · ${progress}%`}
        </span>
      </div>
    );
  }

  if (!s) {
    return (
      <div className="h-16 flex items-center justify-center border-t border-slate-200 bg-white">
        <span className="text-sm text-slate-400">Run an optimization to see results</span>
      </div>
    );
  }

  const metrics = [
    { label: 'Trees planted', value: s.total_trees.toLocaleString() },
    { label: 'Cells used', value: s.total_cells.toLocaleString() },
    { label: 'Budget used', value: `$${s.budget_used.toLocaleString()}` },
    { label: 'Budget remaining', value: `$${s.budget_remaining.toLocaleString()}` },
    { label: 'Total cooling', value: `\u2013${s.total_cooling_delta.toFixed(2)} \u00b0C` },
    { label: 'Solve time', value: `${s.runtime_s}s` },
  ];

  return (
    <div className="flex border-t border-slate-200 bg-white h-16 divide-x divide-slate-100">
      {metrics.map((m) => (
        <div key={m.label} className="flex-1 flex flex-col justify-center px-4">
          <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
            {m.label}
          </span>
          <span className="text-sm font-bold text-slate-800">{m.value}</span>
        </div>
      ))}
    </div>
  );
};

export default MetricsPanel;
