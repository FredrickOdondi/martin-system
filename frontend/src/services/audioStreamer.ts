import { API_URL } from './api';

type AudioStreamerConfig = {
    meetingId: string;
    onTranscript: (data: any) => void;
    onAgendaUpdate?: (data: any) => void;
    onError: (error: string) => void;
    onStatusChange: (status: 'connected' | 'disconnected' | 'recording') => void;
};

export class AudioStreamer {
    private mediaRecorder: MediaRecorder | null = null;
    private socket: WebSocket | null = null;
    private config: AudioStreamerConfig;
    private stream: MediaStream | null = null;
    private token: string | null = null;

    constructor(config: AudioStreamerConfig) {
        this.config = config;
        this.token = localStorage.getItem('token');
    }

    async start() {
        try {
            // 1. Get Microphone Access
            this.stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: 16000, // Deepgram/Google preferred
                }
            });

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
                this.startRecording();
            };

            this.socket.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    if (message.type === 'transcript') {
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

    private startRecording() {
        if (!this.stream || !this.socket) return;

        // Create MediaRecorder
        // Use a supported mime type. Chrome supports audio/webm;codecs=opus
        const mimeType = 'audio/webm;codecs=opus';
        if (!MediaRecorder.isTypeSupported(mimeType)) {
            console.warn(`${mimeType} not supported, falling back to default`);
        }

        this.mediaRecorder = new MediaRecorder(this.stream, {
            mimeType: MediaRecorder.isTypeSupported(mimeType) ? mimeType : undefined
        });

        this.mediaRecorder.ondataavailable = async (event) => {
            if (event.data.size > 0 && this.socket?.readyState === WebSocket.OPEN) {
                this.socket.send(event.data);
            }
        };

        // Send chunks every 250ms
        this.mediaRecorder.start(250);
        this.config.onStatusChange('recording');
    }

    stop() {
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        this.config.onStatusChange('disconnected');
    }
}
