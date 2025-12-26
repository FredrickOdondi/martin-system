import { Card, Badge } from '../../components/ui'

export default function DealPipeline() {
    const stats = [
        { label: 'Identified Projects', value: '42', change: '+5 this month', icon: ProjectsIcon, color: 'text-blue-600' },
        { label: 'Total Investment', value: '$12.4B', change: '+1.2B target', icon: MoneyIcon, color: 'text-green-600' },
        { label: 'Avg. AfCEN Score', value: '84', change: 'Top Tier', icon: ScoreIcon, color: 'text-purple-600' },
    ]

    const projects = [
        { name: 'WAPP Solar Expansion B', pillar: 'Energy', country: 'Nigeria', investment: '$450M', score: 92, status: 'Pre-Vetting', statusColor: 'info' },
        { name: 'Lekki Port Digitalization', pillar: 'Digital', country: 'Nigeria', investment: '$120M', score: 88, status: 'Due Diligence', statusColor: 'warning' },
        { name: 'Regional Agri-Hub Freetown', pillar: 'Agribusiness', country: 'Sierra Leone', investment: '$85M', score: 76, status: 'Identified', statusColor: 'neutral' },
        { name: 'Critical Minerals Belt', pillar: 'Minerals', country: 'Guinea', investment: '$2.1B', score: 95, status: 'Ready for Summit', statusColor: 'success' },
        { name: 'Cross-Border Fiber Link', pillar: 'Digital', country: 'Regional', investment: '$210M', score: 82, status: 'Due Diligence', statusColor: 'warning' },
    ]

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-display font-bold text-slate-900 dark:text-white transition-colors">Summit Deal Pipeline</h1>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Resource Mobilization & Project Vetting Command Center</p>
                </div>
                <div className="flex gap-3">
                    <button className="btn-secondary text-sm flex items-center gap-2">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
                        Export Pipeline
                    </button>
                    <button className="btn-primary text-sm flex items-center gap-2">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
                        Add Project
                    </button>
                </div>
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {stats.map((stat) => (
                    <Card key={stat.label} className="p-6 flex items-start justify-between group hover:border-blue-400/50 transition-all">
                        <div className="space-y-2">
                            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">{stat.label}</p>
                            <div className="flex items-baseline gap-2">
                                <h2 className="text-3xl font-display font-bold text-slate-900 dark:text-white transition-colors">{stat.value}</h2>
                                <span className="text-[10px] font-bold text-green-500">{stat.change}</span>
                            </div>
                        </div>
                        <div className={`p-4 rounded-2xl bg-slate-50 dark:bg-slate-800 transition-all group-hover:scale-110 ${stat.color}`}>
                            <stat.icon className="w-6 h-6" />
                        </div>
                    </Card>
                ))}
            </div>

            {/* Project Table */}
            <Card className="p-0 overflow-hidden shadow-xl shadow-slate-200/50 dark:shadow-none border-slate-100 dark:border-dark-border transition-colors">
                <div className="p-6 border-b border-slate-100 dark:border-dark-border flex items-center justify-between transition-colors">
                    <h3 className="font-bold text-slate-900 dark:text-white">Active Projects Pipeline</h3>
                    <div className="flex gap-2">
                        <select className="bg-slate-50 dark:bg-slate-800 border-0 rounded-lg text-xs font-bold px-3 py-1.5 outline-none focus:ring-2 focus:ring-blue-500 transition-colors">
                            <option>All Pillars</option>
                            <option>Energy</option>
                            <option>Minerals</option>
                            <option>Digital</option>
                        </select>
                        <select className="bg-slate-50 dark:bg-slate-800 border-0 rounded-lg text-xs font-bold px-3 py-1.5 outline-none focus:ring-2 focus:ring-blue-500 transition-colors">
                            <option>Highest Score</option>
                            <option>Newest</option>
                            <option>Largest Scale</option>
                        </select>
                    </div>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm border-collapse">
                        <thead>
                            <tr className="bg-slate-50 dark:bg-slate-800/50 text-[10px] font-black text-slate-400 uppercase tracking-widest transition-colors">
                                <th className="px-6 py-4">Project Name</th>
                                <th className="px-6 py-4">Pillar</th>
                                <th className="px-6 py-4">Country</th>
                                <th className="px-6 py-4">Investment</th>
                                <th className="px-6 py-4">AfCEN Score</th>
                                <th className="px-6 py-4">Status</th>
                                <th className="px-6 py-4 text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800 transition-colors">
                            {projects.map((p, i) => (
                                <tr key={i} className="hover:bg-slate-50 dark:hover:bg-slate-800/20 transition-colors group">
                                    <td className="px-6 py-4">
                                        <div className="font-bold text-slate-900 dark:text-white group-hover:text-blue-600 transition-colors">{p.name}</div>
                                        <div className="text-[10px] text-slate-400 uppercase font-black">ID: ECO-2026-0{i + 1}</div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <Badge variant="neutral" size="sm" className="font-bold">{p.pillar}</Badge>
                                    </td>
                                    <td className="px-6 py-4 text-slate-600 dark:text-slate-400 font-medium">{p.country}</td>
                                    <td className="px-6 py-4 text-slate-900 dark:text-white font-black">{p.investment}</td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-2">
                                            <div className="flex-1 h-1.5 w-16 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                                                <div className={`h-full ${p.score > 90 ? 'bg-purple-500' : p.score > 80 ? 'bg-blue-500' : 'bg-green-500'}`} style={{ width: `${p.score}%` }}></div>
                                            </div>
                                            <span className="font-black text-slate-700 dark:text-slate-300">{p.score}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <Badge variant={p.statusColor as any} size="sm" className="font-black tracking-tighter uppercase whitespace-nowrap">{p.status}</Badge>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <button className="text-[10px] font-black text-blue-600 hover:text-blue-700 uppercase tracking-widest border-b border-transparent hover:border-blue-600">Details</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <div className="p-4 bg-slate-50 dark:bg-slate-800/30 flex justify-center transition-colors">
                    <button className="text-xs font-bold text-slate-500 hover:text-slate-700 transition-colors flex items-center gap-2">
                        Load 15 more projects
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M19 9l-7 7-7-7" /></svg>
                    </button>
                </div>
            </Card>

            {/* AI Insights Sidebar layout maybe? No let's do a bottom grid */}
            <div className="grid grid-cols-2 gap-6">
                <Card className="space-y-4">
                    <h3 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
                        <svg className="w-4 h-4 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
                        AI Deal Suggestion
                    </h3>
                    <div className="bg-purple-50 dark:bg-purple-900/10 border border-purple-100 dark:border-purple-900/20 rounded-xl p-4 space-y-3 transition-colors">
                        <p className="text-xs text-purple-900 dark:text-purple-300 leading-relaxed font-medium">
                            Analysis of the <span className="font-black underline">Energy TWG</span> minutes suggests a high-potential cross-border hydro project in Liberia. Currently not in pipeline.
                        </p>
                        <button className="bg-purple-600 hover:bg-purple-700 text-white text-[10px] font-black px-3 py-1.5 rounded-lg shadow-lg shadow-purple-900/20 uppercase tracking-widest">
                            Create Lead
                        </button>
                    </div>
                </Card>

                <Card className="space-y-4">
                    <h3 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
                        <svg className="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
                        Funding Allocation
                    </h3>
                    <div className="flex items-end gap-2 h-20 pt-2">
                        {[40, 70, 45, 90, 30].map((h, i) => (
                            <div key={i} className="flex-1 bg-slate-100 dark:bg-slate-800 rounded-t-md relative group transition-colors">
                                <div className="absolute bottom-0 w-full bg-blue-500 rounded-t-md group-hover:bg-blue-600 transition-all" style={{ height: `${h}%` }}></div>
                            </div>
                        ))}
                    </div>
                    <div className="flex justify-between text-[8px] font-black text-slate-400 uppercase tracking-widest px-1">
                        <span>Energy</span>
                        <span>Digital</span>
                        <span>Agri</span>
                        <span>Minerals</span>
                        <span>Other</span>
                    </div>
                </Card>
            </div>
        </div>
    )
}

function ProjectsIcon({ className }: { className?: string }) {
    return (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
    )
}

function MoneyIcon({ className }: { className?: string }) {
    return (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
    )
}

function ScoreIcon({ className }: { className?: string }) {
    return (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
    )
}
