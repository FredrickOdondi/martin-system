import { API_URL } from './api';

type AudioStreamerConfig = {
    meetingId: string;
    onTranscript: (data: any) => void;
    onAgendaUpdate?: (data: any) => void;
    onError: (error: string) => void;
    onStatusChange: (status: 'connected' | 'disconnected' | 'recording') => void;
};

export class AudioStreamer {
    private socket: WebSocket | null = null;
    private config: AudioStreamerConfig;
    private token: string | null = null;

    constructor(config: AudioStreamerConfig) {
        this.config = config;
        this.token = localStorage.getItem('token');
    }

    async start() {
        try {
            // No microphone needed - we rely on Vexa sync

            // 2. Connect WebSocket
            // Handle relative API_URL or absolute
            const baseUrl = API_URL.replace(/^http/, 'ws');
            // If the URL is just 'https://...', replace with 'wss://...'
            // The regex /^http/ matches both 'http' and 'https' prefix start? No.
            // 'https'.match(/^http/); -> matches.
            // So 'https://foo'.replace(/^http/, 'ws') -> 'wss://foo'.
            // 'http://foo'.replace(/^http/, 'ws') -> 'ws://foo'.
            // This logic is actually correct if API_URL starts with http/https.

            const wsUrl = `${baseUrl}/meetings/${this.config.meetingId}/live?token=${this.token}`;

            this.socket = new WebSocket(wsUrl);

            this.socket.onopen = () => {
                this.config.onStatusChange('connected');
                // Removed: startRecording()
            };

            this.socket.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);

                    // Unified handler for live Meeting insights and Vexa transcripts
                    if (message.type === 'live_meeting_update') {
                        if (message.source === 'vexa_transcript_sync') {
                            // Map Vexa chunk to transcript area
                            this.config.onTranscript({
                                text: message.content,
                                is_final: true
                            });
                        } else {
                            // Map other insights (conflicts, answers) to agenda monitor
                            if (this.config.onAgendaUpdate) {
                                this.config.onAgendaUpdate(message);
                            }
                        }
                    } else if (message.type === 'transcript') {
                        // Legacy/Direct support
                        this.config.onTranscript(message.data);
                    } else if (message.type === 'agenda_update') {
                        if (this.config.onAgendaUpdate) {
                            this.config.onAgendaUpdate(message.data);
                        }
                    } else if (message.type === 'error') {
                        this.config.onError(message.message);
                    }
                } catch (e) {
                    console.error("WS Parse error", e);
                }
            };

            this.socket.onerror = (e) => {
                console.error("WebSocket Error", e);
                this.config.onStatusChange('disconnected');
                this.config.onError("WebSocket connection failed");
            };

            this.socket.onclose = () => {
                this.config.onStatusChange('disconnected');
                this.stop();
            };

        } catch (error: any) {
            console.error("AudioStreamer Error:", error);
            this.config.onError(error.message || "Failed to access microphone");
        }
    }

    // startRecording removed - purely listening to Vexa stream

    sendCommand(data: any) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(data));
        } else {
            console.warn("WebSocket not open, cannot send command");
        }
    }

    stop() {
        if (this.socket) {
            // Only attempt to close if not already closed or closing
            if (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING) {
                this.socket.close();
            }
            this.socket = null;
        }
        this.config.onStatusChange('disconnected');
    }
}
