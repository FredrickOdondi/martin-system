import axios from 'axios';
import { store } from '../store';
import { logout } from '../store/slices/authSlice';

// Create axios instance with base URL
// In VITE, we use import.meta.env for environment variables
let apiUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1').trim();

// Fix Mixed Content: Force HTTPS for Railway production URLs
// This handles both http:// URLs and ensures railway.app always uses https://
if (apiUrl.toLowerCase().includes('railway.app')) {
    // Remove any existing protocol
    apiUrl = apiUrl.replace(/^https?:\/\//i, '');
    // Add https://
    apiUrl = 'https://' + apiUrl;
}

// Debug logging (will be visible in browser console)
console.log('[API Config] Final API URL:', apiUrl);

const API_URL = apiUrl;

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor for adding the auth token
api.interceptors.request.use(
    (config) => {
        // Try to get token from Redux store first, then fall back to localStorage
        let token = store.getState().auth.token;
        if (!token) {
            token = localStorage.getItem('token');
        }
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for handling 401 (Unauthorized)
api.interceptors.response.use(
    (response) => {
        return response;
    },
    async (error) => {
        const originalRequest = error.config;

        // If error is 401 and we haven't tried to refresh already
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            // Dispatch logout action to clear state and redirect to login
            // Ideally implementation would try to refresh token here
            store.dispatch(logout());
            return Promise.reject(error);
        }

        return Promise.reject(error);
    }
);

export default api;

export const meetings = {
    list: (skip = 0, limit = 100) => api.get(`/meetings/?skip=${skip}&limit=${limit}`),
    get: (id: string) => api.get(`/meetings/${id}`),
    create: (data: any) => api.post('/meetings/', data),
    update: (id: string, data: any) => api.patch(`/meetings/${id}`, data),
    schedule: (id: string) => api.post(`/meetings/${id}/schedule`),

    // Operational Tools
    getAgenda: (id: string) => api.get(`/meetings/${id}/agenda`),
    updateAgenda: (id: string, data: { content: string }) => api.post(`/meetings/${id}/agenda`, data),

    addParticipants: (id: string, participants: Array<{ user_id?: string, email?: string, name?: string }>) =>
        api.post(`/meetings/${id}/participants`, participants),

    updateRsvp: (meetingId: string, participantId: string, status: string) =>
        api.put(`/meetings/${meetingId}/participants/${participantId}/rsvp`, { rsvp_status: status }),

    getMinutes: (id: string) => api.get(`/meetings/${id}/minutes`),
    updateMinutes: (id: string, data: { content: string, status?: string }) => api.post(`/meetings/${id}/minutes`, data),
};
