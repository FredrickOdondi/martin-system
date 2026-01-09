import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';


interface ProjectData {
  id: string;
  name: string;
  projectId: string;
  status: string;
  fundingAsk: string;
  readinessScore: number;
  currentPhase: string;
  nextPhase: string;
  twgName: string;
  lastUpdated: string;
  pillar: string;
  leadCountry: string;
  leadCompany: string;
  executiveSummary: string;
  description: string;
  icon: string;
  iconColor: string;
}

const ProjectDetails: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'overview' | 'financials' | 'documents' | 'history'>('overview');
  const [aiInsight, setAiInsight] = useState<string>('');
  const [aiRecommendation, setAiRecommendation] = useState<string>('');
  const [isLoadingInsight, setIsLoadingInsight] = useState(false);

  // Project data mapping - in real app, fetch from API based on projectId
  const projectsData: Record<string, ProjectData> = {
    '#ECW-2024-001': {
      id: '#ECW-2024-001',
      name: 'West African Rail Link',
      projectId: '#8492',
      status: 'In Review',
      fundingAsk: '$1.2B',
      readinessScore: 82,
      currentPhase: 'Feasibility',
      nextPhase: 'Technical Design',
      twgName: 'Infrastructure & Transport',
      lastUpdated: '2 hours ago',
      pillar: 'Infrastructure',
      leadCountry: 'Nigeria',
      leadCompany: 'RailCo Ltd.',
      executiveSummary: 'The West African Rail Link project aims to rehabilitate and extend the rail corridor connecting Lagos (Nigeria) to Cotonou (Benin), facilitating the movement of goods and passengers across the key economic hubs of the ECOWAS region. This project is a critical component of the broader West African Railway Master Plan.',
      description: 'Currently in the Feasibility Study phase, the project has secured preliminary backing from the African Development Bank and local stakeholders. The technical survey indicates no major geographical impediments, though urban displacement in Lagos suburbs remains a key risk factor requiring mitigation.',
      icon: 'train',
      iconColor: 'blue',
    },
    '#ECW-2024-042': {
      id: '#ECW-2024-042',
      name: 'Solar Grid Expansion',
      projectId: '#7821',
      status: 'Approved',
      fundingAsk: '$450M',
      readinessScore: 95,
      currentPhase: 'Implementation',
      nextPhase: 'Operations',
      twgName: 'Energy & Power',
      lastUpdated: '5 hours ago',
      pillar: 'Energy',
      leadCountry: 'Ghana',
      leadCompany: 'Volta Energy',
      executiveSummary: 'The Solar Grid Expansion project aims to deploy 500MW of solar capacity across Ghana and neighboring countries, providing clean and reliable electricity to over 2 million households. This initiative supports the ECOWAS Renewable Energy Policy and contributes to regional climate goals.',
      description: 'With approvals secured and financing in place, the project is moving into the implementation phase. Site preparation has begun in three locations, with the first installations expected to be operational within 18 months.',
      icon: 'solar_power',
      iconColor: 'orange',
    },
    '#ECW-2024-088': {
      id: '#ECW-2024-088',
      name: 'Agribusiness Hub',
      projectId: '#6543',
      status: 'Draft',
      fundingAsk: '$85M',
      readinessScore: 45,
      currentPhase: 'Concept',
      nextPhase: 'Feasibility',
      twgName: 'Agriculture & Food Security',
      lastUpdated: '1 day ago',
      pillar: 'Agriculture',
      leadCountry: "Côte d'Ivoire",
      leadCompany: 'AgriCorp Int.',
      executiveSummary: 'The Agribusiness Hub project proposes establishing a modern agricultural processing and logistics center in Abidjan, connecting smallholder farmers to regional and international markets. The hub will feature cold storage, processing facilities, and training centers.',
      description: 'The project is in early concept phase, with stakeholder consultations ongoing. Additional feasibility studies are required to assess market demand, infrastructure requirements, and financial viability before proceeding to the next phase.',
      icon: 'agriculture',
      iconColor: 'green',
    },
    '#ECW-2024-102': {
      id: '#ECW-2024-102',
      name: 'Tech City Phase 1',
      projectId: '#9201',
      status: 'In Review',
      fundingAsk: '$2.1B',
      readinessScore: 78,
      currentPhase: 'Planning',
      nextPhase: 'Development',
      twgName: 'Digital Innovation & Technology',
      lastUpdated: '3 hours ago',
      pillar: 'Technology',
      leadCountry: 'Senegal',
      leadCompany: 'Dakar Innovations',
      executiveSummary: 'Tech City Phase 1 envisions creating a world-class technology and innovation hub in Dakar, featuring startup incubators, research facilities, co-working spaces, and smart infrastructure. The project aims to position West Africa as a global tech destination.',
      description: 'Master planning is complete, and the project team is finalizing agreements with anchor tenants and technology partners. Environmental and social impact assessments are underway, with initial construction targeted for Q3 2025.',
      icon: 'computer',
      iconColor: 'indigo',
    },
  };

  const projectData = projectsData[decodeURIComponent(projectId || '')] || projectsData['#ECW-2024-001'];

  // Fetch AI insights from supervisor agent
  const fetchAIInsights = async () => {
    setIsLoadingInsight(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/agents/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          message: `Analyze this investment project and provide key insights and recommendations:

Project: ${projectData.name}
Sector: ${projectData.pillar}
Funding Required: ${projectData.fundingAsk}
Lead Country: ${projectData.leadCountry}
Readiness Score: ${projectData.readinessScore}/100
Current Phase: ${projectData.currentPhase}
Status: ${projectData.status}

Executive Summary: ${projectData.executiveSummary}

Description: ${projectData.description}

Provide:
1. A brief insight (1-2 sentences) highlighting key observations or concerns
2. A specific, actionable recommendation for decision-makers

Format your response as:
INSIGHT: [your insight here]
RECOMMENDATION: [your recommendation here]`,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const content = data.response || '';

        // Parse the response
        const insightMatch = content.match(/INSIGHT:\s*(.+?)(?=RECOMMENDATION:|$)/s);
        const recommendationMatch = content.match(/RECOMMENDATION:\s*(.+)/s);

        if (insightMatch) {
          setAiInsight(insightMatch[1].trim());
        }
        if (recommendationMatch) {
          setAiRecommendation(recommendationMatch[1].trim());
        }
      }
    } catch (error) {
      console.error('Error fetching AI insights:', error);
      // Set fallback insights
      setAiInsight(`Readiness Score is ${projectData.readinessScore >= 80 ? 'high' : projectData.readinessScore >= 60 ? 'moderate' : 'low'} (${projectData.readinessScore}/100). Further analysis recommended.`);
      setAiRecommendation('Request updated documentation from the TWG lead before proceeding.');
    } finally {
      setIsLoadingInsight(false);
    }
  };

  // Load AI insights on component mount
  useEffect(() => {
    fetchAIInsights();
  }, [projectId]);

  const getStatusColor = (_status: string) => {
    return 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200 border-amber-200 dark:border-amber-800';
  };

  const getProgressColor = (score: number) => {
    if (score >= 80) return 'bg-primary';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-orange-500';
  };

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
        <span className="text-slate-900 dark:text-white font-medium">{projectData.name}</span>
      </div>

      {/* Page Header */}
      <div className="flex flex-wrap justify-between items-start gap-3">
        <div className="flex flex-col gap-2 min-w-72">
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-3xl md:text-4xl font-black text-slate-900 dark:text-white leading-tight tracking-tight">
              {projectData.name}
            </h1>
            <span className={`px-2 py-1 rounded text-xs font-bold uppercase tracking-wider border ${getStatusColor(projectData.status)}`}>
              {projectData.status}
            </span>
          </div>
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            Project ID: {projectData.projectId} • Last updated {projectData.lastUpdated} by{' '}
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
            onClick={() => navigate(`/deal-pipeline/${encodeURIComponent(projectData.id)}/memo`)}
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
            <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">Funding Ask</p>
            <span className="material-symbols-outlined text-slate-400">payments</span>
          </div>
          <p className="text-slate-900 dark:text-white text-2xl font-bold">
            {projectData.fundingAsk} <span className="text-base font-medium text-slate-400">USD</span>
          </p>
          <p className="text-emerald-600 dark:text-emerald-400 text-xs font-bold bg-emerald-50 dark:bg-emerald-900/20 px-2 py-1 rounded w-fit">
            +5% vs last month
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
            {projectData.readinessScore}
            <span className="text-slate-400 text-lg">/100</span>
          </p>
          <div className="w-full bg-slate-100 dark:bg-slate-700 rounded-full h-1.5 mt-2">
            <div
              className={`${getProgressColor(projectData.readinessScore)} h-1.5 rounded-full`}
              style={{ width: `${projectData.readinessScore}%` }}
            ></div>
          </div>
        </div>

        {/* Current Phase */}
        <div className="flex flex-col gap-2 rounded-xl p-5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
          <div className="flex justify-between items-start">
            <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">Current Phase</p>
            <span className="material-symbols-outlined text-slate-400">timeline</span>
          </div>
          <p className="text-slate-900 dark:text-white text-2xl font-bold">{projectData.currentPhase}</p>
          <p className="text-slate-400 text-sm">Next: {projectData.nextPhase}</p>
        </div>

        {/* Originating TWG */}
        <div className="flex flex-col gap-2 rounded-xl p-5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
          <div className="flex justify-between items-start">
            <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">Originating TWG</p>
            <span className="material-symbols-outlined text-slate-400">groups</span>
          </div>
          <p className="text-slate-900 dark:text-white text-xl font-bold truncate" title={projectData.twgName}>
            {projectData.twgName}
          </p>
          <div className="flex -space-x-2 mt-1">
            <div className="w-6 h-6 rounded-full bg-slate-300 dark:bg-slate-600 border-2 border-white dark:border-slate-800"></div>
            <div className="w-6 h-6 rounded-full bg-slate-300 dark:bg-slate-600 border-2 border-white dark:border-slate-800"></div>
            <div className="w-6 h-6 rounded-full bg-slate-200 dark:bg-slate-700 border-2 border-white dark:border-slate-800 flex items-center justify-center text-[10px] font-bold text-slate-600 dark:text-slate-300">
              +4
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="sticky top-[72px] bg-background-light dark:bg-background-dark z-40 pt-2 pb-0 mb-6">
        <div className="flex border-b border-slate-200 dark:border-slate-700 gap-8 overflow-x-auto">
          <button
            onClick={() => setActiveTab('overview')}
            className={`flex items-center justify-center border-b-[3px] pb-3 pt-2 min-w-fit transition-colors ${activeTab === 'overview'
                ? 'border-primary text-slate-900 dark:text-white'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
              }`}
          >
            <span className="text-sm font-bold">Overview</span>
          </button>
          <button
            onClick={() => setActiveTab('financials')}
            className={`flex items-center justify-center border-b-[3px] pb-3 pt-2 min-w-fit transition-colors ${activeTab === 'financials'
                ? 'border-primary text-slate-900 dark:text-white'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
              }`}
          >
            <span className="text-sm font-bold">Financials</span>
          </button>
          <button
            onClick={() => setActiveTab('documents')}
            className={`flex items-center justify-center border-b-[3px] pb-3 pt-2 min-w-fit transition-colors ${activeTab === 'documents'
                ? 'border-primary text-slate-900 dark:text-white'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
              }`}
          >
            <span className="text-sm font-bold flex gap-2 items-center">
              Documents
              <span className="bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-[10px] px-1.5 py-0.5 rounded-full">
                4
              </span>
            </span>
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center justify-center border-b-[3px] pb-3 pt-2 min-w-fit transition-colors ${activeTab === 'history'
                ? 'border-primary text-slate-900 dark:text-white'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
              }`}
          >
            <span className="text-sm font-bold">History</span>
          </button>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pb-12">
        {/* Left Column (Primary Content) */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          {/* Executive Summary */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">Executive Summary</h3>
            <div className="prose prose-slate dark:prose-invert max-w-none text-slate-600 dark:text-slate-300">
              <p className="mb-4">{projectData.executiveSummary}</p>
              <p>{projectData.description}</p>
            </div>
          </div>

          {/* Strategic Rationale */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
              Strategic Rationale & Business Case
            </h3>
            <ul className="space-y-4">
              <li className="flex gap-4 items-start">
                <div className="size-8 rounded-full bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center flex-shrink-0 text-primary">
                  <span className="material-symbols-outlined text-sm">hub</span>
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white">Regional Connectivity</h4>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                    Directly supports ECOWAS Vision 2050 Goal 3: "Integrated Infrastructure". Expected to reduce
                    transit times by 40%.
                  </p>
                </div>
              </li>
              <li className="flex gap-4 items-start">
                <div className="size-8 rounded-full bg-green-50 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0 text-green-600 dark:text-green-400">
                  <span className="material-symbols-outlined text-sm">eco</span>
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white">Economic & Environmental Impact</h4>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                    Projected IRR of 14% over 25 years. Shifts 20% of road freight to rail, reducing regional carbon
                    emissions by 150k tons annually.
                  </p>
                </div>
              </li>
              <li className="flex gap-4 items-start">
                <div className="size-8 rounded-full bg-purple-50 dark:bg-purple-900/30 flex items-center justify-center flex-shrink-0 text-purple-600 dark:text-purple-400">
                  <span className="material-symbols-outlined text-sm">handshake</span>
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white">Trade Facilitation</h4>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                    Will streamline customs procedures at the border through integrated rail terminals, boosting
                    intra-regional trade volume.
                  </p>
                </div>
              </li>
            </ul>
          </div>

          {/* Map Visual Placeholder */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden shadow-sm h-64 relative group">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-100 to-indigo-200 dark:from-blue-900/50 dark:to-indigo-900/50"></div>
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="material-symbols-outlined text-6xl text-white/50">map</span>
            </div>
            <div className="absolute bottom-4 left-4 text-white">
              <p className="font-bold text-lg">Proposed Route</p>
              <p className="text-sm opacity-80">
                Lagos Terminus A
                <span className="material-symbols-outlined text-xs align-middle mx-1">arrow_forward</span>
                Cotonou Port
              </p>
            </div>
            <button className="absolute top-4 right-4 bg-white/90 dark:bg-black/50 backdrop-blur text-slate-900 dark:text-white p-2 rounded-lg hover:bg-white transition-colors">
              <span className="material-symbols-outlined">fullscreen</span>
            </button>
          </div>
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
                  {aiInsight || `Readiness Score is ${projectData.readinessScore >= 80 ? 'high' : projectData.readinessScore >= 60 ? 'moderate' : 'low'} (${projectData.readinessScore}/100).`}
                </p>
                <div className="bg-white/60 dark:bg-black/20 rounded-lg p-3 text-xs text-slate-600 dark:text-slate-400 backdrop-blur-sm border border-white/50 dark:border-white/10">
                  <strong>Recommendation:</strong> {aiRecommendation || 'Request updated documentation from the TWG lead.'}
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

          {/* Action Items */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5 shadow-sm">
            <h4 className="text-xs font-bold text-slate-500 dark:text-slate-400 mb-4 uppercase tracking-wider">
              Action Required
            </h4>
            <div className="space-y-3">
              <div className="flex gap-3 items-start p-3 bg-amber-50 dark:bg-amber-900/10 border border-amber-100 dark:border-amber-800/30 rounded-lg">
                <span className="material-symbols-outlined text-amber-600 text-lg mt-0.5">warning</span>
                <div>
                  <p className="text-sm font-bold text-slate-900 dark:text-white">Missing Document</p>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">Updated EIA Report pending upload.</p>
                </div>
              </div>
              <div className="flex gap-3 items-start p-3 bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-700 rounded-lg">
                <span className="material-symbols-outlined text-slate-400 text-lg mt-0.5">pending_actions</span>
                <div>
                  <p className="text-sm font-bold text-slate-900 dark:text-white">Sign-off Needed</p>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
                    Finance Ministry approval for Phase 2 funding.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Documents */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5 shadow-sm">
            <div className="flex justify-between items-center mb-4">
              <h4 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                Recent Attachments
              </h4>
              <button className="text-primary text-xs font-bold hover:underline">View All</button>
            </div>
            <ul className="space-y-3">
              <li className="flex items-center gap-3 group cursor-pointer">
                <div className="size-8 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded flex items-center justify-center">
                  <span className="material-symbols-outlined text-sm">picture_as_pdf</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-900 dark:text-white truncate group-hover:text-primary transition-colors">
                    Feasibility_Study_v2.pdf
                  </p>
                  <p className="text-xs text-slate-500">2.4 MB • 2 days ago</p>
                </div>
                <span className="material-symbols-outlined text-slate-400 text-sm opacity-0 group-hover:opacity-100 transition-opacity">
                  download
                </span>
              </li>
              <li className="flex items-center gap-3 group cursor-pointer">
                <div className="size-8 bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 rounded flex items-center justify-center">
                  <span className="material-symbols-outlined text-sm">table_view</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-900 dark:text-white truncate group-hover:text-primary transition-colors">
                    Financial_Model_2024.xlsx
                  </p>
                  <p className="text-xs text-slate-500">1.1 MB • 1 week ago</p>
                </div>
                <span className="material-symbols-outlined text-slate-400 text-sm opacity-0 group-hover:opacity-100 transition-opacity">
                  download
                </span>
              </li>
            </ul>
            <button className="w-full mt-4 border border-dashed border-slate-300 dark:border-slate-600 rounded-lg p-2 text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 hover:border-slate-400 dark:hover:border-slate-500 transition-colors flex items-center justify-center gap-2">
              <span className="material-symbols-outlined text-sm">upload_file</span>
              Upload Document
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectDetails;
