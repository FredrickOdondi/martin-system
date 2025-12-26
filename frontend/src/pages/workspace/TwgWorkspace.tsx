import { Card, Badge, Avatar } from '../../components/ui'

export default function TwgWorkspace() {
    const members = [
        { name: 'Dr. A. Sow', role: 'Chairperson', avatar: 'AS' },
        { name: 'John Doe', role: 'Member', avatar: 'JD' },
        { name: 'Maria Kone', role: 'Member', avatar: 'MK' },
        { name: 'Sarah Lee', role: 'Member', avatar: 'SL' },
    ]

    const actions = [
        { task: 'Review Renewable Energy Annex', assignee: 'John Doe', avatar: 'JD', date: 'Oct 10', status: 'In Progress' },
        { task: 'Approve Minutes from Sept 1st', assignee: 'Dr. A. Sow', avatar: 'AS', date: 'Sept 15', status: 'Overdue' },
        { task: 'Draft Logistics Plan', assignee: 'M. Kone', avatar: 'MK', date: 'Oct 20', status: 'Not Started' },
    ]

    const documents = [
        { name: 'Energy_Policy_Draft_v2.pdf', size: '2.4 MB', date: 'Uploaded today', type: 'pdf' },
        { name: 'Meeting_Brief_001.docx', size: '845 KB', date: '2 days ago', type: 'doc' },
    ]

    return (
        <div className="flex h-full gap-6">
            <div className="flex-1 space-y-6">
                {/* Banner Section */}
                <div className="relative h-48 rounded-2xl overflow-hidden bg-gradient-to-r from-blue-700 via-blue-800 to-blue-900">
                    <div className="absolute inset-0 opacity-20">
                        <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                            <path d="M0 0 L100 0 L100 100 L0 100 Z" fill="url(#grad)" />
                            <defs>
                                <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
                                    <stop offset="0%" style={{ stopColor: 'white', stopOpacity: 0.2 }} />
                                    <stop offset="100%" style={{ stopColor: 'white', stopOpacity: 0 }} />
                                </linearGradient>
                            </defs>
                        </svg>
                    </div>
                    <div className="relative z-10 h-full flex flex-col justify-end p-8 text-white">
                        <div className="flex items-center gap-2 mb-2">
                            <Badge className="bg-white/20 text-white border-0">ACTIVE WORKSPACE</Badge>
                            <Badge className="bg-white/10 text-white border-0">ECOWAS SUMMIT 2024</Badge>
                        </div>
                        <h1 className="text-3xl font-display font-bold">Energy Technical Working Group</h1>
                        <p className="max-w-xl text-blue-100 text-sm mt-2">
                            Focusing on renewable energy integration, cross-border power transmission, and sustainable policy frameworks for the region.
                        </p>

                        <div className="absolute top-8 right-8 flex gap-3">
                            <button className="p-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors flex items-center gap-2 text-sm font-medium">
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                                </svg>
                                Settings
                            </button>
                            <button className="p-2 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors flex items-center gap-2 text-sm font-medium shadow-lg shadow-blue-900/40">
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                                </svg>
                                New Meeting
                            </button>
                        </div>
                    </div>
                </div>

                {/* Info Row */}
                <div className="grid grid-cols-4 gap-4">
                    <Card className="p-4 flex flex-col gap-1">
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
                            Chairperson
                        </span>
                        <p className="font-bold text-slate-900 dark:text-white transition-colors">Dr. A. Sow</p>
                    </Card>
                    <Card className="p-4 flex flex-col gap-1">
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                            Next Deadline
                        </span>
                        <p className="font-bold text-slate-900 dark:text-white transition-colors">Oct 12, 2024</p>
                    </Card>
                    <Card className="p-4 flex flex-col gap-1">
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" /></svg>
                            Pending Decisions
                        </span>
                        <p className="font-bold text-slate-900 dark:text-white transition-colors">3 Items</p>
                    </Card>
                    <Card className="p-4 flex flex-col gap-1">
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
                            Members
                        </span>
                        <div className="flex -space-x-2 mt-1">
                            {members.map((m, i) => (
                                <Avatar key={i} fallback={m.avatar} size="sm" className="ring-2 ring-white dark:ring-dark-card" />
                            ))}
                            <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 border-2 border-white dark:border-dark-card flex items-center justify-center text-[10px] font-bold text-slate-500">
                                +12
                            </div>
                        </div>
                    </Card>
                </div>

                <div className="grid grid-cols-2 gap-6">
                    {/* Action Items */}
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <h2 className="text-lg font-bold text-slate-900 dark:text-white transition-colors">Action Items</h2>
                            <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">View All</button>
                        </div>
                        <Card className="p-0 overflow-hidden">
                            <table className="w-full text-sm text-left">
                                <thead className="bg-slate-50 dark:bg-slate-800 text-slate-400 font-bold text-[10px] uppercase transition-colors">
                                    <tr>
                                        <th className="px-4 py-3">Task</th>
                                        <th className="px-4 py-3">Assignee</th>
                                        <th className="px-4 py-3">Due Date</th>
                                        <th className="px-4 py-3">Status</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                                    {actions.map((action, i) => (
                                        <tr key={i} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                                            <td className="px-4 py-3 font-medium text-slate-700 dark:text-slate-300 transition-colors">{action.task}</td>
                                            <td className="px-4 py-3">
                                                <div className="flex items-center gap-2">
                                                    <Avatar size="sm" fallback={action.avatar} />
                                                    <span className="text-xs text-slate-500">{action.assignee}</span>
                                                </div>
                                            </td>
                                            <td className="px-4 py-3 text-slate-500">{action.date}</td>
                                            <td className="px-4 py-3">
                                                <Badge variant={action.status === 'In Progress' ? 'info' : action.status === 'Overdue' ? 'danger' : 'neutral'} size="sm">
                                                    {action.status}
                                                </Badge>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </Card>
                    </div>

                    {/* Timeline */}
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <h2 className="text-lg font-bold text-slate-900 dark:text-white transition-colors">Timeline</h2>
                        </div>
                        <Card className="p-6">
                            <div className="space-y-6">
                                <div className="flex gap-4 relative">
                                    <div className="absolute left-[7px] top-6 bottom-[-24px] w-px bg-slate-100 dark:bg-slate-800"></div>
                                    <div className="w-4 h-4 rounded-full bg-green-500 ring-4 ring-green-100 dark:ring-green-900/20 z-10 flex-shrink-0"></div>
                                    <div>
                                        <p className="text-[10px] font-bold text-green-600 uppercase">Completed • Sept 1</p>
                                        <h4 className="font-bold text-sm text-slate-900 dark:text-white transition-colors">Kick-off Meeting</h4>
                                        <p className="text-xs text-slate-500 mt-0.5 transition-colors">Initial goal setting and role assignment.</p>
                                    </div>
                                </div>
                                <div className="flex gap-4 relative">
                                    <div className="absolute left-[7px] top-6 bottom-[-24px] w-px bg-slate-100 dark:bg-slate-800"></div>
                                    <div className="w-4 h-4 rounded-full bg-blue-500 ring-4 ring-blue-100 dark:ring-blue-900/20 z-10 flex-shrink-0"></div>
                                    <div className="flex-1">
                                        <p className="text-[10px] font-bold text-blue-600 uppercase">Today • 2:00 PM</p>
                                        <h4 className="font-bold text-sm text-slate-900 dark:text-white transition-colors">Draft Policy Review</h4>
                                        <p className="text-xs text-slate-500 mt-0.5 transition-colors">Virtual review of the v2 document.</p>
                                        <button className="mt-2 btn-secondary text-xs py-1 px-3">Join Call</button>
                                    </div>
                                </div>
                                <div className="flex gap-4">
                                    <div className="w-4 h-4 rounded-full bg-slate-200 dark:bg-slate-700 border-4 border-white dark:border-dark-card z-10 flex-shrink-0 transition-colors"></div>
                                    <div>
                                        <p className="text-[10px] font-bold text-slate-400 uppercase">Upcoming • Oct 15</p>
                                        <h4 className="font-bold text-sm text-slate-900 dark:text-white transition-colors">Summit Presentation</h4>
                                        <p className="text-xs text-slate-500 mt-0.5 transition-colors">Final presentation to the ECOWAS board.</p>
                                    </div>
                                </div>
                            </div>
                        </Card>
                    </div>
                </div>

                {/* Recent Documents */}
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-bold text-slate-900 dark:text-white transition-colors">Recent Documents</h2>
                        <button className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
                            Upload New
                        </button>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        {documents.map((doc, i) => (
                            <Card key={i} className="flex items-center gap-4 p-4 hover:border-blue-300 dark:hover:border-blue-900 transition-all cursor-pointer group">
                                <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${doc.type === 'pdf' ? 'bg-red-50 text-red-600' : 'bg-blue-50 text-blue-600'} transition-colors`}>
                                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                    </svg>
                                </div>
                                <div className="flex-1">
                                    <h4 className="font-bold text-sm text-slate-900 dark:text-white transition-colors truncate">{doc.name}</h4>
                                    <p className="text-xs text-slate-500 transition-colors uppercase font-bold tracking-tighter mt-0.5">{doc.size} • {doc.date}</p>
                                </div>
                                <button className="p-1.5 text-slate-300 group-hover:text-slate-500 transition-colors">
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" /></svg>
                                </button>
                            </Card>
                        ))}
                    </div>
                </div>
            </div>

            {/* AI Copilot Sidebar */}
            <div className="w-80 flex flex-col gap-6">
                <Card className="flex-1 flex flex-col p-0 overflow-hidden bg-white dark:bg-dark-card border-slate-100 dark:border-dark-border transition-colors">
                    {/* Header */}
                    <div className="p-4 border-b border-slate-100 dark:border-dark-border flex items-center justify-between transition-colors">
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white">
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
                            </div>
                            <div>
                                <h3 className="font-bold text-sm text-slate-900 dark:text-white">ECOWAS AI Copilot</h3>
                                <p className="text-[10px] text-green-500 font-bold uppercase flex items-center gap-1 transition-colors">
                                    <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                                    Online • Energy Context
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Chat Messages */}
                    <div className="flex-1 overflow-auto p-4 space-y-4">
                        <div className="flex gap-3">
                            <div className="w-6 h-6 rounded bg-slate-100 dark:bg-slate-800 flex items-center justify-center flex-shrink-0 transition-colors">
                                <svg className="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
                            </div>
                            <div className="bg-slate-50 dark:bg-slate-800/50 p-3 rounded-2xl rounded-tl-none transition-colors">
                                <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed transition-colors">
                                    Hello Dr. Sow. I've analyzed the <span className="text-blue-600 font-bold underline cursor-pointer">Energy_Policy_Draft_v2.pdf</span> uploaded today. It appears 85% compliant with the 2023 sustainability framework.
                                </p>
                            </div>
                        </div>

                        <div className="flex gap-3">
                            <div className="w-6 h-6 rounded bg-slate-100 dark:bg-slate-800 flex items-center justify-center flex-shrink-0 transition-colors">
                                <svg className="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
                            </div>
                            <div className="bg-slate-50 dark:bg-slate-800/50 p-3 rounded-2xl rounded-tl-none transition-colors">
                                <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed transition-colors">
                                    Would you like me to draft an agenda for the 'Draft Policy Review' meeting based on the missing compliance items?
                                </p>
                            </div>
                        </div>

                        <div className="flex gap-3 flex-row-reverse">
                            <div className="bg-blue-600 text-white p-3 rounded-2xl rounded-tr-none transition-colors">
                                <p className="text-xs leading-relaxed">
                                    Yes, please draft the agenda. Also, summarize the main conflicts in section 4.
                                </p>
                            </div>
                        </div>

                        <div className="flex gap-3">
                            <div className="w-6 h-6 rounded bg-slate-100 dark:bg-slate-800 flex items-center justify-center flex-shrink-0 transition-colors">
                                <svg className="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
                            </div>
                            <div className="flex gap-1 p-2 bg-slate-50 dark:bg-slate-800/50 rounded-full transition-colors">
                                <div className="w-1 h-1 bg-slate-400 rounded-full animate-bounce"></div>
                                <div className="w-1 h-1 bg-slate-400 rounded-full animate-bounce [animation-delay:0.2s]"></div>
                                <div className="w-1 h-1 bg-slate-400 rounded-full animate-bounce [animation-delay:0.4s]"></div>
                            </div>
                        </div>
                    </div>

                    {/* Input */}
                    <div className="p-4 border-t border-slate-100 dark:border-dark-border space-y-3 transition-colors">
                        <div className="flex flex-wrap gap-2">
                            <button className="px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded-lg text-[10px] font-bold text-slate-500 hover:text-slate-700 transition-colors">Generate Summary</button>
                            <button className="px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded-lg text-[10px] font-bold text-slate-500 hover:text-slate-700 transition-colors">Schedule Meeting</button>
                        </div>
                        <div className="relative">
                            <input
                                type="text"
                                placeholder="Ask AI Copilot..."
                                className="w-full bg-slate-50 dark:bg-slate-800 border-0 rounded-xl px-4 py-3 text-xs focus:ring-2 focus:ring-blue-500 transition-colors pr-10"
                            />
                            <button className="absolute right-2 top-1.5 p-1.5 bg-blue-600 text-white rounded-lg">
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
                            </button>
                        </div>
                    </div>
                </Card>
            </div>
        </div>
    )
}
