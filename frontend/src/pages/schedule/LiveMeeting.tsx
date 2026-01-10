import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AudioStreamer } from '../../services/audioStreamer';
import { meetings } from '../../services/api';
import { Card, Badge } from '../../components/ui';

export default function LiveMeeting() {
    const { id: meetingId } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [status, setStatus] = useState<'connected' | 'disconnected' | 'recording'>('disconnected');
    const [transcript, setTranscript] = useState<string>('');
    const [interimTranscript, setInterimTranscript] = useState<string>('');
    const [error, setError] = useState<string | null>(null);
    const [meeting, setMeeting] = useState<any>(null);
    const [agendaAnalysis, setAgendaAnalysis] = useState<any>(null);
    const streamerRef = useRef<AudioStreamer | null>(null);
    const transcriptEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        loadMeeting();
        return () => {
            if (streamerRef.current) {
                streamerRef.current.stop();
            }
        };
    }, [meetingId]);

    useEffect(() => {
        // Auto-scroll to bottom of transcript
        transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [transcript, interimTranscript]);

    const loadMeeting = async () => {
        if (!meetingId) return;
        try {
            const res = await meetings.get(meetingId);
            setMeeting(res.data);
            if (res.data.transcript) {
                setTranscript(res.data.transcript);
            }
        } catch (e) {
            console.error("Failed to load meeting", e);
            setError("Failed to load meeting details");
        }
    };

    const handleStart = async () => {
        if (!meetingId) return;
        setError(null);

        streamerRef.current = new AudioStreamer({
            meetingId,
            onTranscript: (data) => {
                // Determine if it's final or interim
                // The backend sends { text: "...", is_final: boolean } OR { type: "agenda_update", data: ... }
                // Since AudioStreamer might just pass data.data if type is transcript, let's see implementation.
                // Assuming AudioStreamer raw message handler needs to distinguish.
                // Wait, AudioStreamer implementation only passed transcript data. 
                // Let's modify AudioStreamer to pass full event or handle it here if it's generic.
                // Looking at AudioStreamer implementation in previous memory, it checks type.

                if (data.is_final) {
                    setTranscript(prev => prev + (prev ? ' ' : '') + data.text);
                    setInterimTranscript('');
                } else {
                    setInterimTranscript(data.text);
                }
            },
            onAgendaUpdate: (data) => {
                console.log("Agenda Update:", data);
                setAgendaAnalysis(data);
            },
            onError: (err) => setError(err),
            onStatusChange: (s) => setStatus(s)
        });

        await streamerRef.current.start();
    };

    const handleStop = () => {
        if (streamerRef.current) {
            streamerRef.current.stop();
        }
    };

    return (
        <div className="h-full flex flex-col bg-slate-50 dark:bg-slate-900">
            {/* Header */}
            <div className="px-8 py-6 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
                <div className="flex items-center justify-between">
                    <div>
                        <button onClick={() => navigate(`/meetings/${meetingId}`)} className="text-sm text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 mb-2 flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                            </svg>
                            Back to Meeting Details
                        </button>
                        <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
                            {meeting?.title || 'Loading...'}
                            <Badge variant={status === 'recording' ? 'danger' : 'neutral'} className="animate-pulse">
                                {status === 'recording' ? '🔴 LIVE' : 'OFFLINE'}
                            </Badge>
                        </h1>
                    </div>

                    <div className="flex gap-3">
                        {status === 'recording' ? (
                            <button
                                onClick={handleStop}
                                className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold shadow-lg shadow-red-500/30 transition-all flex items-center gap-2"
                            >
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                                </svg>
                                End Session
                            </button>
                        ) : (
                            <button
                                onClick={handleStart}
                                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold shadow-lg shadow-blue-500/30 transition-all flex items-center gap-2"
                            >
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                                </svg>
                                Join Live Session
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-hidden flex">
                {/* Transcript Area */}
                <div className="flex-1 p-8 overflow-y-auto">
                    <div className="max-w-3xl mx-auto">

                        {error && (
                            <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded-r-lg">
                                <div className="flex">
                                    <div className="flex-shrink-0">
                                        <svg className="h-5 w-5 text-red-500" viewBox="0 0 20 20" fill="currentColor">
                                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                        </svg>
                                    </div>
                                    <div className="ml-3">
                                        <p className="text-sm text-red-700">{error}</p>
                                    </div>
                                </div>
                            </div>
                        )}

                        <Card className="min-h-[500px] p-8 shadow-sm border border-slate-200 dark:border-slate-800">
                            <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-6 border-b pb-2">Live Transcript</h2>

                            <div className="space-y-4 font-mono text-sm leading-relaxed">
                                {transcript ? (
                                    <p className="text-slate-700 dark:text-slate-300 whitespace-pre-wrap">{transcript}</p>
                                ) : (
                                    <p className="text-slate-400 italic">Waiting for speech...</p>
                                )}

                                {interimTranscript && (
                                    <p className="text-slate-500 dark:text-slate-500 italic animate-pulse">
                                        {interimTranscript}
                                    </p>
                                )}
                                <div ref={transcriptEndRef} />
                            </div>
                        </Card>
                    </div>
                </div>

                {/* Right Sidebar - Agenda Monitor */}
                <div className="w-96 border-l border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 overflow-y-auto hidden xl:block transition-all">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500">Agenda Monitor</h2>
                        <Badge variant="neutral" className="text-xs">AI Agent Active</Badge>
                    </div>

                    {!agendaAnalysis ? (
                        <div className="text-center py-10 opacity-50">
                            <div className="animate-spin w-8 h-8 border-2 border-slate-300 border-t-blue-600 rounded-full mx-auto mb-3"></div>
                            <p className="text-xs text-slate-500">Waiting for analysis...</p>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {/* Current Focus */}
                            <div className="relative">
                                <div className="absolute -left-3 top-[-10px] bg-blue-100 text-blue-700 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
                                    Current Focus
                                </div>
                                <div className="p-4 pt-6 rounded-xl bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100 shadow-sm relative overflow-hidden">
                                    <div className="absolute top-0 right-0 p-2 opacity-10">
                                        <svg className="w-16 h-16 text-blue-600" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6l5.25 3.15-.75 1.23-6.5-3.9V7z" /></svg>
                                    </div>
                                    <div className="flex items-start gap-3 relative z-10">
                                        <div className="mt-1.5 w-2.5 h-2.5 rounded-full bg-blue-600 animate-ping" />
                                        <div className="w-2.5 h-2.5 rounded-full bg-blue-600 absolute left-0 top-1.5" />
                                        <div>
                                            <h3 className="font-bold text-slate-800 text-lg leading-tight">
                                                {agendaAnalysis.current_item_title || "General Discussion"}
                                            </h3>
                                            <p className="text-blue-700 text-xs mt-2 font-medium">
                                                Item #{agendaAnalysis.current_item_index !== null ? agendaAnalysis.current_item_index + 1 : "?"}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Decisions */}
                            {agendaAnalysis.decisions && agendaAnalysis.decisions.length > 0 && (
                                <div>
                                    <h3 className="text-xs font-bold uppercase text-slate-400 mb-3 flex items-center gap-2">
                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                        Captured Decisions
                                    </h3>
                                    <ul className="space-y-2">
                                        {agendaAnalysis.decisions.map((d: string, i: number) => (
                                            <li key={i} className="text-sm bg-green-50 text-green-900 border border-green-100 p-3 rounded-md flex gap-2">
                                                <span className="text-green-500 font-bold">✓</span>
                                                {d}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Progress Tracker (Example if we had full items list, but we rely on agent output for now) */}
                            {agendaAnalysis.completed_items_indices && agendaAnalysis.completed_items_indices.length > 0 && (
                                <div>
                                    <h3 className="text-xs font-bold uppercase text-slate-400 mb-3">Completed Items</h3>
                                    <div className="flex flex-wrap gap-2">
                                        {agendaAnalysis.completed_items_indices.map((idx: number) => (
                                            <span key={idx} className="bg-slate-100 text-slate-500 px-2 py-1 rounded text-xs line-through">
                                                Item {idx + 1}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
