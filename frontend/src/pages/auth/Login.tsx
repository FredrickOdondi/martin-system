import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Input } from '../../components/ui'
import { useAppDispatch } from '../../hooks/useRedux'
import { setCredentials } from '../../store/slices/authSlice'

export default function Login() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const navigate = useNavigate()
    const dispatch = useAppDispatch()

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)

        // Simulate login
        setTimeout(() => {
            dispatch(setCredentials({
                user: {
                    id: '1',
                    name: 'Admin User',
                    email: email,
                    role: 'administrator'
                },
                token: 'fake-jwt-token'
            }))
            setIsLoading(false)
            navigate('/dashboard')
        }, 1000)
    }

    return (
        <div className="flex h-screen bg-[#020617] text-white">
            {/* Left side - Visuals */}
            <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-blue-950">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-blue-500/20 via-transparent to-transparent"></div>

                {/* Abstract Globe/Network visualization placeholder */}
                <div className="absolute inset-0 flex items-center justify-center opacity-40">
                    <svg className="w-full h-full p-20" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
                        <defs>
                            <radialGradient id="grad1" cx="50%" cy="50%" r="50%" fx="50%" fy="50%">
                                <stop offset="0%" style={{ stopColor: '#3b82f6', stopOpacity: 0.5 }} />
                                <stop offset="100%" style={{ stopColor: '#1d4ed8', stopOpacity: 0 }} />
                            </radialGradient>
                        </defs>
                        <circle cx="100" cy="100" r="80" fill="url(#grad1)" />
                        <circle cx="100" cy="100" r="80" stroke="#3b82f6" strokeWidth="0.5" fill="none" />
                        <path d="M20 100 Q 100 20 180 100" stroke="#3b82f6" strokeWidth="0.2" fill="none" />
                        <path d="M20 100 Q 100 180 180 100" stroke="#3b82f6" strokeWidth="0.2" fill="none" />
                        <path d="M100 20 Q 20 100 100 180" stroke="#3b82f6" strokeWidth="0.2" fill="none" />
                        <path d="M100 20 Q 180 100 100 180" stroke="#3b82f6" strokeWidth="0.2" fill="none" />
                    </svg>
                </div>

                <div className="relative z-10 flex flex-col justify-end p-16 space-y-6">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                            <span className="font-bold text-lg">E</span>
                        </div>
                        <span className="text-xl font-display font-semibold">ECOWAS SUMMIT TWG</span>
                    </div>
                    <h1 className="text-5xl font-display font-bold leading-tight">
                        Empowering Regional Cooperation through AI-Driven Insights
                    </h1>
                    <p className="text-blue-200 text-lg max-w-lg">
                        Welcome to the Technical Working Group Support System. Securely access real-time data analysis and strategic planning tools.
                    </p>
                    <div className="flex gap-2">
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        <div className="w-2 h-2 bg-slate-700 rounded-full"></div>
                        <div className="w-2 h-2 bg-slate-700 rounded-full"></div>
                    </div>
                </div>
            </div>

            {/* Right side - Form */}
            <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-[#020617]">
                <div className="w-full max-w-md space-y-8">
                    <div className="flex justify-end">
                        <div className="flex items-center gap-2 px-3 py-1 bg-slate-800/50 border border-slate-700 rounded-full text-xs text-slate-400">
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 00-2 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                            </svg>
                            SECURE ACCESS
                        </div>
                    </div>

                    <div className="space-y-2">
                        <h2 className="text-3xl font-display font-bold">Log In</h2>
                        <p className="text-slate-400">Enter your official credentials to access the TWG workspace.</p>
                    </div>

                    <form onSubmit={handleLogin} className="space-y-6">
                        <div className="space-y-4">
                            <Input
                                label="Official Email"
                                type="email"
                                placeholder="name@ecowas.int"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                className="bg-slate-900 border-slate-700 text-white placeholder:text-slate-600 focus:ring-blue-500"
                            />
                            <div className="space-y-1">
                                <Input
                                    label="Password"
                                    type="password"
                                    placeholder="••••••••"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    className="bg-slate-900 border-slate-700 text-white placeholder:text-slate-600 focus:ring-blue-500"
                                />
                                <div className="flex justify-end">
                                    <button type="button" className="text-sm text-slate-400 hover:text-blue-400 transition-colors">
                                        Forgot Password?
                                    </button>
                                </div>
                            </div>
                        </div>

                        <Button
                            type="submit"
                            isLoading={isLoading}
                            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-lg shadow-blue-900/20 flex items-center justify-center gap-2"
                        >
                            Access Dashboard
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                            </svg>
                        </Button>
                    </form>

                    <div className="pt-8 border-t border-slate-800 text-center">
                        <p className="text-xs text-slate-500">
                            ECOWAS Summit © 2024. Authorized Personnel Only.
                        </p>
                        <p className="text-xs text-slate-600 mt-1">
                            By logging in, you agree to our Terms of Service and Privacy Policy.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
