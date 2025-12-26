import { createSlice, PayloadAction } from '@reduxjs/toolkit'

type ThemeMode = 'light' | 'dark'

interface ThemeState {
    mode: ThemeMode
}

const initialState: ThemeState = {
    mode: (localStorage.getItem('theme') as ThemeMode) || 'dark',
}

const themeSlice = createSlice({
    name: 'theme',
    initialState,
    reducers: {
        toggleTheme: (state) => {
            state.mode = state.mode === 'light' ? 'dark' : 'light'
            localStorage.setItem('theme', state.mode)
        },
        setTheme: (state, action: PayloadAction<ThemeMode>) => {
            state.mode = action.payload
            localStorage.setItem('theme', state.mode)
        },
    },
})

export const { toggleTheme, setTheme } = themeSlice.actions
export default themeSlice.reducer
