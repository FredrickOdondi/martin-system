import { Card, Badge } from '../../components/ui';

import { useEffect, useState } from 'react';
import { getConflicts, ConflictAlert, getDashboardStats, exportDashboardReport } from '../../services/dashboardService';

export default function ConflictDashboard() {
    const [stats, setStats] = useState<any>(null);
    const [conflicts, setConflicts] = useState<ConflictAlert[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadData = async () => {
            try {
                const [conflictsData, statsData] = await Promise.all([
                    getConflicts(),
                    getDashboardStats()
                ]);
                setConflicts(conflictsData);
                setStats(statsData);
            } catch (error) {
                console.error("Failed to load dashboard data", error);
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, []);

    // Calculate Weekly Packet progress from pipeline stats
    const totalDeals = stats?.pipeline?.total || 1;
    const completedDeals = (stats?.pipeline?.final_review || 0) + (stats?.pipeline?.signed || 0);
    const packetCompletion = Math.round((completedDeals / totalDeals) * 100) || 0;

    const weeklyPacket = {
        completion: packetCompletion,
        // Keep items static for now as they represent specific highlighted documents not yet in generic stats
        items: [
            { name: 'Session Prop: Green Hydrogen', status: 'Ready' },
            { name: 'Policy Note: Tariff Harmonization', status: 'Review' },
            { name: 'Budget Request: Q3', status: 'Pending Data' }
        ]
    };

    return (
        <div className="space-y-6 mb-8">
            <div className="flex items-center justify-between">
                <div>
                    <div className="flex items-center gap-2">
                        <h2 className="text-xl font-display font-bold text-slate-900 dark:text-white">Admin Control Tower</h2>
                        <Badge variant="warning" className="uppercase tracking-widest text-[10px]">Secretariat Eyes Only</Badge>
                    </div>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Synthesis & Conflict Resolution Center</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={() => exportDashboardReport()}
                        className="px-4 py-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-xl text-xs font-bold hover:shadow-lg transition-all active:scale-95"
                    >
                        Generate Weekly Packet
                    </button>
                    <button
                        onClick={() => {
                            setLoading(true);
                            getConflicts().then(data => {
                                setConflicts(data);
                                setLoading(false);
                            });
                        }}
                        className="px-4 py-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border border-red-100 dark:border-red-900/30 rounded-xl text-xs font-bold hover:bg-red-100 dark:hover:bg-red-900/40 transition-all flex items-center gap-2 active:scale-95"
                    >
                        <span className="material-symbols-outlined text-[16px]">warning</span>
                        Force Reconciliation
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-12 gap-6">
                {/* 1. Reconciliation State & Weekly Packet */}
                <div className="col-span-12 lg:col-span-4 space-y-6">
                    {/* Weekly Packet Status */}
                    <Card className="p-5 border-l-4 border-l-blue-500">
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <h3 className="font-bold text-slate-900 dark:text-white">Weekly Packet</h3>
                                <p className="text-[10px] text-slate-500 uppercase tracking-widest">Target: Friday 17:00</p>
                            </div>
                            <div className="text-right">
                                <span className="text-2xl font-bold text-blue-600">{weeklyPacket.completion}%</span>
                            </div>
                        </div>
                        <div className="w-full h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden mb-4">
                            <div className="h-full bg-blue-500 rounded-full" style={{ width: `${weeklyPacket.completion}%` }}></div>
                        </div>
                        <div className="space-y-2">
                            {weeklyPacket.items.map((item, i) => (
                                <div key={i} className="flex items-center justify-between text-xs">
                                    <span className="text-slate-600 dark:text-slate-300 font-medium">{item.name}</span>
                                    <span className={`font-bold ${item.status === 'Ready' ? 'text-emerald-500' :
                                        item.status === 'Review' ? 'text-amber-500' :
                                            'text-slate-400'
                                        }`}>{item.status}</span>
                                </div>
                            ))}
                        </div>
                    </Card>

                    {/* System Health / Reconciliation */}
                    <Card className="p-5 border-l-4 border-l-emerald-500">
                        <div className="flex justify-between items-start mb-2">
                            <div>
                                <h3 className="font-bold text-slate-900 dark:text-white">Reconciliation State</h3>
                                <p className="text-[10px] text-slate-500 uppercase tracking-widest">Auto-Debate Engine</p>
                            </div>
                            <span className="material-symbols-outlined text-emerald-500 animate-pulse">check_circle</span>
                        </div>
                        <div className="flex items-center gap-4 mt-4">
                            <div className="flex-1 text-center p-3 rounded-lg bg-emerald-50 dark:bg-emerald-900/20">
                                <div className="text-lg font-bold text-emerald-600 dark:text-emerald-400">
                                    {/* Mock 'Resolved' as Total - Pending for now */}
                                    {(stats?.metrics?.deals_in_pipeline || 0) + (stats?.metrics?.active_twgs || 0)}
                                </div>
                                <div className="text-[9px] font-black uppercase text-slate-400">Resolved</div>
                            </div>
                            <div className="flex-1 text-center p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20">
                                <div className="text-lg font-bold text-amber-600 dark:text-amber-400">
                                    {stats?.metrics?.pending_approvals ?? '-'}
                                </div>
                                <div className="text-[9px] font-black uppercase text-slate-400">Pending</div>
                            </div>
                        </div>
                    </Card>
                </div>

                {/* 2. Conflict Radar / Alerts */}
                <div className="col-span-12 lg:col-span-8">
                    <Card className="h-full p-0 overflow-hidden border-t-4 border-t-red-500">
                        <div className="p-5 border-b border-slate-100 dark:border-dark-border bg-red-50/50 dark:bg-red-900/10">
                            <h3 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                <span className="material-symbols-outlined text-red-500">radar</span>
                                Detected Conflicts & Inconsistencies
                            </h3>
                        </div>
                        <div className="divide-y divide-slate-100 dark:divide-slate-800">
                            {loading && (
                                <div className="p-8 text-center text-slate-500 italic">Scanning for conflicts...</div>
                            )}
                            {conflicts.map((conflict) => (
                                <div key={conflict.id || Math.random()} className="p-5 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group">
                                    <div className="flex justify-between items-start mb-2">
                                        <div className="flex items-center gap-2">
                                            <Badge variant={conflict.severity === 'high' || conflict.severity === 'critical' ? 'danger' : 'warning'} className="uppercase text-[10px] font-black tracking-widest">
                                                {conflict.conflict_type}
                                            </Badge>
                                            <span className="text-xs font-bold text-slate-500">
                                                {conflict.agents_involved.join(' vs ')}
                                            </span>
                                        </div>
                                        <button className="text-xs font-bold text-blue-600 hover:text-blue-700 opacity-0 group-hover:opacity-100 transition-opacity">
                                            View Debate Log →
                                        </button>
                                    </div>
                                    <h4 className="font-bold text-slate-900 dark:text-white mb-2">{conflict.description}</h4>
                                    <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-800 p-3 rounded-lg border border-slate-100 dark:border-slate-700">
                                        "{Object.entries(conflict.conflicting_positions || {}).map(([k, v]) => `${k}: ${v}`).join(' | ')}"
                                    </p>
                                    <div className="flex items-center gap-2 mt-4">
                                        <button className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold transition-colors">
                                            Initiate Auto-Negotiation
                                        </button>
                                        <button className="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 rounded-lg text-xs font-bold hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">
                                            Dismiss
                                        </button>
                                    </div>
                                </div>
                            ))}
                            {/* Empty State */}
                            {conflicts.length === 0 && (
                                <div className="p-12 text-center text-slate-400">
                                    <span className="material-symbols-outlined text-4xl mb-2">check_circle</span>
                                    <p>No active conflicts detected.</p>
                                </div>
                            )}
                        </div>
                    </Card>
                </div>
            </div>
        </div>
    );
}
