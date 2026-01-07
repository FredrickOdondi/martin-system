import { useState, useEffect } from 'react'
import { meetings } from '../../services/api'
import { Card, Badge } from '../../components/ui'

interface MeetingDetailProps {
    meetingId: string
    onClose: () => void
}

export default function MeetingDetail({ meetingId, onClose }: MeetingDetailProps) {
    const [meeting, setMeeting] = useState<any>(null)
    const [activeTab, setActiveTab] = useState<'agenda' | 'participants'>('agenda')
    const [loading, setLoading] = useState(true)

    // Agenda State
    const [agendaContent, setAgendaContent] = useState('')
    const [isEditingAgenda, setIsEditingAgenda] = useState(false)

    // Participant State
    const [guestName, setGuestName] = useState('')
    const [guestEmail, setGuestEmail] = useState('')
    const [isAddingGuest, setIsAddingGuest] = useState(false)

    useEffect(() => {
        loadMeetingDetails()
    }, [meetingId])

    const loadMeetingDetails = async () => {
        setLoading(true)
        try {
            const res = await meetings.get(meetingId)
            setMeeting(res.data)

            // Try to load agenda
            try {
                const agendaRes = await meetings.getAgenda(meetingId)
                setAgendaContent(agendaRes.data.content || '')
            } catch (e) {
                // No agenda yet
                setAgendaContent('')
            }
        } catch (error) {
            console.error("Failed to load details", error)
        } finally {
            setLoading(false)
        }
    }

    const handleSaveAgenda = async () => {
        try {
            await meetings.updateAgenda(meetingId, { content: agendaContent })
            setIsEditingAgenda(false)
            await loadMeetingDetails() // Refresh
        } catch (error) {
            console.error("Failed to save agenda", error)
            alert("Failed to save agenda")
        }
    }

    const handleAddGuest = async () => {
        if (!guestEmail) return
        try {
            await meetings.addParticipants(meetingId, [{
                name: guestName,
                email: guestEmail
            }])
            setGuestName('')
            setGuestEmail('')
            setIsAddingGuest(false)
            await loadMeetingDetails() // Refresh list
        } catch (error) {
            console.error("Failed to add guest", error)
            alert("Failed to add guest")
        }
    }

    const handleUpdateRsvp = async (participantId: string, status: string) => {
        try {
            await meetings.updateRsvp(meetingId, participantId, status)
            await loadMeetingDetails()
        } catch (error) {
            console.error("Failed to update RSVP", error)
            alert("Failed to update RSVP")
        }
    }

    if (!meeting && !loading) return null

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white dark:bg-slate-900 w-full max-w-4xl max-h-[90vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden">

                {/* Header */}
                <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex justify-between items-start bg-slate-50 dark:bg-slate-800/50">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <Badge variant="neutral" className="uppercase text-xs">{meeting?.twg?.pillar || 'TWG'}</Badge>
                            <span className="text-sm text-slate-500">{new Date(meeting?.scheduled_at).toLocaleString()}</span>
                        </div>
                        <h2 className="text-2xl font-display font-bold text-slate-900 dark:text-white">{meeting?.title}</h2>
                        <p className="text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-2">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                            {meeting?.location || 'Virtual'}
                        </p>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg transition-colors">
                        <svg className="w-6 h-6 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-slate-200 dark:border-slate-800 px-6">
                    <button
                        onClick={() => setActiveTab('agenda')}
                        className={`py-4 px-4 text-sm font-bold border-b-2 transition-colors ${activeTab === 'agenda' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
                    >
                        Agenda
                    </button>
                    <button
                        onClick={() => setActiveTab('participants')}
                        className={`py-4 px-4 text-sm font-bold border-b-2 transition-colors ${activeTab === 'participants' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
                    >
                        Participants ({meeting?.participants?.length || 0})
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 bg-slate-50/50 dark:bg-slate-900/50">
                    {loading ? (
                        <div className="flex justify-center py-10"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div></div>
                    ) : (
                        <>
                            {/* AGENDA TAB */}
                            {activeTab === 'agenda' && (
                                <div className="space-y-4">
                                    <div className="flex justify-between items-center">
                                        <h3 className="text-lg font-bold">Meeting Agenda</h3>
                                        {!isEditingAgenda ? (
                                            <button onClick={() => setIsEditingAgenda(true)} className="text-sm text-blue-600 font-bold hover:underline">Edit Agenda</button>
                                        ) : (
                                            <div className="flex gap-2">
                                                <button onClick={() => setIsEditingAgenda(false)} className="text-sm text-slate-500 font-bold hover:underline">Cancel</button>
                                                <button onClick={handleSaveAgenda} className="text-sm bg-blue-600 text-white px-3 py-1 rounded-md font-bold hover:bg-blue-700">Save</button>
                                            </div>
                                        )}
                                    </div>

                                    {isEditingAgenda ? (
                                        <textarea
                                            className="w-full h-96 p-4 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-blue-500 outline-none font-mono text-sm"
                                            value={agendaContent}
                                            onChange={(e) => setAgendaContent(e.target.value)}
                                            placeholder="Enter meeting agenda (Markdown supported)..."
                                        />
                                    ) : (
                                        <div className="prose dark:prose-invert max-w-none bg-white dark:bg-slate-800 p-6 rounded-lg border border-slate-200 dark:border-slate-700 min-h-[200px]">
                                            {agendaContent ? (
                                                <div className="whitespace-pre-wrap">{agendaContent}</div>
                                            ) : (
                                                <div className="text-slate-400 italic">No agenda has been set for this meeting.</div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* PARTICIPANTS TAB */}
                            {activeTab === 'participants' && (
                                <div className="space-y-6">
                                    <div className="flex justify-between items-center">
                                        <h3 className="text-lg font-bold">Participant List</h3>
                                        <button
                                            onClick={() => setIsAddingGuest(!isAddingGuest)}
                                            className="btn-secondary text-sm"
                                        >
                                            {isAddingGuest ? 'Cancel' : '+ Add Guest'}
                                        </button>
                                    </div>

                                    {isAddingGuest && (
                                        <Card className="p-4 bg-blue-50 dark:bg-blue-900/10 border-blue-100 dark:border-blue-800">
                                            <h4 className="font-bold text-sm mb-3 text-blue-900 dark:text-blue-100">Add External Guest</h4>
                                            <div className="flex gap-3">
                                                <input
                                                    type="text"
                                                    placeholder="Name (Optional)"
                                                    className="flex-1 px-3 py-2 rounded-md border border-slate-300 dark:border-slate-600 text-sm"
                                                    value={guestName}
                                                    onChange={e => setGuestName(e.target.value)}
                                                />
                                                <input
                                                    type="email"
                                                    placeholder="Email Address"
                                                    className="flex-1 px-3 py-2 rounded-md border border-slate-300 dark:border-slate-600 text-sm"
                                                    value={guestEmail}
                                                    onChange={e => setGuestEmail(e.target.value)}
                                                />
                                                <button
                                                    onClick={handleAddGuest}
                                                    disabled={!guestEmail}
                                                    className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-bold hover:bg-blue-700 disabled:opacity-50"
                                                >
                                                    Add
                                                </button>
                                            </div>
                                        </Card>
                                    )}

                                    <div className="space-y-2">
                                        {meeting?.participants?.length === 0 && <div className="text-slate-500 italic">No participants invited yet.</div>}
                                        {meeting?.participants?.map((p: any) => (
                                            <div key={p.id} className="flex items-center justify-between p-3 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-xs font-bold text-slate-600 dark:text-slate-300">
                                                        {(p.name || p.user?.full_name || p.email || '?')[0].toUpperCase()}
                                                    </div>
                                                    <div>
                                                        <div className="font-bold text-sm text-slate-900 dark:text-white">
                                                            {p.name || p.user?.full_name || 'Guest'}
                                                        </div>
                                                        <div className="text-xs text-slate-500">
                                                            {p.email || p.user?.email}
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <Badge variant={
                                                        p.rsvp_status === 'accepted' ? 'success' :
                                                            p.rsvp_status === 'declined' ? 'danger' : 'warning'
                                                    } className="uppercase text-[10px]">
                                                        {p.rsvp_status}
                                                    </Badge>

                                                    {/* Manual RSVP Toggle (Admin/Facilitator only usually, but exposed here for functionality) */}
                                                    <select
                                                        className="text-xs bg-transparent border border-slate-200 dark:border-slate-700 rounded px-2 py-1 text-slate-500"
                                                        value={p.rsvp_status}
                                                        onChange={(e) => handleUpdateRsvp(p.id, e.target.value)}
                                                    >
                                                        <option value="pending">Pending</option>
                                                        <option value="accepted">Accept</option>
                                                        <option value="declined">Decline</option>
                                                    </select>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    )
}
