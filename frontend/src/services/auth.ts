import api from './api';
import { UserLogin, LoginResponse, User } from '../types/auth';

// Add these types to types/auth.ts if missing, or we can define here locally if just for transport
// But we should use the ones we likely need to define or import

export interface RegisterData {
    email: string;
    password: string;
    full_name: string;
    organization?: string;
}

export const authService = {
    async login(credentials: UserLogin) {
        const response = await api.post<LoginResponse>('/auth/login', credentials);
        return response.data;
    },

    async register(data: RegisterData) {
        const response = await api.post('/auth/register', data);
        return response.data;
    },

    async loginWithGoogle(idToken: string) {
        const response = await api.post<LoginResponse>('/auth/google', { id_token: idToken });
        return response.data;
    },

    async logout(refreshToken: string) {
        return api.post('/auth/logout', { refresh_token: refreshToken });
    },

    async getCurrentUser() {
        const response = await api.get<User>('/auth/me');
        return response.data;
    },

    async forgotPassword(email: string) {
        const response = await api.post('/auth/forgot-password', { email });
        return response.data;
    },

    async resetPassword(token: string, newPassword: string) {
        const response = await api.post('/auth/reset-password', {
            token,
            new_password: newPassword
        });
        return response.data;
    },

    async changePassword(currentPassword: string, newPassword: string) {
        return api.post('/auth/change-password', {
            current_password: currentPassword,
            new_password: newPassword
        });
    }
};
