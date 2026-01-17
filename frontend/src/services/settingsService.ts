import api from './api';

export interface SystemSettings {
    id: string;
    enable_google_calendar: boolean;
    enable_zoom: boolean;
    enable_teams: boolean;
    llm_provider: 'openai' | 'github' | 'gemini' | 'azure';
    llm_model: string;
    smtp_config?: any;
    has_google_creds: boolean;
    has_zoom_creds: boolean;
    has_teams_creds: boolean;
    updated_at: string;
}

export interface SystemSettingsUpdate {
    enable_google_calendar?: boolean;
    enable_zoom?: boolean;
    enable_teams?: boolean;
    llm_provider?: string;
    llm_model?: string;
    google_credentials_json?: string;
    zoom_credentials_json?: string;
    teams_credentials_json?: string;
}

export interface TwgSettings {
    id: string;
    twg_id: string;
    meeting_cadence?: string;
    custom_templates?: any;
    notification_preferences?: any;
    updated_at: string;
}

export const settingsService = {
    // --- System Settings (Admin) ---
    getSystemSettings: async (): Promise<SystemSettings> => {
        const response = await api.get('/settings/system');
        return response.data;
    },

    updateSystemSettings: async (data: SystemSettingsUpdate): Promise<SystemSettings> => {
        const response = await api.patch('/settings/system', data);
        return response.data;
    },

    // --- TWG Settings (Facilitator) ---
    getTwgSettings: async (twgId: string): Promise<TwgSettings> => {
        const response = await api.get(`/settings/twg/${twgId}`);
        return response.data;
    },

    updateTwgSettings: async (twgId: string, data: Partial<TwgSettings>): Promise<TwgSettings> => {
        const response = await api.patch(`/settings/twg/${twgId}`, data);
        return response.data;
    }
};
