import { useNavigate } from 'react-router-dom';
import { TimelineItem } from '../../services/dashboardService';

interface LiveTimelineProps {
    items: TimelineItem[];
}

export default function LiveTimeline({ items }: LiveTimelineProps) {
    const navigate = useNavigate();

    // Group items by date
    // Sort items by date first just in case
    const sortedItems = [...items].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    // Grouping structure: { "2024-01-21": [item1, item2], ... }
    const groupedItems: { [key: string]: TimelineItem[] } = {};

    sortedItems.forEach(item => {
        const dateObj = new Date(item.date);
        const dateKey = dateObj.toISOString().split('T')[0]; // YYYY-MM-DD for stable keys
        if (!groupedItems[dateKey]) {
            groupedItems[dateKey] = [];
        }
        groupedItems[dateKey].push(item);
    });

    const getMonthDay = (dateStr: string) => {
        const date = new Date(dateStr);
        return {
            month: date.toLocaleString('en-US', { month: 'short' }).toUpperCase(),
            day: date.getDate()
        };
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'critical': return 'bg-red-500';
            case 'completed': return 'bg-emerald-500';
            case 'warning': return 'bg-amber-500';
            default: return 'bg-blue-500';
        }
    };

    return (
        <div className="bg-[#f6f8fa] dark:bg-[#1a202c] rounded-3xl p-6 h-full flex flex-col shadow-sm border border-[#eef0f2] dark:border-[#2d3748]">
            <style>{`
                .no-scrollbar::-webkit-scrollbar {
                    display: none;
                }
                .no-scrollbar {
                    -ms-overflow-style: none;
                    scrollbar-width: none;
                }
            `}</style>

            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <h3 className="text-xl font-bold text-[#1e293b] dark:text-white tracking-tight">Live Timeline</h3>
                <span className="material-symbols-outlined text-blue-500 text-2xl">schedule</span>
            </div>

            {/* Timeline Content */}
            <div className="flex-1 overflow-y-auto no-scrollbar pr-1">
                {Object.entries(groupedItems).length > 0 ? (
                    Object.entries(groupedItems).map(([dateKey, dayItems]) => {
                        const { month, day } = getMonthDay(dateKey);
                        return (
                            <div key={dateKey} className="mb-8 last:mb-0">
                                {/* Date Header with Line */}
                                <div className="flex items-end gap-4 mb-4">
                                    <div className="flex flex-col leading-none">
                                        <span className="text-[10px] font-bold text-blue-600 dark:text-blue-400 uppercase mb-1">{month}</span>
                                        <span className="text-2xl font-bold text-[#0f172a] dark:text-white">{day}</span>
                                    </div>
                                    <div className="h-px bg-[#e2e8f0] dark:bg-[#2d3748] flex-1 mb-2"></div>
                                </div>

                                {/* Events List */}
                                <div className="space-y-6 pl-2">
                                    {dayItems.map((item, idx) => (
                                        <div key={`${dateKey}-${idx}`} className="flex justify-between items-start group cursor-pointer">
                                            <div className="flex-1 pr-4">
                                                <h4 className="font-bold text-[#0f172a] dark:text-white text-[15px] mb-0.5 group-hover:text-blue-600 transition-colors">{item.title}</h4>
                                                <p className="text-sm text-[#64748b] dark:text-[#94a3b8]">{item.twg}</p>
                                            </div>
                                            {/* Status Dot */}
                                            <div className="pt-2">
                                                <div className={`size-2.5 rounded-full ${getStatusColor(item.status)} ring-4 ring-transparent group-hover:ring-blue-50 dark:group-hover:ring-blue-900/20 transition-all`}></div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        );
                    })
                ) : (
                    <div className="text-center py-12">
                        <p className="text-[#64748b] text-sm">No scheduled events.</p>
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="mt-6 pt-4">
                <button
                    onClick={() => navigate('/schedule')}
                    className="w-full py-3.5 bg-[#f1f5f9] dark:bg-[#2d3748] rounded-xl text-sm font-semibold text-[#0f172a] dark:text-white hover:bg-[#e2e8f0] dark:hover:bg-[#4a5568] transition-colors"
                >
                    View All Events
                </button>
            </div>
        </div>
    );
}
