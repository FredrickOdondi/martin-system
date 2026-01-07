import { useState, useEffect } from 'react'
import { userService, UserUpdateData } from '../../services/userService'
import { twgs as twgService } from '../../services/api'
import { User, UserRole } from '../../types/auth'
import { Avatar } from '../../components/ui'
import { toast } from 'react-toastify'
import ModernLayout from '../../layouts/ModernLayout'

import { useAppSelector } from '../../hooks/useRedux'

export default function TeamManagement() {
    const currentUser = useAppSelector((state) => state.auth.user)
    const [users, setUsers] = useState<User[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [searchTerm, setSearchTerm] = useState('')
    const [activeTab, setActiveTab] = useState<'users' | 'governance'>('users')

    // Governance State
    const [twgs, setTwgs] = useState<any[]>([])
    const [loadingTwgs, setLoadingTwgs] = useState(false)

    useEffect(() => {
        loadUsers()
    }, [])

    const loadUsers = async () => {
        setIsLoading(true)
        try {
            const data = await userService.getUsers()
            setUsers(data)
        } catch (error) {
            console.error('Failed to load users', error)
            toast.error('Failed to load users')
        } finally {
            setIsLoading(false)
        }
    }

    const loadTwgs = async () => {
        setLoadingTwgs(true)
        try {
            const response = await twgService.list()
            setTwgs(response.data)
        } catch (error) {
            console.error('Failed to load TWGs', error)
            toast.error('Failed to load TWGs')
        } finally {
            setLoadingTwgs(false)
        }
    }

    useEffect(() => {
        if (activeTab === 'governance') {
            loadTwgs()
        }
    }, [activeTab])

    const handleUpdateTwg = async (twgId: string, data: any) => {
        try {
            await twgService.update(twgId, data)
            toast.success('TWG Leadership updated')
            loadTwgs()
        } catch (error) {
            console.error('Failed to update TWG', error)
            toast.error('Failed to update TWG')
        }
    }

    const handleUpdateUser = async (userId: string, data: UserUpdateData) => {
        try {
            await userService.updateUser(userId, data)
            toast.success('User updated successfully')
            loadUsers()
        } catch (error: any) {
            const message = error.response?.data?.detail || 'Failed to update user'
            console.error('Failed to update user:', error)
            toast.error(message)
        }
    }

    const handleDeleteUser = async (userId: string) => {
        if (!window.confirm('Are you sure you want to delete this user?')) return
        try {
            await userService.deleteUser(userId)
            toast.success('User deleted successfully')
            loadUsers()
        } catch (error: any) {
            const message = error.response?.data?.detail || 'Failed to delete user'
            console.error('Failed to delete user:', error)
            toast.error(message)
        }
    }

    const filteredUsers = users.filter(user =>
        user.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.email.toLowerCase().includes(searchTerm.toLowerCase())
    )

    if (isLoading) {
        return (
            <ModernLayout>
                <div className="flex items-center justify-center h-64">
                    <div className="w-8 h-8 border-4 border-[#1152d4] border-t-transparent rounded-full animate-spin"></div>
                </div>
            </ModernLayout>
        )
    }

    return (
        <ModernLayout>
            <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
                <div>
                    <h1 className="text-3xl font-black text-[#0d121b] dark:text-white tracking-tight">Team Management</h1>
                    <p className="text-[#4c669a] dark:text-[#a0aec0] font-medium">Manage user roles, access permissions, and account status.</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={loadUsers}
                        className="px-4 py-2 bg-white dark:bg-[#1a202c] border border-[#e7ebf3] dark:border-[#2d3748] rounded-lg text-sm font-bold text-[#0d121b] dark:text-white hover:bg-gray-50 dark:hover:bg-[#2d3748] transition-colors shadow-sm flex items-center gap-2"
                    >
                        <span className="material-symbols-outlined text-sm">refresh</span>
                        Refresh
                    </button>
                    <button className="px-4 py-2 bg-[#1152d4] hover:bg-[#0e44b1] text-white rounded-lg text-sm font-bold transition-all shadow-md shadow-blue-500/20 flex items-center gap-2">
                        <span className="material-symbols-outlined text-sm">person_add</span>
                        Add Member
                    </button>
                </div>
            </div>



            {/* Tabs */}
            <div className="flex gap-6 border-b border-[#e7ebf3] dark:border-[#2d3748] mb-6">
                <button
                    onClick={() => setActiveTab('users')}
                    className={`pb-3 text-sm font-bold border-b-2 transition-colors ${activeTab === 'users'
                        ? 'border-[#1152d4] text-[#1152d4] dark:text-blue-400 dark:border-blue-400'
                        : 'border-transparent text-[#4c669a] dark:text-[#a0aec0] hover:text-[#0d121b] dark:hover:text-white'
                        }`}
                >
                    Users & Roles
                </button>
                <button
                    onClick={() => setActiveTab('governance')}
                    className={`pb-3 text-sm font-bold border-b-2 transition-colors ${activeTab === 'governance'
                        ? 'border-[#1152d4] text-[#1152d4] dark:text-blue-400 dark:border-blue-400'
                        : 'border-transparent text-[#4c669a] dark:text-[#a0aec0] hover:text-[#0d121b] dark:hover:text-white'
                        }`}
                >
                    TWG Governance
                </button>
            </div>

            {
                activeTab === 'users' ? (
                    <div className="bg-white dark:bg-[#1a202c] rounded-xl border border-[#e7ebf3] dark:border-[#2d3748] shadow-sm overflow-hidden mb-6">
                        <div className="p-4 border-b border-[#e7ebf3] dark:border-[#2d3748] bg-gray-50/50 dark:bg-gray-800/10">
                            <div className="relative max-w-md">
                                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[#4c669a] text-lg">search</span>
                                <input
                                    type="text"
                                    placeholder="Search members by name or email..."
                                    className="w-full pl-10 pr-4 py-2 bg-white dark:bg-[#2d3748] border border-[#e7ebf3] dark:border-[#4a5568] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#1152d4]/20 focus:border-[#1152d4] transition-all"
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                />
                            </div>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="bg-gray-50 dark:bg-[#2d3748]/30">
                                        <th className="px-6 py-4 text-xs font-bold text-[#4c669a] dark:text-[#a0aec0] uppercase tracking-wider">User Member</th>
                                        <th className="px-6 py-4 text-xs font-bold text-[#4c669a] dark:text-[#a0aec0] uppercase tracking-wider">Role</th>
                                        <th className="px-6 py-4 text-xs font-bold text-[#4c669a] dark:text-[#a0aec0] uppercase tracking-wider">Status</th>
                                        <th className="px-6 py-4 text-xs font-bold text-[#4c669a] dark:text-[#a0aec0] uppercase tracking-wider text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-[#e7ebf3] dark:divide-[#2d3748]">
                                    {filteredUsers.map((user) => (
                                        <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-[#2d3748]/30 transition-colors group">
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="relative">
                                                        <Avatar alt={user.full_name} size="md" />
                                                        {user.is_active && (
                                                            <div className="absolute -bottom-0.5 -right-0.5 size-3 bg-green-500 border-2 border-white dark:border-[#1a202c] rounded-full"></div>
                                                        )}
                                                    </div>
                                                    <div>
                                                        <div className="font-bold text-[#0d121b] dark:text-white text-sm">{user.full_name}</div>
                                                        <div className="text-xs text-[#4c669a] dark:text-[#a0aec0]">{user.email}</div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <select
                                                    className="bg-white dark:bg-[#2d3748] border border-[#e7ebf3] dark:border-[#4a5568] text-xs font-medium rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-[#1152d4]/20 text-[#0d121b] dark:text-white"
                                                    value={user.role}
                                                    onChange={(e) => handleUpdateUser(user.id, { role: e.target.value as UserRole })}
                                                >
                                                    {Object.values(UserRole).map((role) => (
                                                        <option key={role} value={role}>
                                                            {role.replace(/_/g, ' ').toUpperCase()}
                                                        </option>
                                                    ))}
                                                </select>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${user.is_active
                                                    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                                                    : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                                                    }`}>
                                                    {user.is_active ? 'Active' : 'Inactive'}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <div className="flex justify-end gap-2">
                                                    <button
                                                        onClick={() => handleUpdateUser(user.id, { is_active: !user.is_active })}
                                                        disabled={user.id === currentUser?.id}
                                                        className={`p-2 rounded-lg transition-colors ${user.is_active
                                                            ? 'text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-900/20'
                                                            : 'text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20'
                                                            } ${user.id === currentUser?.id ? 'opacity-50 cursor-not-allowed' : ''}`}
                                                        title={user.id === currentUser?.id ? 'You cannot deactivate yourself' : (user.is_active ? 'Deactivate' : 'Activate')}
                                                    >
                                                        <span className="material-symbols-outlined text-[20px]">
                                                            {user.is_active ? 'person_off' : 'person_check'}
                                                        </span>
                                                    </button>
                                                    <button
                                                        onClick={() => handleDeleteUser(user.id)}
                                                        disabled={user.id === currentUser?.id}
                                                        className={`p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors ${user.id === currentUser?.id ? 'opacity-50 cursor-not-allowed' : ''
                                                            }`}
                                                        title={user.id === currentUser?.id ? 'You cannot delete yourself' : 'Delete User'}
                                                    >
                                                        <span className="material-symbols-outlined text-[20px]">delete</span>
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {filteredUsers.length === 0 && (
                            <div className="p-12 text-center">
                                <div className="size-16 bg-gray-100 dark:bg-[#2d3748] rounded-full flex items-center justify-center mx-auto mb-4 text-[#4c669a]">
                                    <span className="material-symbols-outlined text-3xl">group_off</span>
                                </div>
                                <h3 className="text-lg font-bold text-[#0d121b] dark:text-white">No members found</h3>
                                <p className="text-[#4c669a] dark:text-[#a0aec0]">Try adjusting your search criteria or add a new member.</p>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="space-y-6">
                        {loadingTwgs && (
                            <div className="flex justify-center p-12">
                                <div className="w-8 h-8 border-4 border-[#1152d4] border-t-transparent rounded-full animate-spin"></div>
                            </div>
                        )}
                        {!loadingTwgs && twgs.map((twg) => (
                            <div key={twg.id} className="bg-white dark:bg-[#1a202c] rounded-xl border border-[#e7ebf3] dark:border-[#2d3748] p-6 shadow-sm">
                                <div className="flex justify-between items-start mb-6">
                                    <div>
                                        <h3 className="text-lg font-bold text-[#0d121b] dark:text-white">{twg.name}</h3>
                                        <p className="text-sm text-[#4c669a] dark:text-[#a0aec0] uppercase tracking-wider font-bold mt-1">
                                            Pillar: {twg.pillar?.replace(/_/g, ' ')}
                                        </p>
                                    </div>
                                    <div className="px-3 py-1 bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 rounded-full text-xs font-bold uppercase">
                                        {twg.status}
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    {/* Political Lead */}
                                    <div className="p-4 bg-blue-50 dark:bg-blue-900/10 rounded-xl border border-blue-100 dark:border-blue-800/30">
                                        <h4 className="text-xs font-black text-blue-600 dark:text-blue-400 uppercase tracking-widest mb-3">Political Lead</h4>
                                        <select
                                            className="w-full bg-white dark:bg-[#2d3748] border border-blue-200 dark:border-blue-800 rounded-lg px-3 py-2 text-sm font-medium focus:ring-2 focus:ring-blue-500 text-[#0d121b] dark:text-white"
                                            value={twg.political_lead_id || ''}
                                            onChange={(e) => handleUpdateTwg(twg.id, { political_lead_id: e.target.value || null })}
                                        >
                                            <option value="">Unassigned</option>
                                            {users.map(u => (
                                                <option key={u.id} value={u.id}>{u.full_name} ({u.role})</option>
                                            ))}
                                        </select>
                                    </div>

                                    {/* Technical Lead */}
                                    <div className="p-4 bg-emerald-50 dark:bg-emerald-900/10 rounded-xl border border-emerald-100 dark:border-emerald-800/30">
                                        <h4 className="text-xs font-black text-emerald-600 dark:text-emerald-400 uppercase tracking-widest mb-3">Technical Lead</h4>
                                        <select
                                            className="w-full bg-white dark:bg-[#2d3748] border border-emerald-200 dark:border-emerald-800 rounded-lg px-3 py-2 text-sm font-medium focus:ring-2 focus:ring-emerald-500 text-[#0d121b] dark:text-white"
                                            value={twg.technical_lead_id || ''}
                                            onChange={(e) => handleUpdateTwg(twg.id, { technical_lead_id: e.target.value || null })}
                                        >
                                            <option value="">Unassigned</option>
                                            {users.map(u => (
                                                <option key={u.id} value={u.id}>{u.full_name} ({u.role})</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                            </div>
                        ))}
                        {twgs.length === 0 && (
                            <div className="p-12 text-center text-slate-400">
                                No TWGs found. System seed required?
                            </div>
                        )}
                    </div>
                )
            }
        </ModernLayout >
    )
}
