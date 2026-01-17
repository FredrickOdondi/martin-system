import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface UiState {
    notification: {
        type: 'success' | 'error' | 'info' | 'warning';
        message: string;
    } | null;
}

const initialState: UiState = {
    notification: null,
};

const uiSlice = createSlice({
    name: 'ui',
    initialState,
    reducers: {
        setNotification: (state, action: PayloadAction<{ type: 'success' | 'error' | 'info' | 'warning'; message: string } | null>) => {
            state.notification = action.payload;
        },
        clearNotification: (state) => {
            state.notification = null;
        },
    },
});

export const { setNotification, clearNotification } = uiSlice.actions;
export default uiSlice.reducer;
