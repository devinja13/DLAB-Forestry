import React, { useMemo } from 'react';
import { useScenarioStore } from '../store/useScenarioStore';
import { calculateMetrics, generateTimeSeriesData, generateAllocationData } from '../utils/heatSimulation';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
    BarChart, Bar, Cell
} from 'recharts';
import { Trees, ThermometerSun, Map as MapIcon, Wallet } from 'lucide-react';

const COLORS = ['#0ea5e9', '#3b82f6', '#1d4ed8'];

const MetricsPanel: React.FC = () => {
    const { trees, timeHorizon, initialBudget } = useScenarioStore();

    const metrics = useMemo(() => calculateMetrics(trees, timeHorizon), [trees, timeHorizon]);
    const timeSeriesData = useMemo(() => generateTimeSeriesData(trees), [trees]);
    const allocationData = useMemo(() => generateAllocationData(trees), [trees]);

    return (
        <div className="bg-white border-t border-slate-200 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] h-64 flex z-20">

            {/* Key Numbers */}
            <div className="w-1/3 p-6 border-r border-slate-100 flex flex-col justify-center">
                <h3 className="text-sm font-semibold text-slate-700 mb-4 tracking-wide uppercase">Impact Summary</h3>

                <div className="grid grid-cols-2 gap-4">
                    <div className="flex items-start">
                        <div className="p-2 bg-emerald-50 text-emerald-600 rounded-md mr-3">
                            <Trees size={20} />
                        </div>
                        <div>
                            <div className="text-xs text-slate-500 font-medium">Trees Active</div>
                            <div className="text-xl font-bold text-slate-800">{metrics.totalTrees}</div>
                        </div>
                    </div>

                    <div className="flex items-start">
                        <div className="p-2 bg-rose-50 text-rose-600 rounded-md mr-3">
                            <ThermometerSun size={20} />
                        </div>
                        <div>
                            <div className="text-xs text-slate-500 font-medium">Heat Relief</div>
                            <div className="text-xl font-bold text-slate-800">
                                {metrics.tempReductionPercent > 0 ? '-' : ''}{metrics.tempReductionPercent.toFixed(1)}%
                            </div>
                        </div>
                    </div>

                    <div className="flex items-start mt-2">
                        <div className="p-2 bg-indigo-50 text-indigo-600 rounded-md mr-3">
                            <MapIcon size={20} />
                        </div>
                        <div>
                            <div className="text-xs text-slate-500 font-medium">Area Impacted</div>
                            <div className="text-lg font-bold text-slate-800">{metrics.areaImpactedSqKm.toFixed(2)} <span className="text-xs font-normal">km²</span></div>
                        </div>
                    </div>

                    <div className="flex items-start mt-2">
                        <div className="p-2 bg-amber-50 text-amber-600 rounded-md mr-3">
                            <Wallet size={20} />
                        </div>
                        <div>
                            <div className="text-xs text-slate-500 font-medium">Total Spent</div>
                            <div className="text-lg font-bold text-slate-800">
                                ${(allocationData.reduce((acc, curr) => acc + curr.value, 0)).toLocaleString()}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Time Series Chart */}
            <div className="w-1/3 p-4 border-r border-slate-100 flex flex-col">
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Projected Cooling Over Time</h3>
                <div className="flex-1 w-full h-full min-h-[150px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={timeSeriesData} margin={{ top: 5, right: 20, bottom: 5, left: -20 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                            <XAxis dataKey="year" tick={{ fontSize: 10, fill: '#64748b' }} tickLine={false} axisLine={false} />
                            <YAxis tick={{ fontSize: 10, fill: '#64748b' }} tickLine={false} axisLine={false} />
                            <RechartsTooltip
                                contentStyle={{ borderRadius: '6px', fontSize: '12px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}
                                labelStyle={{ fontWeight: 'bold', color: '#334155' }}
                            />
                            <Line
                                type="monotone"
                                dataKey="heatReduction"
                                name="Heat Reduction %"
                                stroke="#0284c7"
                                strokeWidth={2}
                                dot={false}
                                activeDot={{ r: 4 }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Allocation Chart */}
            <div className="w-1/3 p-4 flex flex-col">
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Budget Allocation</h3>
                <div className="flex-1 w-full h-full min-h-[150px] flex items-center justify-center">
                    {allocationData.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={allocationData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
                                <XAxis type="number" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                                <YAxis dataKey="name" type="category" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} width={80} />
                                <RechartsTooltip
                                    cursor={{ fill: '#f1f5f9' }}
                                    contentStyle={{ borderRadius: '6px', fontSize: '12px', border: '1px solid #e2e8f0' }}
                                    formatter={(value: number) => [`$${value.toLocaleString()}`, 'Spent']}
                                />
                                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                                    {allocationData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="text-sm text-slate-400 italic">No budget allocated yet.</div>
                    )}
                </div>
            </div>

        </div>
    );
};

export default MetricsPanel;
