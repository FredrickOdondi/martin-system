import { Card, Badge } from '../../components/ui'

export default function DocumentLibrary() {
    const folders = [
        { name: 'Meeting Minutes', count: 45, icon: 'folder', color: 'blue' },
        { name: 'Policy Drafts', count: 28, icon: 'folder', color: 'purple' },
        { name: 'Budget Reports', count: 12, icon: 'folder', color: 'green' },
        { name: 'Legal Documents', count: 34, icon: 'folder', color: 'orange' },
    ]

    const recentDocs = [
        { name: 'Energy_TWG_Minutes_Dec15.pdf', size: '2.4 MB', modified: '2 hours ago', owner: 'Dr. Amara Koné', type: 'pdf', status: 'confidential' },
        { name: 'Regional_Infrastructure_Budget_Q4.xlsx', size: '1.8 MB', modified: '5 hours ago', owner: 'Finance Team', type: 'excel', status: 'internal' },
        { name: 'Trade_Policy_Framework_Draft_v3.docx', size: '845 KB', modified: 'Yesterday', owner: 'Legal Affairs', type: 'word', status: 'public' },
        { name: 'Minerals_Export_Analysis_2025.pdf', size: '3.2 MB', modified: '2 days ago', owner: 'Research Unit', type: 'pdf', status: 'confidential' },
        { name: 'Digital_Economy_Roadmap_Final.pptx', size: '5.1 MB', modified: '3 days ago', owner: 'Strategy Team', type: 'ppt', status: 'internal' },
    ]

    return (
        <div className="max-w-7xl mx-auto space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-display font-bold text-slate-900 dark:text-white transition-colors">Documents</h1>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Centralized document repository for all TWGs</p>
                </div>
                <div className="flex gap-3">
                    <div className="relative">
                        <input
                            type="search"
                            placeholder="Search documents..."
                            className="w-80 pl-10 pr-4 py-2 rounded-lg border border-slate-300 dark:border-dark-border bg-white dark:bg-dark-card text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                    </div>
                    <button className="btn-primary text-sm flex items-center gap-2">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
                        Upload Document
                    </button>
                </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-4 gap-6">
                {[
                    { label: 'Total Documents', value: '1,247', change: '+45 this week' },
                    { label: 'Storage Used', value: '24.8 GB', change: '62% of quota' },
                    { label: 'Shared Files', value: '342', change: '+12 today' },
                    { label: 'Pending Review', value: '18', change: '5 urgent' },
                ].map(stat => (
                    <Card key={stat.label} className="p-6">
                        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">{stat.label}</p>
                        <p className="text-2xl font-display font-black text-slate-900 dark:text-white mb-1">{stat.value}</p>
                        <p className="text-[10px] font-bold text-green-500">{stat.change}</p>
                    </Card>
                ))}
            </div>

            {/* Folders */}
            <div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4">Folders</h2>
                <div className="grid grid-cols-4 gap-6">
                    {folders.map(folder => (
                        <Card key={folder.name} className="p-6 hover:ring-2 hover:ring-blue-500/50 transition-all cursor-pointer group">
                            <div className="flex items-start justify-between mb-4">
                                <div className={`w-12 h-12 rounded-xl bg-${folder.color}-50 dark:bg-${folder.color}-900/20 flex items-center justify-center text-${folder.color}-600 dark:text-${folder.color}-400 group-hover:scale-110 transition-transform`}>
                                    <svg className="w-7 h-7" fill="currentColor" viewBox="0 0 20 20"><path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" /></svg>
                                </div>
                            </div>
                            <h3 className="font-bold text-slate-900 dark:text-white group-hover:text-blue-600 transition-colors">{folder.name}</h3>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{folder.count} files</p>
                        </Card>
                    ))}
                </div>
            </div>

            {/* Recent Documents */}
            <div>
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-bold text-slate-900 dark:text-white">Recent Documents</h2>
                    <div className="flex gap-2">
                        <button className="text-xs font-bold text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 px-3 py-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-all">
                            Grid View
                        </button>
                        <button className="text-xs font-bold text-blue-600 px-3 py-1.5 rounded-lg bg-blue-50 dark:bg-blue-900/20">
                            List View
                        </button>
                    </div>
                </div>
                <Card className="p-0 overflow-hidden">
                    <table className="w-full text-left text-sm">
                        <thead>
                            <tr className="bg-slate-50 dark:bg-slate-800/50 text-[10px] font-black text-slate-400 uppercase tracking-widest">
                                <th className="px-6 py-4">Name</th>
                                <th className="px-6 py-4">Owner</th>
                                <th className="px-6 py-4">Size</th>
                                <th className="px-6 py-4">Modified</th>
                                <th className="px-6 py-4">Status</th>
                                <th className="px-6 py-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                            {recentDocs.map((doc, i) => (
                                <tr key={i} className="hover:bg-slate-50 dark:hover:bg-slate-800/20 transition-colors group">
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${doc.type === 'pdf' ? 'bg-red-50 text-red-600 dark:bg-red-900/20' :
                                                    doc.type === 'excel' ? 'bg-green-50 text-green-600 dark:bg-green-900/20' :
                                                        doc.type === 'word' ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/20' :
                                                            'bg-orange-50 text-orange-600 dark:bg-orange-900/20'
                                                }`}>
                                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" /></svg>
                                            </div>
                                            <span className="font-medium text-slate-900 dark:text-white group-hover:text-blue-600 transition-colors">{doc.name}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-slate-600 dark:text-slate-400">{doc.owner}</td>
                                    <td className="px-6 py-4 text-slate-600 dark:text-slate-400 font-medium">{doc.size}</td>
                                    <td className="px-6 py-4 text-slate-500 dark:text-slate-400 text-xs">{doc.modified}</td>
                                    <td className="px-6 py-4">
                                        <Badge
                                            variant={doc.status === 'confidential' ? 'danger' : doc.status === 'internal' ? 'warning' : 'success'}
                                            className="uppercase text-[8px] font-black tracking-widest"
                                        >
                                            {doc.status}
                                        </Badge>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <button className="p-2 text-slate-400 hover:text-blue-600 transition-colors">
                                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" /></svg>
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </Card>
            </div>
        </div>
    )
}
