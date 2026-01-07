import { useState, useEffect } from 'react'
import { Card, Badge } from '../../components/ui'
import { meetings } from '../../services/api'
import MeetingDetail from './MeetingDetail'
import ModernLayout from '../../layouts/ModernLayout'

export default function SummitSchedule() {
    const [events, setEvents] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [selectedMeetingId, setSelectedMeetingId] = useState<string | null>(null)

    useEffect(() => {
        loadMeetings()
    }, [])

    const loadMeetings = async () => {
        try {
            const response = await meetings.list()
            const meetingData = response.data.map((m: any) => ({
                id: m.id,
                title: m.title,
                location: m.location || 'Virtual',
                scheduled_at: new Date(m.scheduled_at),
                duration: `${m.duration_minutes}m`,
                type: 'twg', // Defaulting for now, backend has this on TWG relationship
                attendees: m.participants.length,
                status: m.status
            }))

            // Sort by date
            meetingData.sort((a: any, b: any) => a.scheduled_at.getTime() - b.scheduled_at.getTime())

            setEvents(meetingData)
        } catch (error) {
            console.error("Failed to load meetings", error)
        } finally {
            setLoading(false)
        }
    }

    // Helper to group by date string for the UI
    const groupedEvents = events.reduce((acc: any, event: any) => {
        const dateStr = event.scheduled_at.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
        if (!acc[dateStr]) acc[dateStr] = []
        acc[dateStr].push(event)
        return acc
    }, {})


    if (loading) {
        return (
            <ModernLayout>
                <div className="flex h-[50vh] items-center justify-center">
                    <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                </div>
            </ModernLayout>
        )
    }

    return (
        <ModernLayout>
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
                    {events.length === 0 ? (
                        <div className="text-center py-20 bg-slate-50 dark:bg-slate-800/50 rounded-2xl border border-dashed border-slate-300 dark:border-slate-700">
                            <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                            </div>
                            <h3 className="text-lg font-bold text-slate-900 dark:text-white">No Sessions Scheduled</h3>
                            <p className="text-slate-500 max-w-sm mx-auto mt-2">There are currently no meetings scheduled for this summit. Create one via the API or wait for the Secretariat to publish the schedule.</p>
                        </div>
                    ) : (
                        Object.keys(groupedEvents).map(date => {
                            const dayEvents = groupedEvents[date]

                            return (
                                <div key={date} className="space-y-4">
                                    <div className="flex items-center gap-4">
                                        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-600 to-blue-800 flex flex-col items-center justify-center text-white shadow-xl shadow-blue-900/30">
                                            <span className="text-xs font-bold opacity-80">{dayEvents[0].scheduled_at.toLocaleDateString('en-US', { weekday: 'short' })}</span>
                                            <span className="text-3xl font-display font-black">{date.split(' ')[1]}</span>
                                        </div>
                                        <div>
                                            <h2 className="text-xl font-bold text-slate-900 dark:text-white">{dayEvents[0].scheduled_at.toLocaleDateString('en-US', { weekday: 'long' })}, {date}</h2>
                                            <p className="text-sm text-slate-500 dark:text-slate-400">{dayEvents.length} sessions scheduled</p>
                                        </div>
                                    </div>

                                    <div className="ml-24 space-y-4">
                                        {dayEvents.map((event: any, i: number) => (
                                            <div key={i} onClick={() => setSelectedMeetingId(event.id)}>
                                                <Card className="p-6 hover:ring-2 hover:ring-blue-500/30 transition-all cursor-pointer group">
                                                    <div className="flex gap-6">
                                                        <div className="flex flex-col items-center w-20 shrink-0">
                                                            <span className="text-sm font-black text-slate-900 dark:text-white">
                                                                {event.scheduled_at.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                                                            </span>
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
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )
                        }))}
                </div>
                {selectedMeetingId && (
                    <MeetingDetail
                        meetingId={selectedMeetingId}
                        onClose={() => setSelectedMeetingId(null)}
                    />
                )}
            </div>
        </ModernLayout>
    )
}
