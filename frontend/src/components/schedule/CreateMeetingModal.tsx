import { useState, useEffect } from 'react';
import { Card } from '../ui';
import { meetings, twgs } from '../../services/api';
import { useAppSelector } from '../../hooks/useRedux';

interface CreateMeetingModalProps {
    isOpen: boolean;
    onClose: () => void;
    twgId?: string;
    onSuccess: () => void;
    prefilledDate?: Date | null;
}

export default function CreateMeetingModal({ isOpen, onClose, twgId, onSuccess, prefilledDate }: CreateMeetingModalProps) {
    const [loading, setLoading] = useState(false);
    const [twgList, setTwgList] = useState<any[]>([]);

    // Get user info from Redux
    const user = useAppSelector(state => state.auth.user);
    const isAdmin = user?.role === 'admin';
    const userTwgIds = user?.twg_ids || [];

    // Auto-select TWG for non-admins
    const getInitialTwgId = () => {
        if (twgId) return twgId; // If passed from TWG Workspace, use it
        if (!isAdmin && userTwgIds.length > 0) return userTwgIds[0]; // Auto-select for facilitators
        return '';
    };

    const [selectedTwgId, setSelectedTwgId] = useState(getInitialTwgId());

    const [formData, setFormData] = useState({
        title: '',
        date: '',
        time: '',
        duration: '60',
        location: 'Virtual',
        description: '',
        type: 'virtual' // Default to virtual for Google Meet link generation
    });

    // Update date when prefilledDate changes
    useEffect(() => {
        if (prefilledDate) {
            const year = prefilledDate.getFullYear();
            const month = String(prefilledDate.getMonth() + 1).padStart(2, '0');
            const day = String(prefilledDate.getDate()).padStart(2, '0');
            setFormData(prev => ({ ...prev, date: `${year}-${month}-${day}` }));
        }
    }, [prefilledDate]);

    // Load TWGs only if admin and no twgId provided
    useEffect(() => {
        if (isAdmin && !twgId && isOpen) {
            loadTwgs();
        }
    }, [isAdmin, twgId, isOpen]);

    const loadTwgs = async () => {
        try {
            const response = await twgs.list();
            setTwgList(response.data);
        } catch (error) {
            console.error('Failed to load TWGs', error);
        }
    };

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            // Treat the input date/time as UTC directly (no timezone conversion)
            // This ensures the time the user enters is the time stored in the database
            const scheduledAt = `${formData.date}T${formData.time}:00.000Z`;

            await meetings.create({
                title: formData.title,
                twg_id: twgId || selectedTwgId || undefined,
                scheduled_at: scheduledAt,
                duration_minutes: parseInt(formData.duration),
                location: formData.location,
                meeting_type: formData.type
            });

            onSuccess();
            onClose();
        } catch (error) {
            console.error('Failed to create meeting', error);
            alert('Failed to schedule meeting. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <Card className="w-full max-w-lg bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-2xl">
                <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center">
                    <h2 className="text-xl font-display font-bold text-slate-900 dark:text-white">Schedule New Session</h2>
                    <button onClick={onClose} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Session Title</label>
                        <input
                            required
                            type="text"
                            className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 focus:ring-2 focus:ring-blue-500 outline-none text-sm dark:text-white"
                            placeholder="e.g. Policy Framework Review"
                            value={formData.title}
                            onChange={e => setFormData({ ...formData, title: e.target.value })}
                        />
                    </div>

                    {/* Show TWG selector only for admins when no twgId provided */}
                    {!twgId && isAdmin && (
                        <div>
                            <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Technical Working Group</label>
                            <select
                                required
                                className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 focus:ring-2 focus:ring-blue-500 outline-none text-sm dark:text-white"
                                value={selectedTwgId}
                                onChange={e => setSelectedTwgId(e.target.value)}
                            >
                                <option value="">Select TWG...</option>
                                {twgList.map(twg => (
                                    <option key={twg.id} value={twg.id}>{twg.name}</option>
                                ))}
                            </select>
                        </div>
                    )}

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Date</label>
                            <input
                                required
                                type="date"
                                readOnly={!!prefilledDate}
                                className={`w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-blue-500 outline-none text-sm dark:text-white ${prefilledDate
                                    ? 'bg-slate-100 dark:bg-slate-800 text-slate-500 cursor-not-allowed opacity-75'
                                    : 'bg-slate-50 dark:bg-slate-800'
                                    }`}
                                value={formData.date}
                                onChange={e => setFormData({ ...formData, date: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Time</label>
                            <div
                                onClick={(e) => {
                                    const input = e.currentTarget.querySelector('input');
                                    input?.showPicker?.();
                                }}
                                className="cursor-pointer"
                            >
                                <input
                                    required
                                    type="time"
                                    className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 focus:ring-2 focus:ring-blue-500 outline-none text-sm dark:text-white cursor-pointer"
                                    value={formData.time}
                                    onChange={e => setFormData({ ...formData, time: e.target.value })}
                                />
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Duration</label>
                            <select
                                className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 focus:ring-2 focus:ring-blue-500 outline-none text-sm dark:text-white"
                                value={formData.duration}
                                onChange={e => setFormData({ ...formData, duration: e.target.value })}
                            >
                                <option value="30">30 Minutes</option>
                                <option value="60">1 Hour</option>
                                <option value="90">1.5 Hours</option>
                                <option value="120">2 Hours</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Meeting Type</label>
                            <select
                                className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 focus:ring-2 focus:ring-blue-500 outline-none text-sm dark:text-white"
                                value={formData.type}
                                onChange={e => setFormData({
                                    ...formData,
                                    type: e.target.value,
                                    location: e.target.value === 'virtual' ? 'Virtual' : ''
                                })}
                            >
                                <option value="virtual">🎥 Virtual (Google Meet)</option>
                                <option value="in_person">📍 In-Person</option>
                            </select>
                        </div>
                    </div>

                    {formData.type === 'in_person' && (
                        <div>
                            <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Location / Venue</label>
                            <input
                                required
                                type="text"
                                placeholder="e.g. Conference Room A, ECOWAS HQ"
                                className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 focus:ring-2 focus:ring-blue-500 outline-none text-sm dark:text-white"
                                value={formData.location}
                                onChange={e => setFormData({ ...formData, location: e.target.value })}
                            />
                        </div>
                    )}

                    <div className="pt-4 flex gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 font-bold text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-1 py-2.5 rounded-xl bg-blue-600 text-white font-bold hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {loading ? 'Scheduling...' : 'Schedule Session'}
                        </button>
                    </div>
                </form>
            </Card>
        </div>
    );
}
