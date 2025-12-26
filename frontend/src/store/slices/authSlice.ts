import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface User {
    id: string
    name: string
    email: string
    role: string
    avatar?: string
}

interface AuthState {
    user: User | null
    isAuthenticated: boolean
    token: string | null
}

const initialState: AuthState = {
    user: null,
    isAuthenticated: false,
    token: localStorage.getItem('token'),
}

const authSlice = createSlice({
    name: 'auth',
    initialState,
    reducers: {
        setCredentials: (state, action: PayloadAction<{ user: User; token: string }>) => {
            state.user = action.payload.user
            state.token = action.payload.token
            state.isAuthenticated = true
            localStorage.setItem('token', action.payload.token)
        },
        logout: (state) => {
            state.user = null
            state.token = null
            state.isAuthenticated = false
            localStorage.removeItem('token')
        },
    },
})

export const { setCredentials, logout } = authSlice.actions
export default authSlice.reducer
