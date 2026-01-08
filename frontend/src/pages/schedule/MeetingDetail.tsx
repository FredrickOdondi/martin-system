import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { meetings } from '../../services/api'
import { Card, Badge } from '../../components/ui'
import MeetingSidebar from './components/MeetingSidebar'
import ModernLayout from '../../layouts/ModernLayout'

type TabType = 'agenda' | 'minutes' | 'participants' | 'documents'

export default function MeetingDetail() {
    const { id: meetingId } = useParams<{ id: string }>()
    const navigate = useNavigate()
    const [meeting, setMeeting] = useState<any>(null)
    const [activeTab, setActiveTab] = useState<TabType>('minutes')
    const [loading, setLoading] = useState(true)

    // Agenda State
    const [agendaContent, setAgendaContent] = useState('')
    const [isEditingAgenda, setIsEditingAgenda] = useState(false)

    // Minutes State
    const [minutesContent, setMinutesContent] = useState('')
    const [isEditingMinutes, setIsEditingMinutes] = useState(false)
    const [actionItems, setActionItems] = useState<any[]>([])

    // Participant State
    const [guestName, setGuestName] = useState('')
    const [guestEmail, setGuestEmail] = useState('')
    const [isAddingGuest, setIsAddingGuest] = useState(false)

    // Modal States
    const [isEditingMeeting, setIsEditingMeeting] = useState(false)
    const [isAddingAction, setIsAddingAction] = useState(false)
    const [newActionDescription, setNewActionDescription] = useState('')
    const [newActionOwner, setNewActionOwner] = useState('')
    const [newActionDueDate, setNewActionDueDate] = useState('')

    // Edit Meeting State
    const [editTitle, setEditTitle] = useState('')
    const [editDate, setEditDate] = useState('')
    const [editLocation, setEditLocation] = useState('')

    // Documents State
    const [documents, setDocuments] = useState<any[]>([])
    const [isUploadingDoc, setIsUploadingDoc] = useState(false)

    useEffect(() => {
        loadMeetingDetails()
    }, [meetingId])

    const loadMeetingDetails = async () => {
        if (!meetingId) return;

        setLoading(true)
        try {
            const res = await meetings.get(meetingId)
            setMeeting(res.data)

            // Load agenda
            try {
                const agendaRes = await meetings.getAgenda(meetingId)
                setAgendaContent(agendaRes.data.content || '')
            } catch (e) {
                setAgendaContent('')
            }

            // Load minutes
            try {
                const minutesRes = await meetings.getMinutes(meetingId)
                setMinutesContent(minutesRes.data.content || '')
            } catch (e) {
                console.log("No minutes yet")
                setMinutesContent('')
            }

            // Load action items
            try {
                const actionsRes = await meetings.getActionItems(meetingId)
                setActionItems(actionsRes.data || [])
            } catch (e) {
                console.log("No action items yet")
                setActionItems([])
            }

            // Load documents
            try {
                const docsRes = await meetings.getDocuments(meetingId)
                setDocuments(docsRes.data || [])
            } catch (e) {
                console.log("No documents yet")
                setDocuments([])
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
            await loadMeetingDetails()
        } catch (error) {
            console.error("Failed to save agenda", error)
            alert("Failed to save agenda")
        }
    }

    const handleApproveMinutes = async () => {
        // TODO: Wire to backend
        alert("Minutes approved! (Backend endpoint pending)")
    }

    const handleGenerateSummary = async () => {
        // TODO: Wire to AI endpoint
        alert("AI Summary generation (Fred will implement backend)")
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
            await loadMeetingDetails()
        } catch (error) {
            console.error("Failed to add guest", error)
            alert("Failed to add guest")
        }
    }

    const handleUpdateRsvp = async (participantId: string, status: string) => {
        if (!meetingId) return;
        try {
            await meetings.updateRsvp(meetingId, participantId, status)
            await loadMeetingDetails()
        } catch (error) {
            console.error("Failed to update RSVP", error)
            alert("Failed to update RSVP")
        }
    }

    const handleAddAction = async () => {
        if (!meetingId || !newActionDescription) return;
        try {
            await meetings.createActionItem(meetingId, {
                description: newActionDescription,
                owner_id: newActionOwner || null,
                due_date: newActionDueDate || null,
                status: 'pending'
            })
            setNewActionDescription('')
            setNewActionOwner('')
            setNewActionDueDate('')
            setIsAddingAction(false)
            await loadMeetingDetails()
        } catch (error) {
            console.error("Failed to add action", error)
            alert("Failed to add action item")
        }
    }

    const handleUpdateMeeting = async () => {
        if (!meetingId) return;
        try {
            await meetings.update(meetingId, {
                title: editTitle,
                scheduled_at: editDate,
                location: editLocation
            })
            setIsEditingMeeting(false)
            await loadMeetingDetails()
        } catch (error) {
            console.error("Failed to update meeting", error)
            alert("Failed to update meeting")
        }
    }

    const openEditModal = () => {
        setEditTitle(meeting?.title || '')
        setEditDate(meeting?.scheduled_at ? new Date(meeting.scheduled_at).toISOString().slice(0, 16) : '')
        setEditLocation(meeting?.location || '')
        setIsEditingMeeting(true)
    }

    const handleDocumentUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!meetingId || !e.target.files || e.target.files.length === 0) return;

        const file = e.target.files[0];
        setIsUploadingDoc(true);

        try {
            await meetings.uploadDocument(meetingId, file);
            await loadMeetingDetails();
            // Reset file input
            e.target.value = '';
        } catch (error) {
            console.error("Failed to upload document", error);
            alert("Failed to upload document");
        } finally {
            setIsUploadingDoc(false);
        }
    }

    const handleDownloadDocument = (docId: string) => {
        const downloadUrl = `${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1'}/meetings/documents/${docId}/download`;
        window.open(downloadUrl, '_blank');
    }

    const handleDeleteDocument = async (docId: string) => {
        if (!confirm('Are you sure you want to delete this document?')) return;

        try {
            await fetch(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1'}/meetings/documents/${docId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            await loadMeetingDetails();
        } catch (error) {
            console.error("Failed to delete document", error);
            alert("Failed to delete document");
        }
    }

    if (!meeting && !loading) return null

    return (
        <ModernLayout>
            <div className="flex flex-col h-full">

                {/* Header */}
                <div className="px-8 py-6 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
                    <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                                <button onClick={() => navigate(-1)} className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded transition-colors">
                                    <svg className="w-5 h-5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                                    </svg>
                                </button>
                                <span className="text-sm text-slate-500">Home / Infrastructure TWG / Meeting #{meetingId?.slice(0, 6)}</span>
                            </div>
                            <div className="flex items-center gap-4">
                                <h1 className="text-3xl font-display font-black text-slate-900 dark:text-white">{meeting?.title}</h1>
                                <Badge variant="success" className="uppercase text-xs">{meeting?.status}</Badge>
                            </div>
                            <div className="flex items-center gap-2 mt-2 text-sm text-slate-500">
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                                <span>Minutes Pending Approval</span>
                            </div>
                        </div>
                        <div className="flex gap-3">
                            <button onClick={openEditModal} className="btn-secondary text-sm flex items-center gap-2">
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                </svg>
                                Edit Meeting
                            </button>
                            <button onClick={handleApproveMinutes} className="btn-primary text-sm flex items-center gap-2">
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                Approve Minutes
                            </button>
                        </div>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-slate-200 dark:border-slate-800 px-8 bg-white dark:bg-slate-900">
                    {[
                        { id: 'agenda', label: 'Agenda' },
                        { id: 'minutes', label: 'Minutes & Decisions' },
                        { id: 'participants', label: 'Participants' },
                        { id: 'documents', label: 'Documents' }
                    ].map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as TabType)}
                            className={`py-4 px-6 text-sm font-bold border-b-2 transition-colors ${activeTab === tab.id
                                ? 'border-blue-600 text-blue-600'
                                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                                }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto">
                    <div className="flex">
                        <div className="flex-1 p-8">
                            {loading ? (
                                <div className="flex justify-center py-20">
                                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                                </div>
                            ) : (
                                <>
                                    {/* AGENDA TAB */}
                                    {activeTab === 'agenda' && (
                                        <div className="max-w-4xl space-y-6">
                                            <div className="flex justify-between items-center">
                                                <h2 className="text-xl font-bold text-slate-900 dark:text-white">Meeting Agenda</h2>
                                                {!isEditingAgenda ? (
                                                    <button onClick={() => setIsEditingAgenda(true)} className="btn-secondary text-sm">
                                                        Edit Agenda
                                                    </button>
                                                ) : (
                                                    <div className="flex gap-2">
                                                        <button onClick={() => setIsEditingAgenda(false)} className="btn-secondary text-sm">Cancel</button>
                                                        <button onClick={handleSaveAgenda} className="btn-primary text-sm">Save</button>
                                                    </div>
                                                )}
                                            </div>

                                            {isEditingAgenda ? (
                                                <textarea
                                                    className="w-full h-96 p-4 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-blue-500 outline-none font-mono text-sm"
                                                    value={agendaContent}
                                                    onChange={(e) => setAgendaContent(e.target.value)}
                                                    placeholder="Enter meeting agenda..."
                                                />
                                            ) : (
                                                <Card className="p-6">
                                                    {agendaContent ? (
                                                        <div className="prose dark:prose-invert max-w-none whitespace-pre-wrap">{agendaContent}</div>
                                                    ) : (
                                                        <div className="text-slate-400 italic text-center py-10">No agenda has been set for this meeting.</div>
                                                    )}
                                                </Card>
                                            )}
                                        </div>
                                    )}

                                    {/* MINUTES & DECISIONS TAB */}
                                    {activeTab === 'minutes' && (
                                        <div className="max-w-4xl space-y-6">
                                            {/* AI Summary Widget */}
                                            <Card className="p-6 bg-blue-50 dark:bg-blue-900/10 border-blue-200 dark:border-blue-800">
                                                <div className="flex items-start gap-4">
                                                    <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center shrink-0">
                                                        <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                                                        </svg>
                                                    </div>
                                                    <div className="flex-1">
                                                        <h3 className="font-bold text-blue-900 dark:text-blue-100 mb-1">AI Meeting Summary Available</h3>
                                                        <p className="text-sm text-blue-700 dark:text-blue-300 mb-3">
                                                            The AI agent has processed the transcript and generated a draft of the minutes, decisions, and action items. Please review before approving.
                                                        </p>
                                                        <button onClick={handleGenerateSummary} className="text-sm font-bold text-blue-600 dark:text-blue-400 hover:underline">
                                                            View Summary →
                                                        </button>
                                                    </div>
                                                </div>
                                            </Card>

                                            {/* Minutes Content */}
                                            <div>
                                                <div className="flex items-center justify-between mb-4">
                                                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">Meeting Minutes</h2>
                                                    <div className="flex gap-2">
                                                        <button className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors">
                                                            <svg className="w-5 h-5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                                                            </svg>
                                                        </button>
                                                        <button className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors">
                                                            <svg className="w-5 h-5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                                                            </svg>
                                                        </button>
                                                    </div>
                                                </div>
                                                <Card className="p-8">
                                                    <div className="prose dark:prose-invert max-w-none">
                                                        <div dangerouslySetInnerHTML={{ __html: minutesContent.replace(/\n/g, '<br/>') }} />
                                                    </div>
                                                </Card>
                                            </div>

                                            {/* Action Items */}
                                            <div>
                                                <div className="flex items-center justify-between mb-4">
                                                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">Action Items</h2>
                                                    <button onClick={() => setIsAddingAction(true)} className="btn-secondary text-sm flex items-center gap-2">
                                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                                                        </svg>
                                                        Add Action
                                                    </button>
                                                </div>

                                                {/* Add Action Form */}
                                                {isAddingAction && (
                                                    <Card className="p-4 mb-4 bg-blue-50 dark:bg-blue-900/10 border-blue-200 dark:border-blue-800">
                                                        <h4 className="font-bold text-sm mb-3 text-blue-900 dark:text-blue-100">Create New Action Item</h4>
                                                        <div className="space-y-3">
                                                            <div>
                                                                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Description *</label>
                                                                <textarea
                                                                    className="w-full px-3 py-2 rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-sm"
                                                                    placeholder="What needs to be done?"
                                                                    rows={2}
                                                                    value={newActionDescription}
                                                                    onChange={e => setNewActionDescription(e.target.value)}
                                                                />
                                                            </div>
                                                            <div className="grid grid-cols-2 gap-3">
                                                                <div>
                                                                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Owner (Optional)</label>
                                                                    <input
                                                                        type="text"
                                                                        className="w-full px-3 py-2 rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-sm"
                                                                        placeholder="User ID"
                                                                        value={newActionOwner}
                                                                        onChange={e => setNewActionOwner(e.target.value)}
                                                                    />
                                                                </div>
                                                                <div>
                                                                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Due Date (Optional)</label>
                                                                    <input
                                                                        type="date"
                                                                        className="w-full px-3 py-2 rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-sm"
                                                                        value={newActionDueDate}
                                                                        onChange={e => setNewActionDueDate(e.target.value)}
                                                                    />
                                                                </div>
                                                            </div>
                                                            <div className="flex gap-2 justify-end">
                                                                <button
                                                                    onClick={() => {
                                                                        setIsAddingAction(false)
                                                                        setNewActionDescription('')
                                                                        setNewActionOwner('')
                                                                        setNewActionDueDate('')
                                                                    }}
                                                                    className="btn-secondary text-sm"
                                                                >
                                                                    Cancel
                                                                </button>
                                                                <button
                                                                    onClick={handleAddAction}
                                                                    disabled={!newActionDescription}
                                                                    className="btn-primary text-sm"
                                                                >
                                                                    Create Action
                                                                </button>
                                                            </div>
                                                        </div>
                                                    </Card>
                                                )}

                                                <div className="space-y-3">
                                                    {actionItems.map(item => (
                                                        <Card key={item.id} className="p-4">
                                                            <div className="flex items-center gap-4">
                                                                <input type="checkbox" className="w-5 h-5 rounded border-slate-300" />
                                                                <div className="flex-1">
                                                                    <div className="font-bold text-slate-900 dark:text-white">{item.description}</div>
                                                                </div>
                                                                <div className="flex items-center gap-3">
                                                                    <div className="flex items-center gap-2">
                                                                        <div className="w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold">
                                                                            {item.owner.avatar}
                                                                        </div>
                                                                        <span className="text-sm text-slate-600 dark:text-slate-400">{item.owner.name}</span>
                                                                    </div>
                                                                    <span className="text-sm text-slate-500">{item.dueDate}</span>
                                                                    <Badge variant={item.status === 'pending' ? 'warning' : 'info'} className="text-xs">
                                                                        {item.status === 'pending' ? 'Pending' : 'In Progress'}
                                                                    </Badge>
                                                                </div>
                                                            </div>
                                                        </Card>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* PARTICIPANTS TAB */}
                                    {activeTab === 'participants' && (
                                        <div className="max-w-4xl space-y-6">
                                            <div className="flex justify-between items-center">
                                                <h2 className="text-xl font-bold text-slate-900 dark:text-white">Participant List</h2>
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
                                                            className="btn-primary text-sm"
                                                        >
                                                            Add
                                                        </button>
                                                    </div>
                                                </Card>
                                            )}

                                            <div className="space-y-2">
                                                {meeting?.participants?.map((p: any) => (
                                                    <Card key={p.id} className="p-4">
                                                        <div className="flex items-center justify-between">
                                                            <div className="flex items-center gap-3">
                                                                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold">
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
                                                    </Card>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* DOCUMENTS TAB */}
                                    {activeTab === 'documents' && (
                                        <div className="max-w-4xl space-y-6">
                                            <div className="flex justify-between items-center">
                                                <h2 className="text-xl font-bold text-slate-900 dark:text-white">Meeting Documents</h2>
                                                <label className="btn-primary text-sm flex items-center gap-2 cursor-pointer">
                                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                                    </svg>
                                                    {isUploadingDoc ? 'Uploading...' : 'Upload Document'}
                                                    <input
                                                        type="file"
                                                        className="hidden"
                                                        onChange={handleDocumentUpload}
                                                        disabled={isUploadingDoc}
                                                    />
                                                </label>
                                            </div>

                                            {documents.length === 0 ? (
                                                <div className="text-center py-20 bg-slate-50 dark:bg-slate-800/50 rounded-2xl border border-dashed border-slate-300 dark:border-slate-700">
                                                    <div className="w-16 h-16 bg-slate-200 dark:bg-slate-700 text-slate-400 rounded-full flex items-center justify-center mx-auto mb-4">
                                                        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                                        </svg>
                                                    </div>
                                                    <h3 className="text-lg font-bold text-slate-900 dark:text-white">No Documents Yet</h3>
                                                    <p className="text-slate-500 max-w-sm mx-auto mt-2">Upload meeting documents, presentations, or attachments here.</p>
                                                </div>
                                            ) : (
                                                <div className="space-y-3">
                                                    {documents.map((doc: any) => (
                                                        <Card key={doc.id} className="p-4 hover:border-blue-300 dark:hover:border-blue-700 transition-colors cursor-pointer">
                                                            <div className="flex items-center gap-4">
                                                                <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${doc.file_name?.endsWith('.pdf') ? 'bg-red-100 dark:bg-red-900/30' :
                                                                    doc.file_name?.endsWith('.docx') || doc.file_name?.endsWith('.doc') ? 'bg-blue-100 dark:bg-blue-900/30' :
                                                                        'bg-slate-100 dark:bg-slate-800'
                                                                    }`}>
                                                                    <svg className={`w-6 h-6 ${doc.file_name?.endsWith('.pdf') ? 'text-red-600 dark:text-red-400' :
                                                                        doc.file_name?.endsWith('.docx') || doc.file_name?.endsWith('.doc') ? 'text-blue-600 dark:text-blue-400' :
                                                                            'text-slate-600 dark:text-slate-400'
                                                                        }`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                                                    </svg>
                                                                </div>
                                                                <div className="flex-1 min-w-0">
                                                                    <div className="font-bold text-sm text-slate-900 dark:text-white truncate">{doc.file_name || 'Untitled Document'}</div>
                                                                    <div className="text-xs text-slate-500">
                                                                        {doc.file_size ? `${(doc.file_size / 1024).toFixed(1)} KB` : 'Unknown size'} •
                                                                        {doc.created_at ? ` Uploaded ${new Date(doc.created_at).toLocaleDateString()}` : ' Recently uploaded'}
                                                                    </div>
                                                                </div>
                                                                <div className="flex gap-2">
                                                                    <button
                                                                        onClick={() => handleDownloadDocument(doc.id)}
                                                                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                                                                        title="Download"
                                                                    >
                                                                        <svg className="w-5 h-5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                                                        </svg>
                                                                    </button>
                                                                    <button
                                                                        onClick={() => handleDeleteDocument(doc.id)}
                                                                        className="p-2 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-colors"
                                                                        title="Delete"
                                                                    >
                                                                        <svg className="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                                        </svg>
                                                                    </button>
                                                                </div>
                                                            </div>
                                                        </Card>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </>
                            )}
                        </div>

                        {/* Sidebar */}
                        <MeetingSidebar meeting={meeting} />
                    </div>
                </div>
            </div>

            {/* Edit Meeting Modal */}
            {isEditingMeeting && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
                        <div className="p-6 border-b border-slate-200 dark:border-slate-800">
                            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Edit Meeting</h2>
                        </div>
                        <div className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">Meeting Title *</label>
                                <input
                                    type="text"
                                    className="w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none"
                                    value={editTitle}
                                    onChange={e => setEditTitle(e.target.value)}
                                    placeholder="Enter meeting title"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">Date & Time *</label>
                                <input
                                    type="datetime-local"
                                    className="w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none"
                                    value={editDate}
                                    onChange={e => setEditDate(e.target.value)}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">Location</label>
                                <input
                                    type="text"
                                    className="w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none"
                                    value={editLocation}
                                    onChange={e => setEditLocation(e.target.value)}
                                    placeholder="Meeting location or video link"
                                />
                            </div>
                        </div>
                        <div className="p-6 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-3">
                            <button
                                onClick={() => setIsEditingMeeting(false)}
                                className="btn-secondary"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleUpdateMeeting}
                                disabled={!editTitle || !editDate}
                                className="btn-primary"
                            >
                                Save Changes
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </ModernLayout>
    )
}
