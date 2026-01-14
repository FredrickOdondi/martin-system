import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { pipelineService } from '../services/pipelineService';
import { Project, InvestorMatch, InvestorMatchStatus } from '../types/pipeline';

const ProjectDetails: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'overview' | 'financials' | 'documents' | 'history' | 'matches'>('overview');
  const [project, setProject] = useState<Project | null>(null);
  const [matches, setMatches] = useState<InvestorMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMatches, setLoadingMatches] = useState(false);
  const [triggeringMatch, setTriggeringMatch] = useState(false);

  // AI Insight State
  const [aiInsight, setAiInsight] = useState<string>('');
  const [aiRecommendation, setAiRecommendation] = useState<string>('');
  const [isLoadingInsight, setIsLoadingInsight] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      if (!projectId) return;
      setLoading(true);
      try {
        const data = await pipelineService.getProject(projectId);
        setProject(data);

        // Fetch matches if available, but don't block main load
        fetchMatches(projectId);
      } catch (error) {
        console.error("Failed to fetch project", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [projectId]);

  const fetchMatches = async (id: string) => {
    setLoadingMatches(true);
    try {
      const matchData = await pipelineService.getMatches(id);
      setMatches(matchData);
    } catch (e) {
      console.error("Failed to load matches", e);
    } finally {
      setLoadingMatches(false);
    }
  };

  const handleTriggerMatching = async () => {
    if (!project) return;
    setTriggeringMatch(true);
    try {
      await pipelineService.triggerMatching(project.id);
      await fetchMatches(project.id);
      alert("Investor matching triggered successfully!");
    } catch (error: any) { // Changed 'error' to 'any' to allow access to 'response'
      let errorMessage = 'Failed to trigger matching. Please try again.';
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        } else {
          errorMessage = JSON.stringify(error.response.data.detail);
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      console.error("Failed to trigger matching", error);
      alert(errorMessage); // Use the constructed error message
    } finally {
      setTriggeringMatch(false);
    }
  };

  const handleUpdateMatchStatus = async (matchId: string, newStatus: InvestorMatchStatus) => {
    try {
      await pipelineService.updateMatchStatus(matchId, { status: newStatus });
      // Optimistic update
      setMatches(prev => prev.map(m => m.match_id === matchId ? { ...m, status: newStatus } : m));
      if (newStatus === InvestorMatchStatus.INTERESTED) {
        alert("Status updated to 'Interested'. Protocol Agent has been notified to schedule a meeting.");
      }
    } catch (error) {
      console.error("Failed to update match status", error);
      alert("Failed to update status.");
    }
  };

  const fetchAIInsights = async () => {
    if (!project) return;
    setIsLoadingInsight(true);
    // ... existing AI logic adapted for real project data ...
    // Placeholder for now as the logic was largely similar
    setTimeout(() => {
      setAiInsight(`Readiness Score is ${project.readiness_score >= 80 ? 'high' : 'moderate'} (${project.readiness_score}/100). AfCEN Score: ${project.afcen_score?.toFixed(1)}`);
      setAiRecommendation('Review pending investor matches in the Deal Room tab.');
      setIsLoadingInsight(false);
    }, 1500);
  };

  useEffect(() => {
    if (project) fetchAIInsights();
  }, [project]);


  const getStatusColor = (status: string) => {
    switch (status) {
      case 'identified': return 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200 border-slate-200 dark:border-slate-700';
      case 'vetting': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200 border-blue-200 dark:border-blue-800';
      case 'due_diligence': return 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-200 border-purple-200 dark:border-purple-800';
      case 'deal_room': return 'bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-200 border-pink-200 dark:border-pink-800';
      case 'financing': return 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-200 border-indigo-200 dark:border-indigo-800';
      case 'bankable': return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200 border-green-200 dark:border-green-800';
      default: return 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200 border-amber-200 dark:border-amber-800';
    }
  };

  const getProgressColor = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-primary';
    return 'bg-orange-500';
  };

  const formatCurrency = (amount?: number) => {
    if (!amount) return 'N/A';
    if (amount >= 1000000000) return `$${(amount / 1000000000).toFixed(1)}B`;
    if (amount >= 1000000) return `$${(amount / 1000000).toFixed(1)}M`;
    return `$${amount.toLocaleString()}`;
  };

  if (loading || !project) {
    return <div className="p-12 text-center">Loading Project...</div>;
  }

  return (
    <div className="max-w-[1200px] mx-auto space-y-6">
      {/* Breadcrumbs */}
      <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
        <button onClick={() => navigate('/dashboard')} className="hover:text-primary transition-colors">
          Home
        </button>
        <span className="material-symbols-outlined text-[16px]">chevron_right</span>
        <button onClick={() => navigate('/deal-pipeline')} className="hover:text-primary transition-colors">
          Deal Pipeline
        </button>
        <span className="material-symbols-outlined text-[16px]">chevron_right</span>
        <span className="text-slate-900 dark:text-white font-medium">{project.name}</span>
      </div>

      {/* Page Header */}
      <div className="flex flex-wrap justify-between items-start gap-3">
        <div className="flex flex-col gap-2 min-w-72">
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-3xl md:text-4xl font-black text-slate-900 dark:text-white leading-tight tracking-tight">
              {project.name}
            </h1>
            <span className={`px-2 py-1 rounded text-xs font-bold uppercase tracking-wider border ${getStatusColor(project.status)}`}>
              {project.status.replace('_', ' ')}
            </span>
          </div>
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            Project ID: {project.id} • Lead: {project.lead_country || 'Regional'} •{' '}
            <span className="inline-flex items-center gap-1 font-medium text-primary">
              <span className="material-symbols-outlined text-[16px]">smart_toy</span>
              AI Agent
            </span>
          </p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center justify-center px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 text-sm font-bold rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors">
            <span>Edit Project</span>
          </button>
          <button
            onClick={() => navigate(`/deal-pipeline/${encodeURIComponent(project.id)}/memo`)}
            className="flex items-center justify-center gap-2 px-4 py-2 bg-primary text-white text-sm font-bold rounded-lg shadow-md hover:bg-blue-700 transition-colors"
          >
            <span className="material-symbols-outlined text-[18px]">auto_awesome</span>
            <span>Generate Memo</span>
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Funding Ask */}
        <div className="flex flex-col gap-2 rounded-xl p-5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
          <div className="flex justify-between items-start">
            <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">Investment Size</p>
            <span className="material-symbols-outlined text-slate-400">payments</span>
          </div>
          <p className="text-slate-900 dark:text-white text-2xl font-bold">
            {formatCurrency(project.investment_size)} <span className="text-base font-medium text-slate-400">USD</span>
          </p>
          <p className="text-emerald-600 dark:text-emerald-400 text-xs font-bold bg-emerald-50 dark:bg-emerald-900/20 px-2 py-1 rounded w-fit">
            Estimated
          </p>
        </div>

        {/* Readiness Score */}
        <div className="flex flex-col gap-2 rounded-xl p-5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
            <span className="material-symbols-outlined text-6xl text-primary">speed</span>
          </div>
          <div className="flex justify-between items-start z-10">
            <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">Readiness Score</p>
            <span className="material-symbols-outlined text-primary">check_circle</span>
          </div>
          <p className="text-slate-900 dark:text-white text-2xl font-bold">
            {project.readiness_score}
            <span className="text-slate-400 text-lg">/100</span>
          </p>
          <div className="w-full bg-slate-100 dark:bg-slate-700 rounded-full h-1.5 mt-2">
            <div
              className={`${getProgressColor(project.readiness_score)} h-1.5 rounded-full`}
              style={{ width: `${project.readiness_score}%` }}
            ></div>
          </div>
        </div>

        {/* AfCEN Score (New) */}
        <div className="flex flex-col gap-2 rounded-xl p-5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
          <div className="flex justify-between items-start">
            <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">AfCEN Score</p>
            <span className="material-symbols-outlined text-purple-400">stars</span>
          </div>
          <p className="text-slate-900 dark:text-white text-2xl font-bold">{project.afcen_score ? project.afcen_score.toFixed(1) : 'N/A'}</p>
          <p className="text-slate-400 text-xs">Composite Rating</p>
        </div>

        {/* Pillar */}
        <div className="flex flex-col gap-2 rounded-xl p-5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
          <div className="flex justify-between items-start">
            <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">Pillar</p>
            <span className="material-symbols-outlined text-slate-400">category</span>
          </div>
          <p className="text-slate-900 dark:text-white text-xl font-bold truncate" title={project.pillar}>
            {project.pillar || 'General'}
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="sticky top-[72px] bg-background-light dark:bg-background-dark z-40 pt-2 pb-0 mb-6">
        <div className="flex border-b border-slate-200 dark:border-slate-700 gap-8 overflow-x-auto">
          {['overview', 'matches', 'financials', 'documents', 'history'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`flex items-center justify-center border-b-[3px] pb-3 pt-2 min-w-fit transition-colors capitalize ${activeTab === tab
                ? 'border-primary text-slate-900 dark:text-white'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
                }`}
            >
              <span className="text-sm font-bold">
                {tab === 'matches' ? 'Deal Room / Investors' : tab}
              </span>
              {tab === 'matches' && matches.length > 0 && (
                <span className="ml-2 bg-primary text-white text-[10px] px-1.5 py-0.5 rounded-full">
                  {matches.length}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pb-12">
        {/* Left Column (Primary Content) */}
        <div className="lg:col-span-2 flex flex-col gap-6">

          {/* Overview Tab Content */}
          {activeTab === 'overview' && (
            <>
              {/* Executive Summary */}
              <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">Description</h3>
                <div className="prose prose-slate dark:prose-invert max-w-none text-slate-600 dark:text-slate-300">
                  <p className="mb-4">{project.description || 'No description provided.'}</p>
                </div>
              </div>

              {/* Mock Data for Strategic Rationale (Placeholder) */}
              <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
                  Scores Breakdown
                </h3>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div className="p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                    <div className="text-2xl font-bold text-primary">{project.strategic_alignment_score ?? 'N/A'}</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">Strategic Alignment</div>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-700/50 p-3 rounded-lg text-center">
                    <div className="text-2xl font-bold text-primary">N/A</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">Regional Impact</div>
                  </div>
                  <div className="p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                    <div className="text-2xl font-bold text-primary">{project.readiness_score}</div>
                    <div className="text-xs text-slate-500">Readiness</div>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* Matches Tab (NEW) */}
          {activeTab === 'matches' && (
            <div className="space-y-6">
              <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white">Investor Matching</h3>
                  <button
                    onClick={handleTriggerMatching}
                    disabled={triggeringMatch}
                    className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm font-bold shadow-md hover:bg-primary-hover disabled:opacity-50">
                    <span className="material-symbols-outlined">restart_alt</span>
                    {triggeringMatch ? 'Running Engine...' : 'Run Matching Engine'}
                  </button>
                </div>

                {loadingMatches ? (
                  <div className="text-center py-8 text-slate-500">Loading matches...</div>
                ) : matches.length === 0 ? (
                  <div className="text-center py-8 text-slate-500 bg-slate-50 rounded-lg border border-dashed border-slate-300">
                    <span className="material-symbols-outlined text-4xl mb-2">person_search</span>
                    <p>No investors matched yet. Run the matching engine to find potential investors.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {matches.map((match) => (
                      <div key={match.match_id} className="flex flex-col md:flex-row gap-4 p-4 border border-slate-200 dark:border-slate-700 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="text-base font-bold text-slate-900 dark:text-white">{match.investor?.name || 'Unknown Investor'}</h4>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${match.status === InvestorMatchStatus.INTERESTED ? 'bg-green-100 text-green-700' :
                              match.status === InvestorMatchStatus.CONTACTED ? 'bg-blue-100 text-blue-700' :
                                'bg-slate-100 text-slate-600'
                              }`}>
                              {match.status}
                            </span>
                          </div>
                          <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-2">
                            {/* Use sector preferences or investment instruments */}
                            {match.investor?.sector_preferences?.join(', ') || 'No specific strategy'}
                          </p>
                          <div className="text-xs text-slate-500 dark:text-slate-400">
                            <span className="font-medium">Ticket:</span> {match.investor?.ticket_size_min ? `$${match.investor.ticket_size_min}M - $${match.investor.ticket_size_max}M` : 'N/A'}
                          </div>
                          <div className="text-xs text-slate-500 dark:text-slate-400">
                            <span className="font-medium">Focus:</span> {match.investor?.geographic_focus?.join(', ') || 'N/A'}
                          </div>
                        </div>

                        <div className="flex flex-row md:flex-col items-center md:items-end justify-between gap-4 min-w-[140px]">
                          <div className="text-right">
                            <div className="text-2xl font-bold text-primary">{Math.round(match.score)}%</div>
                            <div className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">Match Score</div>
                          </div>

                          <div className="relative group">
                            <select
                              value={match.status}
                              onChange={(e) => handleUpdateMatchStatus(match.match_id, e.target.value as InvestorMatchStatus)}
                              className="appearance-none bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-200 text-xs font-bold py-2 pl-3 pr-8 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 cursor-pointer hover:bg-slate-50"
                            >
                              <option value={InvestorMatchStatus.DETECTED}>Detected</option>
                              <option value={InvestorMatchStatus.CONTACTED}>Contacted</option>
                              <option value={InvestorMatchStatus.INTERESTED}>Interested</option>
                              <option value={InvestorMatchStatus.COMMITTED}>Committed</option>
                              <option value={InvestorMatchStatus.DECLINED}>Declined</option>
                            </select>
                            <span className="material-symbols-outlined absolute right-2 top-1.5 text-[18px] pointer-events-none text-slate-500">expand_more</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Placeholders for other tabs (Simple message to preserve layout) */}
          {(activeTab === 'financials' || activeTab === 'documents' || activeTab === 'history') && (
            <div className="bg-slate-50 border border-dashed border-slate-300 rounded-xl p-12 text-center text-slate-500">
              <span className="material-symbols-outlined text-4xl mb-4">engineering</span>
              <p>This module is currently being connected to the new pipeline backend.</p>
            </div>
          )}

        </div>

        {/* Right Column (Sidebar) */}
        <div className="flex flex-col gap-6">
          {/* AI Insight Card */}
          <div className="rounded-xl p-5 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/40 dark:to-indigo-950/20 border border-blue-100 dark:border-blue-900 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 p-3 opacity-10">
              <span className="material-symbols-outlined text-6xl text-primary">psychology</span>
            </div>
            <div className="flex items-center gap-2 mb-3">
              <span className="material-symbols-outlined text-primary">auto_awesome</span>
              <h4 className="text-sm font-bold text-primary">AI Agent Insight</h4>
            </div>
            {isLoadingInsight ? (
              <div className="flex flex-col items-center justify-center py-4">
                <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mb-2"></div>
                <p className="text-xs text-slate-500 dark:text-slate-400">Analyzing project...</p>
              </div>
            ) : (
              <>
                <p className="text-sm text-slate-700 dark:text-slate-300 mb-3 font-medium">
                  {aiInsight || 'No insights available yet.'}
                </p>
                <div className="bg-white/60 dark:bg-black/20 rounded-lg p-3 text-xs text-slate-600 dark:text-slate-400 backdrop-blur-sm border border-white/50 dark:border-white/10">
                  <strong>Recommendation:</strong> {aiRecommendation || 'Review matches.'}
                </div>
              </>
            )}
            <button
              onClick={fetchAIInsights}
              disabled={isLoadingInsight}
              className="mt-3 w-full py-2 bg-primary/10 hover:bg-primary/20 text-primary text-xs font-bold rounded flex items-center justify-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span className="material-symbols-outlined text-[16px]">psychology</span>
              {isLoadingInsight ? 'Analyzing...' : 'Refresh AI Insight'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectDetails;
