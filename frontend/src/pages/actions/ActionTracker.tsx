import { Card, Badge, Avatar } from '../../components/ui'

interface Task {
    title: string
    source: 'AI Extracted' | 'Manual Entry'
    date: string
    avatar: string
    priority: 'low' | 'medium' | 'high'
    progress?: number
    overdue?: boolean
    completed?: boolean
}

interface Column {
    name: string
    count: number
    tasks: Task[]
}

export default function ActionTracker() {
    const stats = [
        { label: 'Open Items', value: '12', change: '+2 new', icon: ListIcon, color: 'text-blue-500' },
        { label: 'Overdue', value: '5', change: '+1 today', icon: AlertIcon, color: 'text-red-500' },
        { label: 'Completed (Week)', value: '8', change: '+3 items', icon: CheckIcon, color: 'text-green-500' },
    ]

    const columns: Column[] = [
        {
            name: 'To Do',
            count: 4,
            tasks: [
                { title: 'Draft Logistics Protocol for VVIPs', source: 'AI Extracted', date: 'Nov 12', avatar: 'JD', priority: 'medium' },
                { title: 'Update Security Clearance List', source: 'Manual Entry', date: 'Nov 15', avatar: 'MK', priority: 'low' }
            ]
        },
        {
            name: 'In Progress',
            count: 3,
            tasks: [
                { title: 'Review Border Control Integration Plan', source: 'AI Extracted', date: 'Nov 10', avatar: 'AS', priority: 'high', progress: 65 }
            ]
        },
        {
            name: 'Review',
            count: 2,
            tasks: [
                { title: 'Finalize budget for Q4 Summit', source: 'Manual Entry', date: 'Oct 30', avatar: 'SF', priority: 'high', overdue: true }
            ]
        },
        {
            name: 'Completed',
            count: 8,
            tasks: [
                { title: 'Distribute meeting agenda', source: 'AI Extracted', date: 'Nov 01', avatar: 'JD', priority: 'medium', completed: true }
            ]
        }
    ]

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-display font-bold text-slate-900 dark:text-white transition-colors">Action Items Tracker</h1>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Manage and track tasks for the Security Technical Working Group</p>
                </div>
                <div className="flex gap-3">
                    <button className="btn-secondary text-sm flex items-center gap-2">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
                        Upload Minutes
                    </button>
                    <button className="btn-primary text-sm flex items-center gap-2">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
                        Add New Task
                    </button>
                </div>
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {stats.map((stat) => (
                    <Card key={stat.label} className="p-5 flex items-start justify-between">
                        <div className="space-y-1">
                            <p className="text-xs font-bold text-slate-500 dark:text-slate-500 uppercase tracking-wider">{stat.label}</p>
                            <div className="flex items-baseline gap-2">
                                <h2 className="text-3xl font-display font-bold text-slate-900 dark:text-white transition-colors">{stat.value}</h2>
                                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${stat.color === 'text-red-500' ? 'bg-red-50 text-red-600 dark:bg-red-900/30' : 'bg-green-50 text-green-600 dark:bg-green-900/30'}`}>
                                    {stat.change}
                                </span>
                            </div>
                        </div>
                        <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-xl transition-colors">
                            <stat.icon className={`w-6 h-6 ${stat.color}`} />
                        </div>
                    </Card>
                ))}
            </div>

            {/* AI extraction alert */}
            <div className="bg-blue-600/10 border border-blue-500/20 rounded-xl p-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white">
                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                    </div>
                    <div>
                        <h4 className="font-bold text-slate-900 dark:text-white transition-colors">AI Extraction Complete</h4>
                        <p className="text-xs text-slate-600 dark:text-slate-400">3 new action items extracted from "Meeting Minutes - Nov 10"</p>
                    </div>
                </div>
                <button className="btn-primary py-1.5 px-4 text-xs font-bold">Review Items</button>
            </div>

            {/* Toolbar */}
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-dark-border pb-4 transition-colors">
                <div className="flex gap-4">
                    <button className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-2">
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" /></svg>
                        Filter
                    </button>
                    <div className="flex items-center gap-4 text-xs font-medium text-slate-500">
                        <div className="flex items-center gap-1 cursor-pointer hover:text-blue-600 transition-colors">Assignee <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M19 9l-7 7-7-7" /></svg></div>
                        <div className="flex items-center gap-1 cursor-pointer hover:text-blue-600 transition-colors">Priority <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M19 9l-7 7-7-7" /></svg></div>
                        <div className="flex items-center gap-1 cursor-pointer hover:text-blue-600 transition-colors">Due Date <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M19 9l-7 7-7-7" /></svg></div>
                    </div>
                </div>
                <div className="flex bg-slate-100 dark:bg-slate-800 rounded-lg p-1 transition-colors">
                    <button className="bg-white dark:bg-dark-card shadow-sm px-3 py-1.5 rounded-md flex items-center gap-2 text-xs font-bold text-slate-900 dark:text-white transition-all">
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>
                        Board
                    </button>
                    <button className="px-3 py-1.5 flex items-center gap-2 text-xs font-bold text-slate-400 hover:text-slate-600 transition-colors">
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
                        List
                    </button>
                </div>
            </div>

            {/* Kanban Board */}
            <div className="grid grid-cols-4 gap-6">
                {columns.map((column) => (
                    <div key={column.name} className="space-y-4">
                        <div className="flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full ${column.name === 'To Do' ? 'bg-slate-400' :
                                column.name === 'In Progress' ? 'bg-blue-600' :
                                    column.name === 'Review' ? 'bg-orange-500' :
                                        'bg-green-500'
                                }`}></div>
                            <h3 className="font-bold text-sm text-slate-900 dark:text-white transition-colors">{column.name}</h3>
                            <Badge size="sm" className="bg-slate-100 dark:bg-slate-800 text-slate-500 transition-colors">{column.count}</Badge>
                        </div>

                        <div className="space-y-4">
                            {column.tasks.map((task, i) => (
                                <Card key={i} className={`p-4 space-y-4 hover:ring-2 hover:ring-blue-500/50 transition-all cursor-pointer ${task.overdue ? 'border-red-500' : ''}`}>
                                    <div className="flex items-center justify-between">
                                        <Badge variant="neutral" className="text-[9px] px-1.5 py-0 flex items-center gap-1 transition-colors">
                                            <svg className="w-2.5 h-2.5 text-purple-600" fill="currentColor" viewBox="0 0 20 20"><path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" /></svg>
                                            {task.source}
                                        </Badge>
                                        {task.completed && (
                                            <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center text-white">
                                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                                            </div>
                                        )}
                                        {task.overdue && (
                                            <Badge variant="danger" size="sm" className="text-[9px] uppercase font-bold">Overdue</Badge>
                                        )}
                                    </div>

                                    <h4 className={`font-bold text-sm leading-tight transition-colors ${task.completed ? 'text-slate-400 line-through' : 'text-slate-900 dark:text-white'}`}>
                                        {task.title}
                                    </h4>

                                    {task.progress !== undefined && (
                                        <div className="space-y-1">
                                            <div className="h-1.5 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden transition-colors">
                                                <div className="h-full bg-blue-600" style={{ width: `${task.progress}%` }}></div>
                                            </div>
                                            <div className="flex justify-between items-center text-[10px] text-slate-500">
                                                <span>Progress</span>
                                                <span>{task.progress}%</span>
                                            </div>
                                        </div>
                                    )}

                                    <div className="flex items-center justify-between pt-2">
                                        <div className="flex items-center gap-2">
                                            <Avatar size="sm" fallback={task.avatar} />
                                        </div>
                                        <div className={`flex items-center gap-1.5 text-xs font-bold transition-colors ${task.overdue ? 'text-red-500' : 'text-slate-400'}`}>
                                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                            {task.date}
                                        </div>
                                    </div>
                                </Card>
                            ))}
                            <button className="w-full py-3 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-xl text-slate-400 hover:border-blue-500 hover:text-blue-500 flex items-center justify-center transition-all">
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M12 4v16m8-8H4" /></svg>
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}

function ListIcon({ className }: { className?: string }) {
    return (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
    )
}

function AlertIcon({ className }: { className?: string }) {
    return (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
    )
}

function CheckIcon({ className }: { className?: string }) {
    return (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
    )
}
