import { useState } from 'react'
import { Card, Badge } from '../../components/ui'

export default function Integrations() {
    const [integrations] = useState([
        { id: 'calendar', name: 'Calendar Services', provider: 'Google Workspace & Office 365', status: 'Connected', connected: true, description: 'Allows agents to check availability and schedule meetings directly on user calendars.' },
        { id: 'conferencing', name: 'Conferencing API', provider: 'Zoom & Microsoft Teams', status: 'Setup', connected: false, description: 'Enable automatic generation of meeting links for agenda items.' },
    ])

    return (
        <div className="flex h-full gap-8">
            {/* Settings Navigation */}
            <aside className="w-64 flex flex-col gap-8 flex-shrink-0">
                <div className="space-y-4">
                    <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-2">Global Configuration</h3>
                    <nav className="space-y-1">
                        {['General', 'Users & Permissions', 'Integrations & System', 'Security & Data', 'AI Agent Behavior', 'Templates'].map((item) => (
                            <button
                                key={item}
                                className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-colors ${item === 'Integrations & System' ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'}`}
                            >
                                {item}
                            </button>
                        ))}
                    </nav>
                </div>

                <div className="space-y-4">
                    <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-2">System Health</h3>
                    <nav className="space-y-1">
                        {['Audit Logs', 'API Usage'].map((item) => (
                            <button
                                key={item}
                                className="w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                            >
                                {item}
                            </button>
                        ))}
                    </nav>
                </div>

                <div className="mt-auto p-4 bg-blue-50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-900/20 rounded-xl">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="w-5 h-5 bg-blue-100 dark:bg-blue-900/40 rounded flex items-center justify-center text-blue-600">
                            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" /></svg>
                        </div>
                        <span className="text-[10px] font-bold text-blue-600 uppercase">v2.4.0 currently installed</span>
                    </div>
                    <button className="text-[10px] text-blue-500 hover:underline">View Changelog</button>
                </div>
            </aside>

            {/* Main Settings Area */}
            <div className="flex-1 space-y-6">
                <div className="flex items-center justify-between border-b border-slate-100 dark:border-dark-border pb-4 transition-colors">
                    <div>
                        <h1 className="text-xl font-display font-bold text-slate-900 dark:text-white transition-colors">System Integrations & Configuration</h1>
                        <p className="text-sm text-slate-500 dark:text-slate-400">Manage external connections, security protocols, and AI parameters.</p>
                    </div>
                    <div className="flex gap-3">
                        <button className="btn-secondary text-sm">Discard Changes</button>
                        <button className="btn-primary text-sm flex items-center gap-2">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V3" /></svg>
                            Save Changes
                        </button>
                    </div>
                </div>

                {/* External Integrations */}
                <section className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-sm font-bold text-slate-800 dark:text-white transition-colors flex items-center gap-2">
                            <svg className="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.826a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
                            External Integrations
                        </h2>
                        <Badge variant="success" size="sm" className="font-bold tracking-wider">ALL SYSTEMS OPERATIONAL</Badge>
                    </div>

                    <div className="grid grid-cols-2 gap-6">
                        {integrations.map((item) => (
                            <Card key={item.id} className="space-y-4">
                                <div className="flex justify-between">
                                    <div className="flex gap-4">
                                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${item.id === 'calendar' ? 'bg-orange-50 text-orange-600' : 'bg-blue-50 text-blue-600'}`}>
                                            {item.id === 'calendar' ? (
                                                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                            ) : (
                                                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                                            )}
                                        </div>
                                        <div>
                                            <h4 className="font-bold text-slate-900 dark:text-white transition-colors">{item.name}</h4>
                                            <p className="text-xs text-slate-500">{item.provider}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs text-slate-400 font-medium">{item.status}</span>
                                        <div className={`w-10 h-5 rounded-full relative transition-colors ${item.connected ? 'bg-blue-600' : 'bg-slate-200 dark:bg-slate-700'}`}>
                                            <div className={`absolute top-1 w-3 h-3 bg-white rounded-full transition-all ${item.connected ? 'left-6' : 'left-1'}`}></div>
                                        </div>
                                    </div>
                                </div>
                                <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed transition-colors">
                                    {item.description}
                                </p>
                                <div className="pt-4 border-t border-slate-50 dark:border-slate-800 transition-colors flex items-center justify-between">
                                    {item.connected ? (
                                        <>
                                            <div className="flex items-center gap-1.5 text-[10px] font-bold text-green-600 uppercase">
                                                <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
                                                Connected
                                            </div>
                                            <button className="text-xs font-bold text-blue-600 hover:text-blue-700">Configure Scopes</button>
                                        </>
                                    ) : (
                                        <div className="w-full flex items-center gap-4">
                                            <div className="flex-1 bg-slate-50 dark:bg-slate-800 rounded-lg px-3 py-1.5 flex items-center gap-2">
                                                <span className="text-[10px] font-bold text-slate-400 uppercase">API KEY</span>
                                                <input type="password" value="••••••••••••••••" readOnly className="flex-1 bg-transparent text-xs text-slate-900 dark:text-white outline-none cursor-default" />
                                                <button className="text-slate-400 hover:text-slate-600 transition-colors">
                                                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                                                </button>
                                            </div>
                                            <button className="text-xs font-bold text-blue-600 hover:text-blue-700">Setup</button>
                                        </div>
                                    )}
                                </div>
                            </Card>
                        ))}
                    </div>
                </section>

                {/* Security & Compliance */}
                <section className="space-y-4">
                    <h2 className="text-sm font-bold text-slate-800 dark:text-white transition-colors flex items-center gap-2">
                        <svg className="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 00-2 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
                        Security & Compliance
                    </h2>
                    <Card className="p-0 overflow-hidden divide-y divide-slate-100 dark:divide-slate-800 transition-colors">
                        <div className="p-6 flex items-center justify-between">
                            <div>
                                <h4 className="font-bold text-sm text-slate-900 dark:text-white transition-colors">Single Sign-On (SSO)</h4>
                                <p className="text-xs text-slate-500 mt-1 transition-colors">Require users to sign in via their organizational identity provider.</p>
                            </div>
                            <div className="flex items-center gap-4">
                                <span className="text-xs text-slate-400 transition-colors">Azure Active Directory</span>
                                <button className="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 rounded-lg text-xs font-bold text-slate-600 dark:text-slate-400 transition-colors">Configure</button>
                            </div>
                        </div>
                        <div className="p-6 flex items-center justify-between">
                            <div>
                                <h4 className="font-bold text-sm text-slate-900 dark:text-white transition-colors">Data Residency</h4>
                                <p className="text-xs text-slate-500 mt-1 transition-colors">Specify the geographical region where TWG data is stored and processed.</p>
                            </div>
                            <div className="relative">
                                <select className="appearance-none bg-slate-50 dark:bg-slate-800 border-0 rounded-lg pl-8 pr-10 py-2 text-xs font-bold text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-500 transition-all">
                                    <option>West Africa (Lagos)</option>
                                    <option>Europe (Frankfurt)</option>
                                </select>
                                <svg className="absolute left-2.5 top-2.5 w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                <svg className="absolute right-3 top-3 w-3 h-3 text-slate-400 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                            </div>
                        </div>
                        <div className="p-6 flex items-center justify-between">
                            <div>
                                <h4 className="font-bold text-sm text-slate-900 dark:text-white transition-colors">Enforce Two-Factor Authentication</h4>
                                <p className="text-xs text-slate-500 mt-1 transition-colors">Mandatory 2FA for all users with Administrator privileges.</p>
                            </div>
                            <div className="w-10 h-5 bg-slate-200 dark:bg-slate-700 rounded-full relative transition-colors">
                                <div className="absolute top-1 left-1 w-3 h-3 bg-white rounded-full transition-all"></div>
                            </div>
                        </div>
                    </Card>
                </section>

                {/* AI Agent Behaviors */}
                <section className="space-y-4">
                    <h2 className="text-sm font-bold text-slate-800 dark:text-white transition-colors flex items-center gap-2">
                        <svg className="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
                        AI Agent Behaviors
                    </h2>
                    <Card className="p-6 space-y-4 transition-colors">
                        <div>
                            <h4 className="font-bold text-sm text-slate-900 dark:text-white transition-colors">Knowledge Base Access</h4>
                            <p className="text-xs text-slate-500 mt-1 transition-colors">Define which document repositories the AI agents can access to generate answers.</p>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            {[
                                { name: 'Official Protocols (PDF)', checked: true },
                                { name: 'Meeting Minutes Archive', checked: true },
                                { name: 'Draft/Unpublished Documents', checked: false },
                                { name: 'Member Contact Details', checked: false },
                            ].map((repo) => (
                                <div key={repo.name} className={`flex items-center gap-3 p-3 rounded-lg border transition-all cursor-pointer ${repo.checked ? 'bg-blue-50/50 dark:bg-blue-900/10 border-blue-200 dark:border-blue-900/30' : 'border-slate-100 dark:border-slate-800'}`}>
                                    <div className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${repo.checked ? 'bg-blue-600 border-blue-600' : 'bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700'}`}>
                                        {repo.checked && <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
                                    </div>
                                    <span className={`text-xs font-medium transition-colors ${repo.checked ? 'text-slate-900 dark:text-white' : 'text-slate-500'}`}>{repo.name}</span>
                                </div>
                            ))}
                        </div>
                    </Card>
                </section>
            </div>
        </div>
    )
}
