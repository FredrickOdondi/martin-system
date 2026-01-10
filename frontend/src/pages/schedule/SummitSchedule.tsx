import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { meetings } from '../../services/api'
import {
    format,
    startOfMonth,
    endOfMonth,
    startOfWeek,
    endOfWeek,
    eachDayOfInterval,
    isSameMonth,
    isSameDay,
    addMonths,
    subMonths,
    isToday
} from 'date-fns'

export default function SummitSchedule() {
    const navigate = useNavigate()
    const [events, setEvents] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [currentDate, setCurrentDate] = useState(new Date())

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
                duration: m.duration_minutes,
                type: m.meeting_type === 'virtual' ? 'virtual' : 'in_person',
                attendees: m.participants.length,
                status: m.status
            }))
            setEvents(meetingData)
        } catch (error) {
            console.error("Failed to load meetings", error)
        } finally {
            setLoading(false)
        }
    }

    // Calendar Generation Logic
    const monthStart = startOfMonth(currentDate)
    const monthEnd = endOfMonth(monthStart)
    const startDate = startOfWeek(monthStart)
    const endDate = endOfWeek(monthEnd)
    const calendarDays = eachDayOfInterval({ start: startDate, end: endDate })

    const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

    const nextMonth = () => setCurrentDate(addMonths(currentDate, 1))
    const prevMonth = () => setCurrentDate(subMonths(currentDate, 1))
    const resetDate = () => setCurrentDate(new Date())

    const getEventsForDay = (day: Date) => {
        return events.filter(event => isSameDay(event.scheduled_at, day))
            .sort((a, b) => a.scheduled_at.getTime() - b.scheduled_at.getTime())
    }

    if (loading) {
        return (
            <div className="flex h-[50vh] items-center justify-center">
                <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            </div>
        )
    }

    return (
        <div className="max-w-7xl mx-auto space-y-6 h-[calc(100vh-100px)] flex flex-col">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 shrink-0">
                <div>
                    <h1 className="text-3xl font-display font-bold text-slate-900 dark:text-white transition-colors">Summit Schedule</h1>
                    <p className="text-sm text-slate-500 dark:text-slate-400">ECOWAS Economic Development Summit 2026 • Abuja, Nigeria</p>
                </div>

                <div className="flex items-center gap-4 bg-white dark:bg-slate-900 p-1.5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                    <div className="flex items-center gap-1">
                        <button onClick={prevMonth} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-500">
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
                        </button>
                        <button onClick={resetDate} className="text-lg font-bold w-40 text-center text-slate-900 dark:text-white">
                            {format(currentDate, 'MMMM yyyy')}
                        </button>
                        <button onClick={nextMonth} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-500">
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                        </button>
                    </div>
                    <div className="h-6 w-px bg-slate-200 dark:bg-slate-700 mx-2" />
                    <button className="btn-primary text-sm whitespace-nowrap px-4 py-2 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 transition" onClick={loadMeetings}>
                        Refresh
                    </button>
                </div>
            </div>

            {/* Calendar Grid */}
            <div className="flex-1 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xl overflow-hidden flex flex-col">
                {/* Weekday Headers */}
                <div className="grid grid-cols-7 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
                    {weekDays.map(day => (
                        <div key={day} className="py-3 text-center text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                            {day}
                        </div>
                    ))}
                </div>

                {/* Days Grid */}
                <div className="grid grid-cols-7 flex-1 auto-rows-[1fr]">
                    {calendarDays.map((day, idx) => {
                        const dayEvents = getEventsForDay(day)
                        const isCurrentMonth = isSameMonth(day, monthStart)
                        const isTodayDate = isToday(day)

                        return (
                            <div
                                key={day.toString()}
                                className={`
                                    border-b border-r border-slate-100 dark:border-slate-800/50 p-2 min-h-[120px] relative group flex flex-col
                                    ${!isCurrentMonth ? 'bg-slate-50/50 dark:bg-slate-900/50 text-slate-300 dark:text-slate-700' : 'bg-white dark:bg-slate-900'}
                                    ${isTodayDate ? 'bg-blue-50/50 dark:bg-blue-900/10' : ''}
                                `}
                            >
                                <div className="flex justify-between items-start mb-2 shrink-0">
                                    <span className={`
                                        text-sm font-bold w-7 h-7 flex items-center justify-center rounded-full
                                        ${isTodayDate ? 'bg-blue-600 text-white shadow-md' : 'text-slate-700 dark:text-slate-300'}
                                        ${!isCurrentMonth ? 'opacity-30' : ''}
                                    `}>
                                        {format(day, 'd')}
                                    </span>
                                    {dayEvents.length > 0 && (
                                        <span className="text-[10px] font-bold text-slate-400">{dayEvents.length}</span>
                                    )}
                                </div>

                                <div className="space-y-1 overflow-y-auto max-h-[100px] scrollbar-hide flex-1">
                                    {dayEvents.map(event => (
                                        <div
                                            key={event.id}
                                            onClick={() => navigate(`/meetings/${event.id}`)}
                                            className={`
                                                px-2 py-1.5 rounded-md text-xs cursor-pointer transition-all border group/event
                                                ${event.type === 'virtual'
                                                    ? 'bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 border-purple-100 dark:border-purple-800 hover:bg-purple-100 dark:hover:bg-purple-900/40'
                                                    : 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 border-blue-100 dark:border-blue-800 hover:bg-blue-100 dark:hover:bg-blue-900/40'}
                                            `}
                                        >
                                            <div className="font-bold truncate">{event.title}</div>
                                            <div className="flex items-center justify-between opacity-75 mt-0.5 text-[10px]">
                                                <span>{format(event.scheduled_at, 'HH:mm')}</span>
                                                {event.type === 'virtual' && <span>📹</span>}
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                {/* Add Button Placeholder on Hover */}
                                <div className="absolute inset-x-0 bottom-0 h-1 bg-gradient-to-r from-transparent via-blue-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                            </div>
                        )
                    })}
                </div>
            </div>
        </div>
    )
}
