import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';


interface Project {
  id: string;
  name: string;
  pillar: string;
  leadCountry: string;
  leadCompany: string;
  investment: string;
  readinessScore: number;
  status: 'In Review' | 'Approved' | 'Draft';
  aiScored: boolean;
  icon: string;
  iconColor: string;
}

const DealPipeline: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [showAIInsight, setShowAIInsight] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  // const [showFilterModal, setShowFilterModal] = useState(false);

  const projects: Project[] = [
    {
      id: '#ECW-2024-001',
      name: 'West African Rail Link',
      pillar: 'Infrastructure',
      leadCountry: 'Nigeria',
      leadCompany: 'RailCo Ltd.',
      investment: '$1.2B',
      readinessScore: 82,
      status: 'In Review',
      aiScored: true,
      icon: 'train',
      iconColor: 'blue',
    },
    {
      id: '#ECW-2024-042',
      name: 'Solar Grid Expansion',
      pillar: 'Energy',
      leadCountry: 'Ghana',
      leadCompany: 'Volta Energy',
      investment: '$450M',
      readinessScore: 95,
      status: 'Approved',
      aiScored: false,
      icon: 'solar_power',
      iconColor: 'orange',
    },
    {
      id: '#ECW-2024-088',
      name: 'Agribusiness Hub',
      pillar: 'Agriculture',
      leadCountry: "Côte d'Ivoire",
      leadCompany: 'AgriCorp Int.',
      investment: '$85M',
      readinessScore: 45,
      status: 'Draft',
      aiScored: false,
      icon: 'agriculture',
      iconColor: 'green',
    },
    {
      id: '#ECW-2024-102',
      name: 'Tech City Phase 1',
      pillar: 'Technology',
      leadCountry: 'Senegal',
      leadCompany: 'Dakar Innovations',
      investment: '$2.1B',
      readinessScore: 78,
      status: 'In Review',
      aiScored: true,
      icon: 'computer',
      iconColor: 'indigo',
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Approved':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300';
      case 'In Review':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300';
      case 'Draft':
        return 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300';
      default:
        return 'bg-slate-100 text-slate-800';
    }
  };

  const getIconColorClasses = (color: string) => {
    const colors: Record<string, string> = {
      blue: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
      orange: 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400',
      green: 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400',
      indigo: 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400',
    };
    return colors[color] || colors.blue;
  };

  const getProgressColor = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-primary';
    return 'bg-yellow-500';
  };

  const filteredProjects = projects.filter(project => {
    if (activeTab !== 'all' && project.pillar.toLowerCase() !== activeTab) return false;
    if (statusFilter !== 'all' && project.status.toLowerCase().replace(' ', '-') !== statusFilter) return false;
    return true;
  });

  const handleExport = () => {
    // Create CSV content
    const headers = ['ID', 'Name', 'Pillar', 'Lead Country', 'Lead Company', 'Investment', 'Readiness Score', 'Status'];
    const csvContent = [
      headers.join(','),
      ...filteredProjects.map(p =>
        [p.id, p.name, p.pillar, p.leadCountry, p.leadCompany, p.investment, p.readinessScore, p.status].join(',')
      )
    ].join('\n');

    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `deal-pipeline-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const handleNewProject = () => {
    navigate('/deal-pipeline/new');
  };

  const handleReviewSuggestions = () => {
    alert('AI Suggestions feature coming soon!');
  };

  const handleFilterClick = () => {
    // setShowFilterModal(true);
    alert('Advanced filters modal coming soon!');
  };

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    setCurrentPage(currentPage + 1);
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Breadcrumbs */}
      <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
        <a href="/dashboard" className="hover:text-primary transition-colors">
          Dashboard
        </a>
        <span className="material-symbols-outlined text-[16px]">chevron_right</span>
        <span className="text-slate-900 dark:text-white font-medium">Deal Pipeline</span>
      </div>

      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Deal Pipeline - Investment Opportunities
          </h2>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Manage and evaluate regional investment opportunities.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-700 dark:text-slate-200 text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors shadow-sm">
            <span className="material-symbols-outlined text-[20px]">download</span>
            Export
          </button>
          <button
            onClick={handleNewProject}
            className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg text-sm font-bold shadow-md shadow-primary/20 transition-all">
            <span className="material-symbols-outlined text-[20px]">add</span>
            New Project
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col gap-1">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
              Total Pipeline Value
            </p>
            <span className="material-symbols-outlined text-green-600 bg-green-100 dark:bg-green-900/30 p-1 rounded">
              trending_up
            </span>
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-white mt-2">$45.2B</p>
          <p className="text-xs text-green-600 font-medium flex items-center gap-1 mt-1">
            <span className="material-symbols-outlined text-[14px]">arrow_upward</span>
            12% vs last month
          </p>
        </div>

        <div className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col gap-1">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
              High Readiness Projects
            </p>
            <span className="material-symbols-outlined text-primary bg-primary/10 dark:bg-primary/20 p-1 rounded">
              verified
            </span>
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-white mt-2">12</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-medium mt-1">
            Ready for immediate investment
          </p>
        </div>

        <div className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col gap-1">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
              Pending AI Review
            </p>
            <span className="material-symbols-outlined text-purple-600 bg-purple-100 dark:bg-purple-900/30 p-1 rounded">
              smart_toy
            </span>
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-white mt-2">5</p>
          <p className="text-xs text-purple-600 font-medium mt-1">Awaiting agent analysis</p>
        </div>
      </div>

      {/* AI Insight Widget */}
      {showAIInsight && (
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 border border-indigo-100 dark:border-indigo-800/50 rounded-xl p-4 flex items-start gap-4 shadow-sm relative overflow-hidden">
          <div className="absolute -right-10 -top-10 h-32 w-32 bg-indigo-200 dark:bg-indigo-800 rounded-full blur-3xl opacity-20"></div>
          <div className="p-2 bg-white dark:bg-slate-800 rounded-lg shadow-sm shrink-0 text-indigo-600 dark:text-indigo-400">
            <span className="material-symbols-outlined">auto_awesome</span>
          </div>
          <div className="flex-1 z-10">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              AI Agent 'Alpha' Insight
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">
              I've identified missing financial data in 3 new project submissions. Updating these
              could increase the overall readiness score by ~15%.
            </p>
          </div>
          <button
            onClick={handleReviewSuggestions}
            className="text-sm font-medium text-indigo-700 dark:text-indigo-300 hover:underline px-2 z-10 whitespace-nowrap self-center">
            Review Suggestions
          </button>
          <button
            onClick={() => setShowAIInsight(false)}
            className="absolute top-2 right-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          >
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>
      )}

      {/* Filters & Toolbar */}
      <div className="flex flex-col sm:flex-row justify-between items-center gap-4 bg-white dark:bg-slate-800 p-4 rounded-lg border border-slate-200 dark:border-slate-700">
        {/* Tabs */}
        <div className="flex p-1 bg-slate-100 dark:bg-slate-700 rounded-lg w-full sm:w-auto overflow-x-auto">
          <button
            onClick={() => setActiveTab('all')}
            className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all whitespace-nowrap ${activeTab === 'all'
              ? 'bg-white dark:bg-slate-600 text-slate-900 dark:text-white shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
          >
            All Projects
          </button>
          <button
            onClick={() => setActiveTab('infrastructure')}
            className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all whitespace-nowrap ${activeTab === 'infrastructure'
              ? 'bg-white dark:bg-slate-600 text-slate-900 dark:text-white shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
          >
            Infrastructure
          </button>
          <button
            onClick={() => setActiveTab('energy')}
            className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all whitespace-nowrap ${activeTab === 'energy'
              ? 'bg-white dark:bg-slate-600 text-slate-900 dark:text-white shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
          >
            Energy
          </button>
          <button
            onClick={() => setActiveTab('agriculture')}
            className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all whitespace-nowrap ${activeTab === 'agriculture'
              ? 'bg-white dark:bg-slate-600 text-slate-900 dark:text-white shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
          >
            Agriculture
          </button>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative w-full sm:w-48">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full appearance-none bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-200 text-sm rounded-lg focus:ring-primary focus:border-primary block px-3 py-2 pr-8"
            >
              <option value="all">Status: All</option>
              <option value="approved">Approved</option>
              <option value="in-review">In Review</option>
              <option value="draft">Draft</option>
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-500">
              <span className="material-symbols-outlined text-[20px]">expand_more</span>
            </div>
          </div>
          <button
            onClick={handleFilterClick}
            className="p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-600">
            <span className="material-symbols-outlined text-[20px]">filter_list</span>
          </button>
        </div>
      </div>

      {/* Data Table */}
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-700">
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Project Name
                </th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Pillar
                </th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Lead Country/Co.
                </th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Investment
                </th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Readiness Score
                </th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider text-right">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
              {filteredProjects.map((project) => (
                <tr
                  key={project.id}
                  onClick={() => navigate(`/deal-pipeline/${encodeURIComponent(project.id)}`)}
                  className="group hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors cursor-pointer"
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-3">
                      <div
                        className={`h-10 w-10 rounded-lg flex items-center justify-center shrink-0 ${getIconColorClasses(
                          project.iconColor
                        )}`}
                      >
                        <span className="material-symbols-outlined">{project.icon}</span>
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-slate-900 dark:text-white">
                          {project.name}
                        </p>
                        <p className="text-xs text-slate-500">ID: {project.id}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-600">
                      {project.pillar}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex flex-col">
                      <span className="text-sm text-slate-900 dark:text-white">
                        {project.leadCountry}
                      </span>
                      <span className="text-xs text-slate-500">{project.leadCompany}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm font-medium text-slate-900 dark:text-white">
                      {project.investment}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap min-w-[180px]">
                    <div className="flex flex-col gap-1">
                      <div className="flex justify-between items-center text-xs">
                        <span className="font-medium text-slate-700 dark:text-slate-200">
                          {project.readinessScore}%
                        </span>
                        {project.aiScored && (
                          <div
                            className="flex items-center gap-1 text-purple-600 dark:text-purple-400"
                            title="AI Calculated Score"
                          >
                            <span className="material-symbols-outlined text-[14px]">
                              auto_awesome
                            </span>
                            <span className="text-[10px] font-bold">AI SCORED</span>
                          </div>
                        )}
                      </div>
                      <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                        <div
                          className={`${getProgressColor(project.readinessScore)} h-2 rounded-full`}
                          style={{ width: `${project.readinessScore}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                        project.status
                      )}`}
                    >
                      {project.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/deal-pipeline/${encodeURIComponent(project.id)}`);
                      }}
                      className="text-slate-400 hover:text-primary transition-colors p-1"
                    >
                      <span className="material-symbols-outlined text-[20px]">visibility</span>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        alert('More options menu coming soon!');
                      }}
                      className="text-slate-400 hover:text-primary transition-colors p-1 ml-2"
                    >
                      <span className="material-symbols-outlined text-[20px]">more_vert</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
          <div className="text-sm text-slate-500 dark:text-slate-400">
            Showing <span className="font-medium text-slate-900 dark:text-white">1</span> to{' '}
            <span className="font-medium text-slate-900 dark:text-white">
              {filteredProjects.length}
            </span>{' '}
            of <span className="font-medium text-slate-900 dark:text-white">24</span> results
          </div>
          <div className="flex gap-2">
            <button
              onClick={handlePreviousPage}
              disabled={currentPage === 1}
              className="px-3 py-1 text-sm border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-600 dark:text-slate-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-50 dark:hover:bg-slate-600">
              Previous
            </button>
            <button
              onClick={handleNextPage}
              className="px-3 py-1 text-sm border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-600">
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Bottom spacing */}
      <div className="h-10"></div>
    </div>
  );
};

export default DealPipeline;
