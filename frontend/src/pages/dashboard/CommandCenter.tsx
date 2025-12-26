import { Card, Badge } from '../../components/ui'

export default function CommandCenter() {
    const stats = [
        { label: 'ACTIVE TWGS', value: '12', trend: 'All operational', icon: TwgIcon, color: 'text-blue-500' },
        { label: 'OPEN ACTIONS', value: '45', trend: '12 Critical items', icon: ActionIcon, color: 'text-orange-500' },
        { label: 'DAYS TO SUMMIT', value: '14', trend: 'Feb 24, 2024', icon: CalendarIcon, color: 'text-purple-500' },
    ]

    const twgs = [
        { name: 'Energy', lead: 'Dr. A. Okafor', status: 'On Track', color: 'blue', readiness: 85, meetings: 3, actions: 5, projects: 2, insight: 'Budget proposal aligns with \'23 goals.' },
        { name: 'Trade & Customs', lead: 'S. Mensah', status: 'Critical', color: 'red', readiness: 40, meetings: 5, actions: 12, projects: 4, insight: 'Bottleneck identified in customs protocol.' },
        { name: 'Digital Infra', lead: 'K. Diop', status: 'Review Needed', color: 'amber', readiness: 60, meetings: 2, actions: 3, projects: 1, nextMeeting: 'TBD' },
        { name: 'Security Coop', lead: 'Gen. M. Faye', status: 'On Track', color: 'green', readiness: 92, meetings: 4, actions: 1, projects: 3, insight: 'Protocol draft finalized 2 days early.' },
    ]

    const timeline = [
        { date: 'FEB 10 • 10:00 AM', title: 'Energy TWG Review', type: 'Virtual • Teams Link', status: 'upcoming' },
        { date: 'FEB 12 • 02:00 PM', title: 'Trade Documentation Deadline', type: 'Critical Submission', status: 'critical' },
        { date: 'FEB 15 • 09:00 AM', title: 'Heads of State Briefing Prep', type: 'Conference Room A', status: 'upcoming' },
        { date: 'FEB 18 • 11:30 AM', title: 'Security Protocols Finalization', type: 'Closed Door Session', status: 'upcoming' },
    ]

    return (
        <div className="space-y-6">
            {/* Page Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-display font-bold text-slate-900 dark:text-white">Summit Command Center</h1>
                    <p className="text-slate-500 dark:text-slate-400">Real-time overview of technical working groups and summit readiness.</p>
                </div>
                <button className="btn-primary flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Generate Report
                </button>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {stats.map((stat) => (
                    <Card key={stat.label} className="flex items-start justify-between">
                        <div>
                            <p className="text-xs font-bold text-slate-500 dark:text-slate-500 tracking-wider transition-colors">{stat.label}</p>
                            <h2 className="text-4xl font-display font-bold mt-2 text-slate-900 dark:text-white transition-colors">{stat.value}</h2>
                            <p className="text-sm mt-2 text-green-600 flex items-center gap-1">
                                {stat.label === 'OPEN ACTIONS' ? (
                                    <span className="text-slate-400">{stat.trend}</span>
                                ) : (
                                    <>
                                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                                        </svg>
                                        {stat.trend}
                                    </>
                                )}
                            </p>
                        </div>
                        <div className={`p-3 rounded-lg bg-slate-50 dark:bg-slate-800 ${stat.color}`}>
                            <stat.icon className="w-6 h-6" />
                        </div>
                    </Card>
                ))}
            </div>

            {/* Alert Banner */}
            <div className="bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-900/30 rounded-xl p-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-red-100 dark:bg-red-900/30 rounded-lg flex items-center justify-center text-red-600 dark:text-red-500">
                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                    </div>
                    <div>
                        <h3 className="font-bold text-slate-900 dark:text-white">Critical Alert: Trade & Customs Group</h3>
                        <p className="text-sm text-slate-600 dark:text-slate-400">Missing required documentation for the upcoming Feb 12 review. Immediate attention required.</p>
                    </div>
                </div>
                <button className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-semibold hover:bg-red-700 transition-colors">
                    Review Alerts
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* TWG Overview */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-bold text-slate-900 dark:text-white transition-colors">TWG Status Overview</h2>
                        <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">View All Groups</button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {twgs.map((twg) => (
                            <Card key={twg.name} className="space-y-4">
                                <div className="flex justify-between items-start">
                                    <div className="flex gap-3">
                                        <div className={`p-2 rounded-lg bg-${twg.color === 'blue' ? 'blue' : twg.color === 'red' ? 'red' : twg.color === 'amber' ? 'amber' : 'green'}-100 dark:bg-${twg.color === 'blue' ? 'blue' : twg.color === 'red' ? 'red' : twg.color === 'amber' ? 'amber' : 'green'}-900/20 text-${twg.color === 'blue' ? 'blue' : twg.color === 'red' ? 'red' : twg.color === 'amber' ? 'amber' : 'green'}-600 dark:text-${twg.color === 'blue' ? 'blue' : twg.color === 'red' ? 'red' : twg.color === 'amber' ? 'amber' : 'green'}-400`}>
                                            {twg.name === 'Energy' && <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>}
                                            {twg.name === 'Trade & Customs' && <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>}
                                            {twg.name === 'Digital Infra' && <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071a9.904 9.904 0 0114.142 0M2.828 9.9a13.264 13.264 0 0118.344 0" /></svg>}
                                            {twg.name === 'Security Coop' && <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>}
                                        </div>
                                        <div>
                                            <h4 className="font-bold text-slate-900 dark:text-white transition-colors">{twg.name}</h4>
                                            <p className="text-xs text-slate-500">Lead: {twg.lead}</p>
                                        </div>
                                    </div>
                                    <Badge variant={twg.status === 'On Track' ? 'success' : twg.status === 'Critical' ? 'danger' : 'warning'} size="sm">
                                        {twg.status}
                                    </Badge>
                                </div>

                                <div className="grid grid-cols-3 gap-2 py-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg transition-colors">
                                    <div className="text-center">
                                        <p className="text-lg font-bold text-slate-900 dark:text-white">{twg.meetings}</p>
                                        <p className="text-[10px] uppercase font-bold text-slate-400">Meetings</p>
                                    </div>
                                    <div className="text-center border-x border-slate-200 dark:border-slate-700">
                                        <p className="text-lg font-bold text-slate-900 dark:text-white">{twg.actions}</p>
                                        <p className="text-[10px] uppercase font-bold text-slate-400">Actions</p>
                                    </div>
                                    <div className="text-center">
                                        <p className="text-lg font-bold text-slate-900 dark:text-white">{twg.projects}</p>
                                        <p className="text-[10px] uppercase font-bold text-slate-400">Projects</p>
                                    </div>
                                </div>

                                <div>
                                    <div className="flex justify-between items-center mb-1">
                                        <span className="text-xs text-slate-500">Readiness</span>
                                        <span className="text-xs font-bold text-slate-900 dark:text-white transition-colors">{twg.readiness}%</span>
                                    </div>
                                    <div className="h-1.5 w-full bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden transition-colors">
                                        <div className={`h-full ${twg.color === 'blue' ? 'bg-blue-600' : twg.color === 'red' ? 'bg-red-600' : twg.color === 'amber' ? 'bg-amber-500' : 'bg-green-600'}`} style={{ width: `${twg.readiness}%` }}></div>
                                    </div>
                                </div>

                                {twg.insight ? (
                                    <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg flex gap-2 transition-colors">
                                        <svg className="w-4 h-4 text-purple-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                            <path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" />
                                        </svg>
                                        <p className="text-[11px] text-slate-600 dark:text-slate-400">AI Insight: {twg.insight}</p>
                                    </div>
                                ) : (
                                    <div className="p-3 border border-dashed border-slate-200 dark:border-slate-700 rounded-lg">
                                        <p className="text-[11px] text-slate-500 flex items-center gap-2">
                                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                            Next Meeting: {twg.nextMeeting}
                                        </p>
                                    </div>
                                )}
                            </Card>
                        ))}
                    </div>
                </div>

                {/* Timeline & AI Recommendation */}
                <div className="space-y-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-bold text-slate-900 dark:text-white transition-colors">Upcoming Timeline</h2>
                        <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">Full Calendar</button>
                    </div>

                    <Card className="p-4">
                        <div className="space-y-6">
                            {timeline.map((item, idx) => (
                                <div key={idx} className="flex gap-4 relative">
                                    {idx !== timeline.length - 1 && (
                                        <div className="absolute left-[19px] top-10 bottom-[-24px] w-px bg-slate-200 dark:bg-slate-700"></div>
                                    )}
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 font-bold text-xs ring-4 ring-white dark:ring-dark-card transition-colors ${item.status === 'critical'
                                            ? 'bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400'
                                            : 'bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400'
                                        }`}>
                                        {item.date.split(' ')[1]}
                                    </div>
                                    <div>
                                        <p className={`text-[10px] font-bold uppercase transition-colors ${item.status === 'critical' ? 'text-red-500' : 'text-slate-400'}`}>
                                            {item.date}
                                        </p>
                                        <h4 className="font-bold text-sm text-slate-900 dark:text-white transition-colors mb-0.5">{item.title}</h4>
                                        <p className="text-xs text-slate-500 transition-colors">{item.type}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </Card>

                    <div className="bg-gradient-to-br from-blue-950 to-blue-900 text-white rounded-xl p-5 space-y-4">
                        <div className="flex items-center gap-2 text-blue-400">
                            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" />
                            </svg>
                            <span className="text-xs font-bold uppercase tracking-wider">AI Recommendation</span>
                        </div>
                        <p className="text-sm text-blue-100">
                            Consider scheduling a joint session between <span className="font-bold text-white">Trade</span> and <span className="font-bold text-white">Digital Infra</span> before Feb 14 to resolve data sharing protocols.
                        </p>
                        <button className="text-sm font-bold text-blue-400 hover:text-blue-300 transition-colors">
                            Schedule Now →
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}

function TwgIcon({ className }: { className?: string }) {
    return (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
    )
}

function ActionIcon({ className }: { className?: string }) {
    return (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
    )
}

function CalendarIcon({ className }: { className?: string }) {
    return (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
    )
}
