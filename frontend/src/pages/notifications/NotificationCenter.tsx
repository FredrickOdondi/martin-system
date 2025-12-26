import { useState } from 'react'
import { Card, Badge } from '../../components/ui'

export default function NotificationCenter() {
    const [activeCategory, setActiveCategory] = useState('all')

    const notifications = [
        {
            id: 1,
            type: 'urgent',
            category: 'action',
            icon: 'alert',
            title: 'OVERDUE: TWG Agenda Item #4',
            message: 'Submission was due yesterday. Please review and submit the required...',
            time: '2 hours ago',
            badge: 'URGENT',
            actions: [
                { label: 'Submit Now', variant: 'danger' },
                { label: 'Dismiss', variant: 'ghost' }
            ]
        },
        {
            id: 2,
            type: 'info',
            category: 'ai-agent',
            icon: 'ai',
            title: 'AI Agent Update: Trade Policy Review',
            message: 'The AI Agent has completed the first draft of the Trade Policy analysis. It is now ready for your approv...',
            time: '15 mins ago',
            badge: 'NEW',
            actions: [
                { label: 'Review Draft', variant: 'primary' }
            ]
        },
        {
            id: 3,
            type: 'document',
            category: 'document',
            icon: 'file',
            title: 'New Document: Summit_Protocol_v2.pdf',
            message: 'Delegate Johnson uploaded a new version of the summit protocol for the Security Council.',
            author: 'Delegate Johnson',
            time: '45 mins ago',
            actions: [
                { label: 'View File', variant: 'secondary' }
            ]
        },
        {
            id: 4,
            type: 'system',
            category: 'system',
            icon: 'settings',
            title: 'System Maintenance Scheduled',
            message: 'The portal will undergo scheduled maintenance on Saturday, Nov 15th from 2:00 AM to 4:00 AM GMT.',
            time: 'Yesterday',
            actions: []
        }
    ]

    const categories = [
        { id: 'all', label: 'All Notifications', count: 3 },
        { id: 'unread', label: 'Unread', count: 0 },
        { id: 'action', label: 'Action Required', count: 1 },
    ]

    const filterCategories = [
        { id: 'ai-agents', label: 'AI Agents', icon: '🤖' },
        { id: 'documents', label: 'Documents', icon: '📄' },
        { id: 'system', label: 'System Updates', icon: '⚙️' },
    ]

    return (
        <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-12 gap-8">
                {/* Left Sidebar */}
                <aside className="col-span-3 space-y-8">
                    <div>
                        <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-4">Inbox</h3>
                        <div className="space-y-1">
                            {categories.map(cat => (
                                <button
                                    key={cat.id}
                                    onClick={() => setActiveCategory(cat.id)}
                                    className={`w-full flex items-center justify-between px-4 py-3 rounded-lg text-sm font-medium transition-all ${activeCategory === cat.id
                                            ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/30'
                                            : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                                        }`}
                                >
                                    <span className="flex items-center gap-3">
                                        {cat.id === 'all' && <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>}
                                        {cat.id === 'unread' && <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>}
                                        {cat.id === 'action' && <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" /></svg>}
                                        {cat.label}
                                    </span>
                                    {cat.count > 0 && (
                                        <Badge variant={cat.id === 'action' ? 'danger' : 'info'} className="text-[10px] font-black">
                                            {cat.count}
                                        </Badge>
                                    )}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div>
                        <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-4">Categories</h3>
                        <div className="space-y-1">
                            {filterCategories.map(cat => (
                                <button
                                    key={cat.id}
                                    className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all"
                                >
                                    <span className="text-lg">{cat.icon}</span>
                                    {cat.label}
                                </button>
                            ))}
                        </div>
                    </div>
                </aside>

                {/* Main Content */}
                <main className="col-span-6 space-y-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-display font-bold text-slate-900 dark:text-white">Notification Center</h1>
                            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                                You have <span className="font-bold text-blue-600">3 unread</span> urgent alerts requiring attention.
                            </p>
                        </div>
                        <button className="px-4 py-2 text-sm font-bold text-blue-600 hover:text-blue-500 transition-colors">
                            Mark All as Read
                        </button>
                    </div>

                    {/* Notifications List */}
                    <div className="space-y-4">
                        {notifications.map(notif => (
                            <Card
                                key={notif.id}
                                className={`p-0 overflow-hidden transition-all ${notif.type === 'urgent'
                                        ? 'border-l-4 border-l-red-500 bg-red-50/5 dark:bg-red-900/5'
                                        : notif.type === 'info'
                                            ? 'border-l-4 border-l-blue-500'
                                            : ''
                                    }`}
                            >
                                <div className="p-6 flex gap-4">
                                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${notif.type === 'urgent' ? 'bg-red-100 dark:bg-red-900/20 text-red-600' :
                                            notif.type === 'info' ? 'bg-blue-100 dark:bg-blue-900/20 text-blue-600' :
                                                notif.type === 'document' ? 'bg-slate-100 dark:bg-slate-800 text-slate-600' :
                                                    'bg-slate-100 dark:bg-slate-800 text-slate-500'
                                        }`}>
                                        {notif.icon === 'alert' && <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" /></svg>}
                                        {notif.icon === 'ai' && <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20"><path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" /><path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" /></svg>}
                                        {notif.icon === 'file' && <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" /></svg>}
                                        {notif.icon === 'settings' && <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>}
                                    </div>
                                    <div className="flex-1 space-y-3">
                                        <div className="flex items-start justify-between gap-4">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <h3 className="font-bold text-slate-900 dark:text-white">{notif.title}</h3>
                                                    {notif.badge && (
                                                        <Badge
                                                            variant={notif.badge === 'URGENT' ? 'danger' : 'info'}
                                                            className="text-[8px] font-black tracking-widest"
                                                        >
                                                            {notif.badge}
                                                        </Badge>
                                                    )}
                                                </div>
                                                <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                                                    {notif.author && <span className="font-bold">{notif.author} </span>}
                                                    {notif.message}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex items-center justify-between">
                                            <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">{notif.time}</span>
                                            {notif.actions.length > 0 && (
                                                <div className="flex gap-2">
                                                    {notif.actions.map((action, i) => (
                                                        <button
                                                            key={i}
                                                            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${action.variant === 'danger'
                                                                    ? 'bg-red-600 hover:bg-red-500 text-white shadow-lg shadow-red-900/30'
                                                                    : action.variant === 'primary'
                                                                        ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/30'
                                                                        : action.variant === 'secondary'
                                                                            ? 'bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300'
                                                                            : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                                                                }`}
                                                        >
                                                            {action.label}
                                                        </button>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </Card>
                        ))}
                    </div>

                    <button className="w-full py-3 text-sm font-bold text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors">
                        Load older notifications
                    </button>
                </main>

                {/* Right Sidebar - Preferences */}
                <aside className="col-span-3 space-y-6">
                    <Card className="space-y-6">
                        <div className="flex items-center gap-2">
                            <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" /></svg>
                            <h3 className="font-bold text-slate-900 dark:text-white">Preferences</h3>
                        </div>

                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-bold text-slate-900 dark:text-white">Email Digest</p>
                                    <p className="text-xs text-slate-500 dark:text-slate-400">Receive summaries via email</p>
                                </div>
                                <button className="w-12 h-6 bg-blue-600 rounded-full relative transition-all">
                                    <div className="w-5 h-5 bg-white rounded-full absolute right-0.5 top-0.5 shadow-lg"></div>
                                </button>
                            </div>

                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-bold text-slate-900 dark:text-white">Push Alerts</p>
                                    <p className="text-xs text-slate-500 dark:text-slate-400">Instant browser notifications</p>
                                </div>
                                <button className="w-12 h-6 bg-blue-600 rounded-full relative transition-all">
                                    <div className="w-5 h-5 bg-white rounded-full absolute right-0.5 top-0.5 shadow-lg"></div>
                                </button>
                            </div>

                            <div className="pt-4 border-t border-slate-100 dark:border-dark-border">
                                <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase mb-2 block">Email Frequency</label>
                                <select className="w-full bg-slate-50 dark:bg-slate-800 border-0 rounded-lg py-2 px-3 text-sm font-medium text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 transition-colors">
                                    <option>Daily Digest (8:00 AM)</option>
                                    <option>Twice Daily</option>
                                    <option>Weekly Summary</option>
                                    <option>Real-time</option>
                                </select>
                            </div>
                        </div>

                        <button className="w-full py-2 text-sm font-bold text-blue-600 hover:text-blue-500 transition-colors">
                            Manage All Settings
                        </button>
                    </Card>
                </aside>
            </div>
        </div>
    )
}
