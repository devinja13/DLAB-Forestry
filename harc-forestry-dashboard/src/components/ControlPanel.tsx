import React, { useState } from 'react';
import { useScenarioStore, TREE_SPECS, TreeSize } from '../store/useScenarioStore';
import { RefreshCcw, DollarSign, Clock, Settings, Play } from 'lucide-react';

const ControlPanel: React.FC = () => {
    const {
        budget,
        initialBudget,
        allowedTreeTypes,
        isOptimizing,
        timeHorizon,
        setBudget,
        toggleAllowedTreeType,
        runOptimization,
        resetScenario,
        setTimeHorizon
    } = useScenarioStore();

    const [localBudget, setLocalBudget] = useState(initialBudget.toString());

    const handleBudgetSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const num = parseFloat(localBudget);
        if (!isNaN(num) && num > 0) {
            setBudget(num);
        }
    };

    return (
        <div className="flex flex-col h-full bg-white border-l border-slate-200 shadow-lg p-6 w-80 z-20 overflow-y-auto overflow-x-hidden">
            <div className="mb-6">
                <h2 className="text-xl font-semibold mb-1 text-slate-800">Scenario Controls</h2>
                <p className="text-xs text-slate-500 uppercase tracking-widest font-semibold">HARC Forestry Platform</p>
            </div>

            {/* Budget Configuration */}
            <div className="mb-8">
                <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center">
                    <DollarSign size={16} className="mr-1 text-planning-accent" />
                    Budget Configuration
                </h3>

                <form onSubmit={handleBudgetSubmit} className="mb-4">
                    <label className="block text-xs text-slate-500 mb-1">Total Allocation ($)</label>
                    <div className="flex">
                        <input
                            type="number"
                            value={localBudget}
                            onChange={(e) => setLocalBudget(e.target.value)}
                            className="flex-1 border border-slate-300 rounded-l-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-planning-accent focus:border-planning-accent"
                            placeholder="e.g. 100000"
                        />
                        <button
                            type="submit"
                            className="bg-planning-hover text-slate-700 font-medium px-4 border border-l-0 border-slate-300 rounded-r-md text-sm hover:bg-slate-100 transition-colors"
                        >
                            Set
                        </button>
                    </div>
                </form>

                <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
                    <div className="text-xs text-slate-500">Remaining Budget</div>
                    <div className={`text-2xl font-bold ${budget < 1000 ? 'text-rose-600' : 'text-slate-800'}`}>
                        ${budget.toLocaleString()}
                    </div>
                </div>
            </div>

            <hr className="border-slate-100 mb-8" />

            {/* Intervention Configuration */}
            <div className="mb-8">
                <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center">
                    <Settings size={16} className="mr-1 text-slate-500" />
                    Model Constraints
                </h3>

                <div className="mb-5">
                    <label className="block text-xs text-slate-500 mb-2">Allowed Tree Types</label>
                    <div className="grid grid-cols-1 gap-2">
                        {(['Small', 'Medium', 'Large'] as TreeSize[]).map((type) => {
                            const isSelected = allowedTreeTypes.includes(type);
                            const spec = TREE_SPECS[type];
                            return (
                                <label
                                    key={type}
                                    className={`flex items-center justify-between p-3 rounded-md border cursor-pointer transition-all ${isSelected
                                        ? 'bg-planning-hover border-planning-accent'
                                        : 'bg-white border-slate-200 hover:border-slate-300'
                                        } ${isOptimizing ? 'opacity-50 cursor-not-allowed' : ''}`}
                                >
                                    <div className="flex items-center">
                                        <input
                                            type="checkbox"
                                            className="w-4 h-4 text-planning-accent bg-gray-100 border-gray-300 rounded focus:ring-planning-accent mr-3 cursor-pointer"
                                            checked={isSelected}
                                            onChange={() => toggleAllowedTreeType(type)}
                                            disabled={isOptimizing}
                                        />
                                        <span className="text-sm font-medium text-slate-700">{type} Tree</span>
                                    </div>
                                    <span className="text-xs text-slate-500">${spec.cost} ea</span>
                                </label>
                            );
                        })}
                    </div>
                </div>

                <div className="mt-6 pt-2">
                    <button
                        onClick={runOptimization}
                        disabled={isOptimizing}
                        className={`w-full flex items-center justify-center py-3 px-4 rounded-md text-sm font-semibold text-white shadow-md transition-all ${isOptimizing
                            ? 'bg-slate-400 cursor-not-allowed animate-pulse'
                            : 'bg-planning-accent hover:bg-slate-700 hover:shadow-lg focus:ring-2 focus:ring-offset-2 focus:ring-planning-accent'
                            }`}
                    >
                        {isOptimizing ? (
                            <>
                                <RefreshCcw size={16} className="mr-2 animate-spin" /> Computing Optimal Scenario...
                            </>
                        ) : (
                            <>
                                <Play size={16} className="mr-2 fill-current" /> Run Optimization Model
                            </>
                        )}
                    </button>
                    <p className="text-[10px] text-slate-400 text-center mt-2 px-4 leading-tight">
                        This simulates passing parameters to the backend Python model to place maximum trees within constraints.
                    </p>
                </div>
            </div>

            <hr className="border-slate-100 mb-8" />

            {/* Time Horizon Slider */}
            <div className="mb-auto">
                <h3 className="text-sm font-semibold text-slate-700 mb-1 flex items-center">
                    <Clock size={16} className="mr-1 text-indigo-500" />
                    Time Horizon
                </h3>
                <div className="flex justify-between items-center mb-2">
                    <span className="text-xs text-slate-500">Year {timeHorizon}</span>
                    <span className="text-xs font-semibold text-indigo-700">Projected Impact</span>
                </div>
                <input
                    type="range"
                    min="0"
                    max="20"
                    value={timeHorizon}
                    onChange={(e) => setTimeHorizon(parseInt(e.target.value))}
                    className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-planning-accent"
                />
                <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                    <span>Present</span>
                    <span>+10yrs</span>
                    <span>+20yrs</span>
                </div>
            </div>

            {/* Reset */}
            <div className="mt-8 pt-4 border-t border-slate-100">
                <button
                    onClick={resetScenario}
                    className="w-full flex items-center justify-center py-2 px-4 text-sm text-red-600 hover:bg-red-50 rounded-md transition-colors"
                >
                    <RefreshCcw size={14} className="mr-2" />
                    Reset Scenario
                </button>
            </div>
        </div>
    );
};

export default ControlPanel;
