import { CellResult } from '../store/useOptimizeStore';

interface Props {
  cell: CellResult;
}

const CellTooltip: React.FC<Props> = ({ cell }) => {
  return (
    <div className="absolute bottom-8 left-4 bg-white rounded-lg shadow-lg p-3 text-sm z-20 min-w-[180px] pointer-events-none">
      <p className="font-semibold text-slate-700 mb-2">Planted cell</p>
      <div className="space-y-1">
        <div className="flex justify-between gap-4">
          <span className="text-slate-500">3-gallon trees</span>
          <span className="font-medium">{cell.trees_3gal}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-slate-500">5-gallon trees</span>
          <span className="font-medium">{cell.trees_5gal}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-slate-500">10-gallon trees</span>
          <span className="font-medium">{cell.trees_10gal}</span>
        </div>
        <div className="border-t border-slate-100 mt-2 pt-2 space-y-1">
          <div className="flex justify-between gap-4">
            <span className="text-slate-500">Cooling delta</span>
            <span className="font-medium text-blue-600">
              &ndash;{cell.cooling_delta.toFixed(3)} &deg;C
            </span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-slate-500">Cell cost</span>
            <span className="font-medium">${cell.total_cost.toLocaleString()}</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-slate-500">Imperviousness</span>
            <span className="font-medium">{(cell.imperviousness * 100).toFixed(0)}%</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CellTooltip;
