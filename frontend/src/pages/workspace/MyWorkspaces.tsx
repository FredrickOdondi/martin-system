import { Card, Badge } from '../../components/ui'
import { Link } from 'react-router-dom'

export default function MyWorkspaces() {
    const workspaces = [
        { id: 'energy', name: 'Energy & Power Infrastructure', color: 'blue', members: 24, progress: 78, deadline: 'Jan 15, 2026', status: 'active', decisions: 12, documents: 45 },
        { id: 'minerals', name: 'Critical Minerals & Mining', color: 'purple', members: 18, progress: 65, deadline: 'Jan 20, 2026', status: 'active', decisions: 8, documents: 32 },
        { id: 'digital', name: 'Digital Economy & Connectivity', color: 'green', members: 32, progress: 82, deadline: 'Jan 10, 2026', status: 'active', decisions: 15, documents: 58 },
        { id: 'trade', name: 'Trade & Customs Harmonization', color: 'orange', members: 21, progress: 45, deadline: 'Feb 5, 2026', status: 'planning', decisions: 5, documents: 28 },
        { id: 'agriculture', name: 'Agribusiness & Food Security', color: 'emerald', members: 19, progress: 55, deadline: 'Jan 25, 2026', status: 'active', decisions: 9, documents: 38 },
    ]

    return (
        <div className="max-w-7xl mx-auto space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-display font-bold text-slate-900 dark:text-white transition-colors">My TWGs</h1>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Technical Working Groups you're assigned to</p>
                </div>
                <div className="flex gap-3">
                    <select className="bg-white dark:bg-dark-card border border-slate-200 dark:border-dark-border rounded-lg px-4 py-2 text-sm font-medium focus:ring-2 focus:ring-blue-500 transition-colors">
                        <option>All Status</option>
                        <option>Active</option>
                        <option>Planning</option>
                        <option>Completed</option>
                    </select>
                    <button className="btn-primary text-sm flex items-center gap-2">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
                        Create TWG
                    </button>
                </div>
            </div>

            {/* Stats Overview */}
            <div className="grid grid-cols-4 gap-6">
                {[
                    { label: 'Active TWGs', value: '5', icon: 'workspace' },
                    { label: 'Total Members', value: '114', icon: 'users' },
                    { label: 'Pending Decisions', value: '23', icon: 'check' },
                    { label: 'Avg. Progress', value: '65%', icon: 'chart' },
                ].map(stat => (
                    <Card key={stat.label} className="p-6 text-center">
                        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">{stat.label}</p>
                        <p className="text-3xl font-display font-black text-slate-900 dark:text-white">{stat.value}</p>
                    </Card>
                ))}
            </div>

            {/* TWG Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {workspaces.map(twg => (
                    <Link key={twg.id} to={`/workspace/${twg.id}`}>
                        <Card className="p-0 overflow-hidden hover:ring-2 hover:ring-blue-500/50 transition-all group cursor-pointer h-full">
                            <div className={`h-2 bg-gradient-to-r from-${twg.color}-500 to-${twg.color}-600`}></div>
                            <div className="p-6 space-y-6">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <h3 className="text-lg font-bold text-slate-900 dark:text-white group-hover:text-blue-600 transition-colors">{twg.name}</h3>
                                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-medium">Deadline: {twg.deadline}</p>
                                    </div>
                                    <Badge
                                        variant={twg.status === 'active' ? 'success' : 'neutral'}
                                        className="uppercase text-[9px] font-black tracking-widest"
                                    >
                                        {twg.status}
                                    </Badge>
                                </div>

                                <div className="space-y-2">
                                    <div className="flex justify-between text-xs">
                                        <span className="font-bold text-slate-500">Overall Progress</span>
                                        <span className="font-black text-slate-900 dark:text-white">{twg.progress}%</span>
                                    </div>
                                    <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                                        <div
                                            className={`h-full bg-gradient-to-r from-${twg.color}-500 to-${twg.color}-600 transition-all`}
                                            style={{ width: `${twg.progress}%` }}
                                        ></div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-3 gap-4 pt-4 border-t border-slate-100 dark:border-dark-border">
                                    <div className="text-center">
                                        <p className="text-2xl font-black text-slate-900 dark:text-white">{twg.members}</p>
                                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tight">Members</p>
                                    </div>
                                    <div className="text-center">
                                        <p className="text-2xl font-black text-slate-900 dark:text-white">{twg.decisions}</p>
                                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tight">Decisions</p>
                                    </div>
                                    <div className="text-center">
                                        <p className="text-2xl font-black text-slate-900 dark:text-white">{twg.documents}</p>
                                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tight">Documents</p>
                                    </div>
                                </div>
                            </div>
                        </Card>
                    </Link>
                ))}
            </div>
        </div>
    )
}
