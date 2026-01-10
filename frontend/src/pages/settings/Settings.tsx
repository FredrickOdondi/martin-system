

export default function Settings() {
    return (
        <>
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="font-bold text-[#0d121b] dark:text-white text-3xl">System Integrations & Configuration</h1>
                    <p className="text-sm text-[#4c669a] mt-1">Manage external connections, security protocols, and AI parameters.</p>
                </div>
                <div className="flex items-center gap-3">
                    <button className="px-4 py-2 text-sm font-medium text-[#4c669a] hover:text-[#0d121b] dark:text-[#a0aec0] dark:hover:text-white transition-colors">
                        Discard Changes
                    </button>
                    <button className="px-4 py-2 bg-[#1152d4] text-white text-sm font-bold rounded-lg hover:bg-blue-700 transition-colors shadow-sm flex items-center gap-2">
                        <span className="material-symbols-outlined text-[18px]">save</span>
                        Save Changes
                    </button>
                </div>
            </div>

            <div className="space-y-8">
                {/* External Integrations Section */}
                <section>
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-base font-bold text-[#0d121b] dark:text-white flex items-center gap-2">
                            <span className="material-symbols-outlined text-[#1152d4]">hub</span>
                            External Integrations
                        </h3>
                        <span className="text-xs bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 px-2 py-1 rounded font-bold uppercase">All Systems Operational</span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-white dark:bg-[#1a202c] border border-[#e7ebf3] dark:border-[#2d3748] rounded-xl p-6 shadow-sm flex flex-col justify-between h-full">
                            <div>
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className="size-10 rounded-lg bg-orange-100 flex items-center justify-center">
                                            <span className="material-symbols-outlined text-orange-600">calendar_month</span>
                                        </div>
                                        <div>
                                            <h4 className="font-bold text-[#0d121b] dark:text-white">Calendar Services</h4>
                                            <p className="text-xs text-[#4c669a]">Google Workspace & Office 365</p>
                                        </div>
                                    </div>
                                    <div className="relative inline-block w-10 mr-2 align-middle select-none transition duration-200 ease-in">
                                        <input type="checkbox" name="toggle" id="toggle1" className="toggle-checkbox absolute block w-5 h-5 rounded-full bg-white border-4 appearance-none cursor-pointer checked:right-0 checked:border-green-400 right-5" defaultChecked />
                                        <label htmlFor="toggle1" className="toggle-label block overflow-hidden h-5 rounded-full bg-green-400 cursor-pointer"></label>
                                    </div>
                                </div>
                                <p className="text-sm text-[#4c669a] mb-4">Allows agents to check availability and schedule meetings directly on user calendars.</p>
                            </div>
                            <div className="pt-4 border-t border-[#e7ebf3] dark:border-[#2d3748] flex items-center justify-between">
                                <span className="text-xs font-medium text-green-600 dark:text-green-400 flex items-center gap-1">
                                    <span className="material-symbols-outlined text-[14px]">check_circle</span> Connected
                                </span>
                                <button className="text-sm font-medium text-[#1152d4] hover:underline">Configure Scopes</button>
                            </div>
                        </div>

                        <div className="bg-white dark:bg-[#1a202c] border border-[#e7ebf3] dark:border-[#2d3748] rounded-xl p-6 shadow-sm flex flex-col justify-between h-full">
                            <div>
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className="size-10 rounded-lg bg-blue-100 flex items-center justify-center">
                                            <span className="material-symbols-outlined text-blue-600">video_camera_front</span>
                                        </div>
                                        <div>
                                            <h4 className="font-bold text-[#0d121b] dark:text-white">Conferencing API</h4>
                                            <p className="text-xs text-[#4c669a]">Zoom & Microsoft Teams</p>
                                        </div>
                                    </div>
                                    <button className="text-xs bg-[#f0f2f5] dark:bg-[#2d3748] text-[#4c669a] dark:text-[#a0aec0] px-2 py-1 rounded hover:bg-gray-200 transition-colors">Setup</button>
                                </div>
                                <p className="text-sm text-[#4c669a] mb-4">Enable automatic generation of meeting links for agenda items.</p>
                            </div>
                            <div className="pt-4 border-t border-[#e7ebf3] dark:border-[#2d3748]">
                                <label className="text-xs font-bold text-[#4c669a] uppercase mb-1 block">API Key</label>
                                <div className="flex gap-2">
                                    <input className="flex-1 bg-[#f6f6f8] dark:bg-[#0d121b] border border-[#e7ebf3] dark:border-[#4a5568] rounded px-3 py-1.5 text-sm text-[#0d121b] dark:text-white" disabled type="password" value="************************" />
                                    <button className="text-[#1152d4] hover:text-blue-700 p-1">
                                        <span className="material-symbols-outlined text-[18px]">edit</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Security & Compliance Section */}
                <section>
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-base font-bold text-[#0d121b] dark:text-white flex items-center gap-2">
                            <span className="material-symbols-outlined text-[#1152d4]">lock</span>
                            Security & Compliance
                        </h3>
                    </div>
                    <div className="bg-white dark:bg-[#1a202c] border border-[#e7ebf3] dark:border-[#2d3748] rounded-xl shadow-sm divide-y divide-[#e7ebf3] dark:divide-[#2d3748]">
                        <div className="p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
                            <div className="flex-1">
                                <h4 className="text-sm font-bold text-[#0d121b] dark:text-white mb-1">Single Sign-On (SSO)</h4>
                                <p className="text-xs text-[#4c669a]">Require users to sign in via their organizational identity provider.</p>
                            </div>
                            <div className="flex items-center gap-4">
                                <select className="bg-[#f6f6f8] dark:bg-[#0d121b] border border-[#e7ebf3] dark:border-[#4a5568] rounded-lg text-sm px-3 py-2 text-[#0d121b] dark:text-white focus:ring-[#1152d4] focus:border-[#1152d4]">
                                    <option>Azure Active Directory</option>
                                    <option>Google Workspace</option>
                                    <option>Okta</option>
                                    <option>Disabled</option>
                                </select>
                            </div>
                        </div>
                        <div className="p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
                            <div className="flex-1">
                                <h4 className="text-sm font-bold text-[#0d121b] dark:text-white mb-1">Data Residency</h4>
                                <p className="text-xs text-[#4c669a]">Specify the geographical region where TWG data is stored and processed.</p>
                            </div>
                            <div className="w-full md:w-64">
                                <select className="w-full bg-[#f6f6f8] dark:bg-[#0d121b] border border-[#e7ebf3] dark:border-[#4a5568] rounded-lg text-sm px-3 py-2 text-[#0d121b] dark:text-white focus:ring-[#1152d4] focus:border-[#1152d4]">
                                    <option>West Africa (Lagos)</option>
                                    <option>Europe (Frankfurt)</option>
                                    <option>North America (Virginia)</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </section>

                <div className="text-center pt-8 pb-4">
                    <p className="text-xs text-[#9ca3af] dark:text-gray-500">
                        Changes to Security settings may require users to re-login. <br />
                        ECOWAS Summit TWG Support System v2.4.0
                    </p>
                </div>
            </div>

            <style>{`
                .toggle-checkbox:checked {
                    right: 0;
                    border-color: #1152d4;
                }
                .toggle-checkbox:checked + .toggle-label {
                    background-color: #1152d4;
                }
            `}</style>
        </>
    )
}
