import { Card, Badge } from '../../components/ui'

export default function SummitSchedule() {
    const events = [
        { date: 'Dec 15', day: 'Mon', time: '09:00 AM', duration: '2h', title: 'Opening Ceremony & Keynote Address', location: 'Main Hall A', attendees: 450, type: 'plenary', status: 'upcoming' },
        { date: 'Dec 15', day: 'Mon', time: '11:30 AM', duration: '1h 30m', title: 'Energy TWG: Regional Power Grid Integration', location: 'Conference Room 3', attendees: 45, type: 'twg', status: 'upcoming' },
        { date: 'Dec 15', day: 'Mon', time: '02:00 PM', duration: '2h', title: 'Minerals TWG: Critical Resources Framework', location: 'Conference Room 1', attendees: 38, type: 'twg', status: 'upcoming' },
        { date: 'Dec 16', day: 'Tue', time: '09:00 AM', duration: '3h', title: 'Infrastructure Investment Roundtable', location: 'Main Hall B', attendees: 120, type: 'roundtable', status: 'upcoming' },
        { date: 'Dec 16', day: 'Tue', time: '02:30 PM', duration: '1h 45m', title: 'Digital Economy TWG: Cross-Border Data Policy', location: 'Conference Room 2', attendees: 52, type: 'twg', status: 'upcoming' },
    ]

    return (
        <div className="max-w-6xl mx-auto space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-display font-bold text-slate-900 dark:text-white transition-colors">Summit Schedule</h1>
                    <p className="text-sm text-slate-500 dark:text-slate-400">ECOWAS Economic Development Summit 2026 • Abuja, Nigeria</p>
                </div>
                <div className="flex gap-3">
                    <button className="btn-secondary text-sm flex items-center gap-2">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" /></svg>
                        Filter
                    </button>
                    <button className="btn-primary text-sm flex items-center gap-2">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                        Export Calendar
                    </button>
                </div>
            </div>

            {/* Week View Tabs */}
            <div className="flex gap-2 border-b border-slate-200 dark:border-dark-border pb-4">
                {['Week 1', 'Week 2', 'Week 3'].map((week, i) => (
                    <button key={week} className={`px-6 py-2 rounded-t-lg text-sm font-bold transition-all ${i === 0 ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/20' : 'bg-slate-100 dark:bg-slate-800 text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-700'}`}>
                        {week}
                    </button>
                ))}
            </div>

            {/* Timeline */}
            <div className="space-y-8">
                {['Dec 15', 'Dec 16'].map(date => {
                    const dayEvents = events.filter(e => e.date === date)
                    return (
                        <div key={date} className="space-y-4">
                            <div className="flex items-center gap-4">
                                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-600 to-blue-800 flex flex-col items-center justify-center text-white shadow-xl shadow-blue-900/30">
                                    <span className="text-xs font-bold opacity-80">{dayEvents[0].day}</span>
                                    <span className="text-3xl font-display font-black">{date.split(' ')[1]}</span>
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">{dayEvents[0].day}, December {date.split(' ')[1]}</h2>
                                    <p className="text-sm text-slate-500 dark:text-slate-400">{dayEvents.length} sessions scheduled</p>
                                </div>
                            </div>

                            <div className="ml-24 space-y-4">
                                {dayEvents.map((event, i) => (
                                    <Card key={i} className="p-6 hover:ring-2 hover:ring-blue-500/30 transition-all cursor-pointer group">
                                        <div className="flex gap-6">
                                            <div className="flex flex-col items-center w-20 shrink-0">
                                                <span className="text-sm font-black text-slate-900 dark:text-white">{event.time}</span>
                                                <span className="text-[10px] font-bold text-slate-400 uppercase mt-1">{event.duration}</span>
                                            </div>
                                            <div className="flex-1 space-y-3">
                                                <div className="flex items-start justify-between gap-4">
                                                    <div className="flex-1">
                                                        <h3 className="text-lg font-bold text-slate-900 dark:text-white group-hover:text-blue-600 transition-colors">{event.title}</h3>
                                                        <div className="flex items-center gap-4 mt-2 text-xs text-slate-500 dark:text-slate-400">
                                                            <span className="flex items-center gap-1.5">
                                                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                                                                {event.location}
                                                            </span>
                                                            <span className="flex items-center gap-1.5">
                                                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
                                                                {event.attendees} attendees
                                                            </span>
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center gap-3">
                                                        <Badge
                                                            variant={event.type === 'plenary' ? 'info' : event.type === 'twg' ? 'warning' : 'neutral'}
                                                            className="uppercase text-[9px] font-black tracking-widest"
                                                        >
                                                            {event.type}
                                                        </Badge>
                                                        <button className="p-2 bg-slate-100 dark:bg-slate-800 rounded-lg text-slate-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all">
                                                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </Card>
                                ))}
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
