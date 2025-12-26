import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAppSelector } from './hooks/useRedux'
import Login from './pages/auth/Login'
import CommandCenter from './pages/dashboard/CommandCenter'
import TwgWorkspace from './pages/workspace/TwgWorkspace'
import MyWorkspaces from './pages/workspace/MyWorkspaces'
import Integrations from './pages/settings/Integrations'
import ActionTracker from './pages/actions/ActionTracker'
import KnowledgeBase from './pages/knowledge/KnowledgeBase'
import DealPipeline from './pages/resource/DealPipeline'
import UserProfile from './pages/profile/UserProfile'
import AgentAssistant from './pages/assistant/AgentAssistant'
import SummitSchedule from './pages/schedule/SummitSchedule'
import DocumentLibrary from './pages/documents/DocumentLibrary'
import NotificationCenter from './pages/notifications/NotificationCenter'
import DashboardLayout from './layouts/DashboardLayout'

function App() {
    const theme = useAppSelector((state) => state.theme.mode)

    useEffect(() => {
        // Apply theme class to html element
        if (theme === 'dark') {
            document.documentElement.classList.add('dark')
        } else {
            document.documentElement.classList.remove('dark')
        }
    }, [theme])

    return (
        <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<DashboardLayout />}>
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="dashboard" element={<CommandCenter />} />
                <Route path="my-twgs" element={<MyWorkspaces />} />
                <Route path="workspace/:id" element={<TwgWorkspace />} />
                <Route path="documents" element={<DocumentLibrary />} />
                <Route path="schedule" element={<SummitSchedule />} />
                <Route path="knowledge-base" element={<KnowledgeBase />} />
                <Route path="deal-pipeline" element={<DealPipeline />} />
                <Route path="integrations" element={<Integrations />} />
                <Route path="actions" element={<ActionTracker />} />
                <Route path="profile" element={<UserProfile />} />
                <Route path="assistant" element={<AgentAssistant />} />
                <Route path="notifications" element={<NotificationCenter />} />
            </Route>
        </Routes>
    )
}

export default App
