import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { meetings } from '../../services/api'
import { Card, Badge } from '../../components/ui'
import MeetingSidebar from './components/MeetingSidebar'
import ModernLayout from '../../layouts/ModernLayout'
import ConflictModal from '../../components/modals/ConflictModal'
import InputModal from '../../components/modals/InputModal'
import InvitePreviewModal from '../../components/modals/InvitePreviewModal'
import StatusModal from '../../components/modals/StatusModal'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

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
    const [isGeneratingAgenda, setIsGeneratingAgenda] = useState(false)

    // Minutes State
    const [minutesContent, setMinutesContent] = useState('')
    const [minutesStatus, setMinutesStatus] = useState<string>('draft')
    const [isGeneratingMinutes, setIsGeneratingMinutes] = useState(false)
    const [isSubmittingForApproval, setIsSubmittingForApproval] = useState(false)
    const [isApprovingMinutes, setIsApprovingMinutes] = useState(false)
    const [actionItems, setActionItems] = useState<any[]>([])

    // Participant State
    const [guestName, setGuestName] = useState('')
    const [guestEmail, setGuestEmail] = useState('')
    const [isAddingGuest, setIsAddingGuest] = useState(false)
    const [isSendingInvites, setIsSendingInvites] = useState(false)
    const [isCheckingConflicts, setIsCheckingConflicts] = useState(false)
    const [showConflictModal, setShowConflictModal] = useState(false)
    const [detectedConflicts, setDetectedConflicts] = useState<any[]>([])
    const [showCancelModal, setShowCancelModal] = useState(false)
    const [showUpdateModal, setShowUpdateModal] = useState(false)
    const [showInvitePreviewModal, setShowInvitePreviewModal] = useState(false)
    const [isLoadingAction, setIsLoadingAction] = useState(false)
    const [statusModal, setStatusModal] = useState<{ isOpen: boolean, type: 'success' | 'error' | 'info', title: string, message: string }>({
        isOpen: false,
        type: 'info',
        title: '',
        message: ''
    })

    // Modal States
    const [isEditingMeeting, setIsEditingMeeting] = useState(false)
    const [isAddingAction, setIsAddingAction] = useState(false)
    const [isExtractingActions, setIsExtractingActions] = useState(false)
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
                setMinutesStatus(minutesRes.data.status || 'draft')
            } catch (e) {
                console.log("No minutes yet")
                setMinutesContent('')
                setMinutesStatus('draft')
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
        if (!meetingId) return
        try {
            await meetings.updateAgenda(meetingId, { content: agendaContent })
            setIsEditingAgenda(false)
            await loadMeetingDetails()
        } catch (error) {
            console.error("Failed to save agenda", error)
            alert("Failed to save agenda")
        }
    }

    const handleGenerateAgenda = async () => {
        if (!meetingId || isGeneratingAgenda) return
        setIsGeneratingAgenda(true)
        try {
            const res = await meetings.generateAgenda(meetingId)
            setAgendaContent(res.data.generated_agenda)
            setIsEditingAgenda(true)  // Switch to edit mode to allow modifications
        } catch (error: any) {
            console.error("Failed to generate agenda", error)
            alert(error?.response?.data?.detail || "Failed to generate agenda")
        } finally {
            setIsGeneratingAgenda(false)
        }
    }

    const handleGenerateSummary = async () => {
        if (!meetingId || isGeneratingMinutes) return
        setIsGeneratingMinutes(true)
        try {
            const res = await meetings.generateMinutes(meetingId)
            setMinutesContent(res.data.generated_minutes)
            setMinutesStatus('draft')  // Generated content starts as draft
        } catch (error: any) {
            console.error("Failed to generate minutes", error)
            alert(error?.response?.data?.detail || "Failed to generate minutes")
        } finally {
            setIsGeneratingMinutes(false)
        }
    }

    const handleSubmitForApproval = async () => {
        if (!meetingId || isSubmittingForApproval) return

        // First save the minutes content
        try {
            await meetings.updateMinutes(meetingId, { content: minutesContent })
        } catch (error) {
            console.error("Failed to save minutes before submission", error)
            alert("Failed to save minutes")
            return
        }

        setIsSubmittingForApproval(true)
        try {
            const res = await meetings.submitMinutesForApproval(meetingId)
            setMinutesStatus(res.data.status)
            alert("Minutes submitted for approval!")
        } catch (error: any) {
            console.error("Failed to submit for approval", error)
            alert(error?.response?.data?.detail || "Failed to submit for approval")
        } finally {
            setIsSubmittingForApproval(false)
        }
    }

    const handleApproveMinutes = async () => {
        if (!meetingId || isApprovingMinutes) return
        setIsApprovingMinutes(true)
        try {
            const res = await meetings.approveMinutes(meetingId)
            setMinutesStatus(res.data.status)
            alert(`Minutes approved by ${res.data.approved_by}!`)
        } catch (error: any) {
            console.error("Failed to approve minutes", error)
            alert(error?.response?.data?.detail || "Failed to approve minutes")
        } finally {
            setIsApprovingMinutes(false)
        }
    }

    const handleAddGuest = async () => {
        if (!meetingId || !guestEmail) return
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

    const handleSendInvites = async () => {
        if (!meetingId || isSendingInvites || isCheckingConflicts) return

        // Step 1: Run conflict check first (Supervisor Air Traffic Control)
        setIsCheckingConflicts(true)
        try {
            const conflictRes = await meetings.conflictCheck(meetingId)
            const conflicts = conflictRes.data.conflicts || []

            if (conflicts.length > 0) {
                // Show custom conflict modal
                setDetectedConflicts(conflicts)
                setShowConflictModal(true)
                setIsCheckingConflicts(false)
                return
            }
        } catch (error: any) {
            console.error("Conflict check failed", error)
            // If conflict check fails, proceed anyway
        }
        setIsCheckingConflicts(false)

        // No conflicts - show HITL preview modal instead of sending directly
        setShowInvitePreviewModal(true)
    }

    const proceedWithSendingInvites = async () => {
        if (!meetingId) return
        setShowConflictModal(false)
        // After conflict resolution, also show HITL preview
        setShowInvitePreviewModal(true)
    }

    const handleApproveAndSend = async () => {
        if (!meetingId) return
        setIsSendingInvites(true)
        try {
            await meetings.approveInvite(meetingId)
            setShowInvitePreviewModal(false)
            setStatusModal({
                isOpen: true,
                type: 'success',
                title: 'Invitations Sent',
                message: 'Meeting invitations have been sent to all participants.'
            })
            await loadMeetingDetails()
        } catch (error: any) {
            console.error("Failed to send invites", error)
            setStatusModal({
                isOpen: true,
                type: 'error',
                title: 'Failed to Send',
                message: error?.response?.data?.detail || 'Failed to send invitations. Please try again.'
            })
        } finally {
            setIsSendingInvites(false)
        }
    }

    const handleConflictCancel = () => {
        setShowConflictModal(false)
        setDetectedConflicts([])
    }

    const handleCancelMeeting = () => setShowCancelModal(true)

    const confirmCancelMeeting = async (reason: string) => {
        if (!meetingId) return
        setIsLoadingAction(true)
        try {
            await meetings.cancel(meetingId, reason)
            setShowCancelModal(false)
            setStatusModal({
                isOpen: true,
                type: 'success',
                title: 'Meeting Cancelled',
                message: 'The meeting has been cancelled and all participants have been notified via email.'
            })
            await loadMeetingDetails()
        } catch (error: any) {
            console.error("Failed to cancel meeting", error)
            setStatusModal({
                isOpen: true,
                type: 'error',
                title: 'Cancellation Failed',
                message: error?.response?.data?.detail || 'An unexpected error occurred while cancelling the meeting.'
            })
        } finally {
            setIsLoadingAction(false)
        }
    }

    const handleNotifyUpdate = () => setShowUpdateModal(true)

    const confirmNotifyUpdate = async (changeSummary: string) => {
        if (!meetingId) return
        setIsLoadingAction(true)
        try {
            await meetings.notifyUpdate(meetingId, [changeSummary])
            setShowUpdateModal(false)
            setStatusModal({
                isOpen: true,
                type: 'success',
                title: 'Update Sent',
                message: 'Update notifications have been sent to all participants with the new meeting details.'
            })
        } catch (error: any) {
            console.error("Failed to send update", error)
            setStatusModal({
                isOpen: true,
                type: 'error',
                title: 'Update Failed',
                message: error?.response?.data?.detail || 'Failed to send update notifications. Please try again.'
            })
        } finally {
            setIsLoadingAction(false)
        }
    }

    const handleExtractActions = async () => {
        if (!meetingId || isExtractingActions) return
        setIsExtractingActions(true)
        try {
            const res = await meetings.extractActions(meetingId)
            const message = res.data.message || `Extracted ${res.data.extracted_actions?.length || 0} action items`
            const createdCount = res.data.created_items?.filter((i: any) => i.created).length || 0

            if (createdCount > 0) {
                alert(`✅ ${message}! The action items have been added to the tracker.`)
                await loadMeetingDetails()  // Refresh to show new action items
            } else if (res.data.extracted_actions?.length > 0) {
                alert("Extracted action items but failed to save them. Check console.")
                console.log("Extraction result:", res.data)
            } else {
                alert("No action items could be extracted from the minutes.")
            }
        } catch (error: any) {
            console.error("Failed to extract actions", error)
            alert(error?.response?.data?.detail || "Failed to extract action items")
        } finally {
            setIsExtractingActions(false)
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

                {/* Conflict Warning Modal */}
                <ConflictModal
                    isOpen={showConflictModal}
                    conflicts={detectedConflicts}
                    onProceed={proceedWithSendingInvites}
                    onCancel={handleConflictCancel}
                />
                {/* Cancel Meeting Modal */}
                <InputModal
                    isOpen={showCancelModal}
                    title="Cancel Meeting"
                    description="Are you sure you want to cancel this meeting? This will send a cancellation email to all participants. This action cannot be undone."
                    placeholder="Reason for cancellation (optional)..."
                    confirmText="Cancel Meeting"
                    confirmVariant="danger"
                    icon="🚫"
                    isLoading={isLoadingAction}
                    onConfirm={confirmCancelMeeting}
                    onCancel={() => setShowCancelModal(false)}
                />
                {/* Update Notification Modal */}
                <InputModal
                    isOpen={showUpdateModal}
                    title="Send Update"
                    description="Notify participants about changes to this meeting. An updated calendar invite will be sent."
                    placeholder="Briefly summarize changes (e.g. 'Time changed to 2 PM')..."
                    confirmText="Send Update"
                    confirmVariant="warning"
                    icon="📢"
                    isLoading={isLoadingAction}
                    onConfirm={confirmNotifyUpdate}
                    onCancel={() => setShowUpdateModal(false)}
                />
                {/* Success/Error Status Modal */}
                <StatusModal
                    isOpen={statusModal.isOpen}
                    type={statusModal.type}
                    title={statusModal.title}
                    message={statusModal.message}
                    onClose={() => setStatusModal(prev => ({ ...prev, isOpen: false }))}
                />
                {/* HITL Invite Preview Modal */}
                <InvitePreviewModal
                    isOpen={showInvitePreviewModal}
                    meetingId={meetingId || ''}
                    onClose={() => setShowInvitePreviewModal(false)}
                    onApprove={handleApproveAndSend}
                    isApproving={isSendingInvites}
                />

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
                            {meeting?.status === 'scheduled' && (
                                <>
                                    <button onClick={handleNotifyUpdate} className="btn-secondary text-sm flex items-center gap-2 border-yellow-500 text-yellow-600 hover:bg-yellow-50 dark:hover:bg-yellow-900/30">
                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                                        </svg>
                                        Send Update
                                    </button>
                                    <button onClick={handleCancelMeeting} className="btn-secondary text-sm flex items-center gap-2 border-red-500 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30">
                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                        </svg>
                                        Cancel
                                    </button>
                                </>
                            )}
                            <button onClick={openEditModal} className="btn-secondary text-sm flex items-center gap-2">
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                </svg>
                                Edit Meeting
                            </button>
                            {minutesStatus === 'pending_approval' && (
                                <button onClick={handleApproveMinutes} className="btn-primary text-sm flex items-center gap-2">
                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                    Approve & Send
                                </button>
                            )}
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
                                                <div className="flex gap-2">
                                                    <button
                                                        onClick={handleGenerateAgenda}
                                                        disabled={isGeneratingAgenda}
                                                        className="btn-secondary text-sm flex items-center gap-1 disabled:opacity-50"
                                                    >
                                                        {isGeneratingAgenda ? (
                                                            <><span className="animate-spin">⏳</span> Generating...</>
                                                        ) : (
                                                            <>✨ Generate Agenda</>
                                                        )}
                                                    </button>
                                                    {!isEditingAgenda ? (
                                                        <button onClick={() => setIsEditingAgenda(true)} className="btn-secondary text-sm">
                                                            Edit Agenda
                                                        </button>
                                                    ) : (
                                                        <>
                                                            <button onClick={() => setIsEditingAgenda(false)} className="btn-secondary text-sm">Cancel</button>
                                                            <button onClick={handleSaveAgenda} className="btn-primary text-sm">Save</button>
                                                        </>
                                                    )}
                                                </div>
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
                                                        <div className="prose prose-slate dark:prose-invert max-w-none">
                                                            <ReactMarkdown
                                                                remarkPlugins={[remarkGfm]}
                                                                components={{
                                                                    h1: ({ node, ...props }) => <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-4" {...props} />,
                                                                    h2: ({ node, ...props }) => <h2 className="text-xl font-bold text-slate-800 dark:text-slate-200 mt-6 mb-3" {...props} />,
                                                                    h3: ({ node, ...props }) => <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-300 mt-4 mb-2" {...props} />,
                                                                    ul: ({ node, ...props }) => <ul className="list-disc pl-6 mb-4 space-y-1" {...props} />,
                                                                    ol: ({ node, ...props }) => <ol className="list-decimal pl-6 mb-4 space-y-1" {...props} />,
                                                                    li: ({ node, ...props }) => <li className="text-slate-600 dark:text-slate-400" {...props} />,
                                                                    p: ({ node, ...props }) => <p className="mb-3 text-slate-600 dark:text-slate-400" {...props} />,
                                                                    strong: ({ node, ...props }) => <strong className="font-bold text-slate-800 dark:text-slate-200" {...props} />,
                                                                    table: ({ node, ...props }) => <table className="min-w-full border-collapse border border-slate-200 dark:border-slate-700 my-4" {...props} />,
                                                                    th: ({ node, ...props }) => <th className="border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 px-4 py-2 text-left font-bold" {...props} />,
                                                                    td: ({ node, ...props }) => <td className="border border-slate-200 dark:border-slate-700 px-4 py-2" {...props} />,
                                                                }}
                                                            >
                                                                {agendaContent}
                                                            </ReactMarkdown>
                                                        </div>
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
                                                        <button
                                                            onClick={handleGenerateSummary}
                                                            disabled={isGeneratingMinutes}
                                                            className="text-sm font-bold text-blue-600 dark:text-blue-400 hover:underline disabled:opacity-50"
                                                        >
                                                            {isGeneratingMinutes ? "⏳ Generating..." : "✨ Generate Minutes →"}
                                                        </button>
                                                    </div>
                                                </div>
                                            </Card>

                                            {/* Minutes Content */}
                                            <div>
                                                <div className="flex items-center justify-between mb-4">
                                                    <div className="flex items-center gap-3">
                                                        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Meeting Minutes</h2>
                                                        {/* Status Badge */}
                                                        <span className={`px-2 py-1 text-xs font-bold rounded-full ${minutesStatus === 'approved' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                                                            minutesStatus === 'pending_approval' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' :
                                                                'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
                                                            }`}>
                                                            {minutesStatus === 'approved' ? '✓ Approved' :
                                                                minutesStatus === 'pending_approval' ? '⏳ Pending Approval' :
                                                                    '📝 Draft'}
                                                        </span>
                                                    </div>
                                                    <div className="flex gap-2">
                                                        {/* Show Submit for Approval if DRAFT */}
                                                        {minutesStatus === 'draft' && minutesContent && (
                                                            <button
                                                                onClick={handleSubmitForApproval}
                                                                disabled={isSubmittingForApproval}
                                                                className="btn-secondary text-sm flex items-center gap-1 disabled:opacity-50"
                                                            >
                                                                {isSubmittingForApproval ? '⏳ Submitting...' : '📤 Submit for Approval'}
                                                            </button>
                                                        )}
                                                        {/* Show Approve button if PENDING_APPROVAL */}
                                                        {minutesStatus === 'pending_approval' && (
                                                            <button
                                                                onClick={handleApproveMinutes}
                                                                disabled={isApprovingMinutes}
                                                                className="btn-primary text-sm flex items-center gap-1 disabled:opacity-50"
                                                            >
                                                                {isApprovingMinutes ? '⏳ Approving...' : '✅ Approve & Send'}
                                                            </button>
                                                        )}
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
                                                    <div className="prose prose-slate dark:prose-invert max-w-none">
                                                        <ReactMarkdown
                                                            remarkPlugins={[remarkGfm]}
                                                            components={{
                                                                h1: ({ node, ...props }) => <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-4" {...props} />,
                                                                h2: ({ node, ...props }) => <h2 className="text-xl font-bold text-slate-800 dark:text-slate-200 mt-6 mb-3" {...props} />,
                                                                h3: ({ node, ...props }) => <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-300 mt-4 mb-2" {...props} />,
                                                                ul: ({ node, ...props }) => <ul className="list-disc pl-6 mb-4 space-y-1" {...props} />,
                                                                ol: ({ node, ...props }) => <ol className="list-decimal pl-6 mb-4 space-y-1" {...props} />,
                                                                li: ({ node, ...props }) => <li className="text-slate-600 dark:text-slate-400" {...props} />,
                                                                p: ({ node, ...props }) => <p className="mb-3 text-slate-600 dark:text-slate-400" {...props} />,
                                                                strong: ({ node, ...props }) => <strong className="font-bold text-slate-800 dark:text-slate-200" {...props} />,
                                                                table: ({ node, ...props }) => <table className="min-w-full border-collapse border border-slate-200 dark:border-slate-700 my-4" {...props} />,
                                                                th: ({ node, ...props }) => <th className="border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 px-4 py-2 text-left font-bold" {...props} />,
                                                                td: ({ node, ...props }) => <td className="border border-slate-200 dark:border-slate-700 px-4 py-2" {...props} />,
                                                            }}
                                                        >
                                                            {minutesContent}
                                                        </ReactMarkdown>
                                                    </div>
                                                </Card>
                                            </div>

                                            {/* Action Items */}
                                            <div>
                                                <div className="flex items-center justify-between mb-4">
                                                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">Action Items</h2>
                                                    <div className="flex gap-2">
                                                        <button
                                                            onClick={handleExtractActions}
                                                            disabled={isExtractingActions || !minutesContent}
                                                            className="btn-secondary text-sm flex items-center gap-1 disabled:opacity-50"
                                                            title="Extract action items from minutes using AI"
                                                        >
                                                            {isExtractingActions ? (
                                                                <><span className="animate-spin">⏳</span> Extracting...</>
                                                            ) : (
                                                                <>📋 Extract from Minutes</>
                                                            )}
                                                        </button>
                                                        <button onClick={() => setIsAddingAction(true)} className="btn-secondary text-sm flex items-center gap-2">
                                                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                                                            </svg>
                                                            Add Action
                                                        </button>
                                                    </div>
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
                                                <div className="flex gap-2">
                                                    <button
                                                        onClick={handleSendInvites}
                                                        disabled={!meeting?.participants?.length || isSendingInvites || isCheckingConflicts}
                                                        className="btn-primary text-sm flex items-center gap-1 disabled:opacity-50"
                                                        title="Send email invitations to all participants"
                                                    >
                                                        {isCheckingConflicts ? (
                                                            <>
                                                                <span className="animate-spin">🔍</span> Checking conflicts...
                                                            </>
                                                        ) : isSendingInvites ? (
                                                            <>
                                                                <span className="animate-spin">⏳</span> Sending...
                                                            </>
                                                        ) : (
                                                            <>📧 Send Invites</>
                                                        )}
                                                    </button>
                                                    <button
                                                        onClick={() => setIsAddingGuest(!isAddingGuest)}
                                                        className="btn-secondary text-sm"
                                                    >
                                                        {isAddingGuest ? 'Cancel' : '+ Add Guest'}
                                                    </button>
                                                </div>
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
