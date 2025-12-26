import { Card, Badge, Avatar, Input } from '../../components/ui'

export default function UserProfile() {
    const tabs = ['Personal Details', 'Account Security', 'Notifications']
    const activeTab = 'Personal Details'

    return (
        <div className="max-w-5xl mx-auto space-y-8">
            <div className="flex flex-col gap-1">
                <h1 className="text-3xl font-display font-bold text-slate-900 dark:text-white transition-colors">User Profile</h1>
                <p className="text-slate-500 dark:text-slate-400">Manage your personal information, role assignments, and account security.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Avatar & Basic Info */}
                <div className="space-y-6">
                    <Card className="p-8 text-center flex flex-col items-center space-y-4">
                        <div className="relative group">
                            <Avatar size="lg" className="w-32 h-32 text-4xl" alt="Dr. Amara Koné" fallback="AK" />
                            <button className="absolute bottom-0 right-0 p-2 bg-blue-600 rounded-full text-white shadow-lg hover:bg-blue-500 transition-all border-4 border-white dark:border-dark-card">
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                                </svg>
                            </button>
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Dr. Amara Koné</h2>
                            <Badge variant="info" className="mt-1 bg-blue-900/20 text-blue-400 border-blue-500/30">TWG Facilitator</Badge>
                        </div>
                        <div className="w-full pt-4 space-y-3 text-left border-t border-slate-100 dark:border-dark-border transition-colors">
                            <div className="flex justify-between text-xs">
                                <span className="text-slate-500 font-medium">Member Since</span>
                                <span className="text-slate-900 dark:text-white font-bold">Jan 2023</span>
                            </div>
                            <div className="flex justify-between text-xs">
                                <span className="text-slate-500 font-medium">Last Login</span>
                                <span className="text-slate-900 dark:text-white font-bold">2 hours ago</span>
                            </div>
                            <div className="flex justify-between text-xs">
                                <span className="text-slate-500 font-medium">Status</span>
                                <span className="text-green-500 font-bold flex items-center gap-1.5">
                                    <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                                    Active
                                </span>
                            </div>
                        </div>
                    </Card>

                    <Card className="space-y-6">
                        <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
                            <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20"><path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" /></svg>
                            Assigned Groups
                        </h3>
                        <div className="space-y-3">
                            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-dark-border transition-colors group hover:border-blue-500/30 cursor-pointer">
                                <div className="flex items-center gap-3">
                                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                                    <span className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-blue-500 transition-colors">Digital Economy TWG</span>
                                </div>
                                <p className="text-[10px] text-slate-500 font-bold uppercase mt-1 pl-5">Role: Lead Facilitator</p>
                            </div>
                            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-dark-border transition-colors group hover:border-purple-500/30 cursor-pointer">
                                <div className="flex items-center gap-3">
                                    <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                                    <span className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-purple-500 transition-colors">Regional Security TWG</span>
                                </div>
                                <p className="text-[10px] text-slate-500 font-bold uppercase mt-1 pl-5">Role: Consultant</p>
                            </div>
                        </div>
                    </Card>
                </div>

                {/* Right Column: Content Tabs */}
                <div className="lg:col-span-2 space-y-8">
                    <Card className="p-0 overflow-hidden">
                        <div className="flex border-b border-slate-100 dark:border-dark-border bg-slate-50/50 dark:bg-slate-800/20 transition-colors">
                            {tabs.map(tab => (
                                <button
                                    key={tab}
                                    className={`px-8 py-4 text-sm font-bold transition-all relative ${tab === activeTab
                                        ? 'text-blue-600 dark:text-blue-400'
                                        : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                                        }`}
                                >
                                    {tab}
                                    {tab === activeTab && (
                                        <div className="absolute bottom-0 left-0 w-full h-0.5 bg-blue-600 dark:bg-blue-400"></div>
                                    )}
                                </button>
                            ))}
                        </div>
                        <div className="p-8 space-y-8">
                            <div className="grid grid-cols-2 gap-6">
                                <Input label="First Name" defaultValue="Amara" icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>} />
                                <Input label="Last Name" defaultValue="Koné" icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>} />
                                <Input label="Email Address" defaultValue="amara.kone@ecowas.int" icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>} />
                                <Input label="Phone Number" defaultValue="+234 803 123 4567" icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" /></svg>} />
                            </div>
                            <Input label="Department / Ministry" defaultValue="Department of Telecommunications & Information Technology" icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>} />

                            <div className="space-y-2">
                                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Professional Bio</label>
                                <textarea
                                    className="w-full bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-dark-border rounded-xl p-4 text-sm text-slate-600 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all min-h-[120px]"
                                    defaultValue="Lead strategist for digital implementation across member states. Focused on harmonizing telecommunications policies and fostering cross-border connectivity."
                                />
                            </div>

                            <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-dark-border transition-colors">
                                <button className="btn-secondary">Cancel</button>
                                <button className="btn-primary flex items-center gap-2">
                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 002-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" /></svg>
                                    Save Changes
                                </button>
                            </div>
                        </div>
                    </Card>

                    <Card className="p-8 flex items-center justify-between">
                        <div>
                            <h3 className="font-bold text-slate-900 dark:text-white">Sign-in Method</h3>
                            <p className="text-xs text-slate-500 dark:text-slate-400">Manage your password and 2FA settings</p>
                        </div>
                        <button className="text-sm font-bold text-blue-600 hover:text-blue-500 transition-colors">Edit Security Settings</button>
                    </Card>
                </div>
            </div>
        </div>
    )
}
