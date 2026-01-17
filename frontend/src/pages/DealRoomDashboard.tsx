import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { pipelineService } from '../services/pipelineService';
import { Project } from '../types/pipeline';

const DealRoomDashboard: React.FC = () => {
    const navigate = useNavigate();
    const [flagshipProjects, setFlagshipProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchFlagship = async () => {
            // Currently no direct filter for flagship in listProjects, so we fetch all and filter client side
            // In a real app we'd add ?is_flagship=true to API
            try {
                const allProjects = await pipelineService.listProjects();
                const flagged = allProjects.filter(p => p.is_flagship);
                setFlagshipProjects(flagged);
            } catch (e) {
                console.error("Failed to load flagship projects", e);
            } finally {
                setLoading(false);
            }
        };
        fetchFlagship();
    }, []);

    return (
        <div className="max-w-[1200px] mx-auto space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">Executive Dashboard</h2>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Curated opportunities and engagement.</p>
                </div>
                <div className="flex gap-3">
                    <button onClick={() => navigate('/schedule')} className="px-4 py-2 bg-primary text-white text-sm font-bold rounded-lg shadow-md hover:bg-blue-700 transition-colors">
                        Schedule Meeting
                    </button>
                </div>
            </div>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gradient-to-br from-purple-600 to-indigo-700 rounded-xl p-6 text-white shadow-lg relative overflow-hidden">
                    <span className="material-symbols-outlined absolute top-4 right-4 text-white/20 text-6xl">campaign</span>
                    <div className="text-3xl font-bold mb-1">{flagshipProjects.length}</div>
                    <div className="text-purple-100 text-sm font-medium">Flagship Opportunities</div>
                </div>
                <div className="bg-white dark:bg-slate-800 rounded-xl p-6 border border-slate-200 dark:border-slate-700 shadow-sm relative overflow-hidden">
                    <span className="material-symbols-outlined absolute top-4 right-4 text-slate-100 dark:text-slate-700 text-6xl">handshake</span>
                    <div className="text-3xl font-bold text-slate-900 dark:text-white mb-1">12</div>
                    <div className="text-slate-500 text-sm font-medium">Active Discussions</div>
                </div>
                <div className="bg-white dark:bg-slate-800 rounded-xl p-6 border border-slate-200 dark:border-slate-700 shadow-sm relative overflow-hidden">
                    <span className="material-symbols-outlined absolute top-4 right-4 text-slate-100 dark:text-slate-700 text-6xl">calendar_month</span>
                    <div className="text-3xl font-bold text-slate-900 dark:text-white mb-1">5</div>
                    <div className="text-slate-500 text-sm font-medium">Upcoming Meetings</div>
                </div>
            </div>

            {/* Featured Projects */}
            <div>
                <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                    <span className="material-symbols-outlined text-amber-500">star</span>
                    Featured Projects
                </h2>

                {loading ? (
                    <div className="text-center py-12 text-slate-500">Loading flagship projects...</div>
                ) : flagshipProjects.length === 0 ? (
                    <div className="text-center py-12 bg-slate-50 border border-dashed border-slate-300 rounded-xl text-slate-500">
                        No flagship projects marked yet. Go to Deal Pipeline to select featured projects.
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {flagshipProjects.map(project => (
                            <div key={project.id} onClick={() => navigate(`/deal-pipeline/${project.id}`)} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5 cursor-pointer hover:shadow-md hover:border-primary/50 transition-all group">
                                <div className="flex justify-between items-start mb-3">
                                    <span className="bg-slate-100 text-slate-600 text-[10px] font-bold px-2 py-1 rounded uppercase tracking-wider">{project.status.replace('_', ' ')}</span>
                                    <span className="text-xs font-bold text-slate-400">{project.lead_country || 'Regional'}</span>
                                </div>
                                <h3 className="font-bold text-slate-900 dark:text-white mb-2 group-hover:text-primary transition-colors">{project.name}</h3>
                                <p className="text-sm text-slate-500 line-clamp-2 mb-4">{project.description}</p>
                                <div className="flex items-center justify-between text-xs font-medium text-slate-500 pt-4 border-t border-slate-100 dark:border-slate-700">
                                    <span>Invest: ${(project.investment_size / 1000000).toFixed(1)}M</span>
                                    <div className="flex items-center gap-1 text-emerald-600">
                                        <span className="material-symbols-outlined text-[14px]">check_circle</span>
                                        {project.readiness_score}/100
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Upcoming Meetings Placeholder */}
            <div>
                <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Upcoming Schedule</h2>
                <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden divide-y divide-slate-100">
                    {[1, 2].map(i => (
                        <div key={i} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                            <div className="flex gap-4">
                                <div className="flex flex-col items-center justify-center bg-blue-50 text-blue-800 rounded-lg w-12 h-12">
                                    <span className="text-xs font-bold uppercase">Oct</span>
                                    <span className="text-lg font-bold">{14 + i}</span>
                                </div>
                                <div>
                                    <h4 className="font-bold text-slate-900 dark:text-white text-sm">Investment Review: Grid Expansion</h4>
                                    <p className="text-xs text-slate-500">10:00 AM • Zoom</p>
                                </div>
                            </div>
                            <button className="text-sm text-primary font-bold hover:underline">Join</button>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default DealRoomDashboard;
