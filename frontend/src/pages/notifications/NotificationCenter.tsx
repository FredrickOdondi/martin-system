import ModernLayout from '../../layouts/ModernLayout';

export default function NotificationCenter() {
    return (
        <ModernLayout>
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-black text-[#0d121b] dark:text-white tracking-tight">Notification Center</h1>
                    <p className="text-[#4c669a] dark:text-[#a0aec0] font-medium">Stay updated on TWG progress, mentions, and system alerts.</p>
                </div>
                <div className="flex gap-3">
                    <button className="px-4 py-2 text-sm font-bold text-[#4c669a] hover:text-[#0d121b] dark:hover:text-white transition-colors">
                        Mark all as read
                    </button>
                    <button className="px-4 py-2 bg-white dark:bg-[#1a202c] border border-[#e7ebf3] dark:border-[#2d3748] rounded-lg text-sm font-bold text-[#0d121b] dark:text-white hover:bg-gray-50 dark:hover:bg-[#2d3748] transition-colors shadow-sm">
                        Refresh
                    </button>
                </div>
            </div>

            <div className="bg-white dark:bg-[#1a202c] rounded-xl border border-[#e7ebf3] dark:border-[#2d3748] shadow-sm overflow-hidden">
                {/* Notification Tabs */}
                <div className="flex border-b border-[#e7ebf3] dark:border-[#2d3748] px-6">
                    <button className="px-4 py-4 text-sm font-bold text-[#1152d4] border-b-2 border-[#1152d4]">
                        Inbox <span className="ml-1 bg-red-100 text-red-600 px-1.5 py-0.5 rounded-full text-[10px]">3</span>
                    </button>
                    <button className="px-4 py-4 text-sm font-medium text-[#4c669a] hover:text-[#0d121b] dark:hover:text-white transition-colors">
                        Archived
                    </button>
                </div>

                {/* Notification List */}
                <div className="divide-y divide-[#e7ebf3] dark:divide-[#2d3748]">
                    {/* Notification 1 */}
                    <div className="p-6 flex gap-4 hover:bg-gray-50 dark:hover:bg-[#2d3748]/30 transition-colors group cursor-pointer">
                        <div className="size-10 rounded-full bg-blue-100 flex items-center justify-center text-[#1152d4] shrink-0">
                            <span className="material-symbols-outlined">description</span>
                        </div>
                        <div className="flex-1">
                            <div className="flex items-start justify-between mb-1">
                                <h4 className="text-sm font-bold text-[#0d121b] dark:text-white">New Document Shared</h4>
                                <span className="text-[10px] text-[#4c669a]">10 mins ago</span>
                            </div>
                            <p className="text-sm text-[#4c669a] dark:text-[#a0aec0]">Sarah Oladipo shared <span className="text-[#1152d4] font-medium">Trade_Customs_Draft_v2.pdf</span> in the Trade & Customs TWG.</p>
                            <div className="mt-3 flex gap-2">
                                <button className="px-3 py-1 bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400 text-xs font-bold rounded hover:bg-blue-100 transition-colors">Review Draft</button>
                            </div>
                        </div>
                        <div className="size-2 rounded-full bg-[#1152d4] mt-2"></div>
                    </div>

                    {/* Notification 2 */}
                    <div className="p-6 flex gap-4 hover:bg-gray-50 dark:hover:bg-[#2d3748]/30 transition-colors group cursor-pointer">
                        <div className="size-10 rounded-full bg-amber-100 flex items-center justify-center text-amber-600 shrink-0">
                            <span className="material-symbols-outlined">warning</span>
                        </div>
                        <div className="flex-1">
                            <div className="flex items-start justify-between mb-1">
                                <h4 className="text-sm font-bold text-[#0d121b] dark:text-white">Deadline Approaching</h4>
                                <span className="text-[10px] text-[#4c669a]">2 hours ago</span>
                            </div>
                            <p className="text-sm text-[#4c669a] dark:text-[#a0aec0]">Regional Security TWG: Annex B signature deadline starts in 24 hours.</p>
                        </div>
                        <div className="size-2 rounded-full bg-[#1152d4] mt-2"></div>
                    </div>

                    {/* Notification 3 */}
                    <div className="p-6 flex gap-4 hover:bg-gray-50 dark:hover:bg-[#2d3748]/30 transition-colors group cursor-pointer opacity-70">
                        <div className="size-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 shrink-0">
                            <span className="material-symbols-outlined">task_alt</span>
                        </div>
                        <div className="flex-1">
                            <div className="flex items-start justify-between mb-1">
                                <h4 className="text-sm font-bold text-[#0d121b] dark:text-white">Task Completed</h4>
                                <span className="text-[10px] text-[#4c669a]">Yesterday at 4:32 PM</span>
                            </div>
                            <p className="text-sm text-[#4c669a] dark:text-[#a0aec0]">AI Agent successfully initialized meeting invites for the Plenary session.</p>
                        </div>
                    </div>
                </div>

                <div className="p-4 bg-gray-50 dark:bg-[#1a202c] border-t border-[#e7ebf3] dark:border-[#2d3748] text-center">
                    <button className="text-xs font-bold text-[#1152d4] hover:underline uppercase tracking-wider">Load More Notifications</button>
                </div>
            </div>
        </ModernLayout>
    )
}
