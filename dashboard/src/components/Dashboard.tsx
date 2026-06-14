import React, { useState, useEffect } from 'react';
import { Activity, GitPullRequest, AlertCircle, Users, TrendingUp, RefreshCw } from 'lucide-react';
import {
  fetchPullRequests,
  fetchIssues,
  fetchRepositoryStats,
  fetchContributors,
  PullRequest,
  Issue,
  RepositoryStats,
  Contributor
} from '../services/githubAPI';
import StatCard from './StatCard';
import PRTable from './PRTable';
import IssueTable from './IssueTable';
import ContributorChart from './ContributorChart';
import PRMetrics from './PRMetrics';

interface DashboardState {
  pullRequests: PullRequest[];
  issues: Issue[];
  stats: RepositoryStats | null;
  contributors: Contributor[];
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

const Dashboard: React.FC = () => {
  const [state, setState] = useState<DashboardState>({
    pullRequests: [],
    issues: [],
    stats: null,
    contributors: [],
    loading: true,
    error: null,
    lastUpdated: null
  });

  const [activeTab, setActiveTab] = useState<'overview' | 'prs' | 'issues' | 'contributors'>('overview');
  const [prFilter, setPrFilter] = useState<'all' | 'open' | 'closed'>('all');
  const [issueFilter, setIssueFilter] = useState<'all' | 'open' | 'closed'>('open');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      const [prs, issues, stats, contributors] = await Promise.all([
        fetchPullRequests(),
        fetchIssues(),
        fetchRepositoryStats(),
        fetchContributors()
      ]);

      setState({
        pullRequests: prs,
        issues: issues,
        stats: {
          ...stats,
          open_pull_requests: prs.filter(pr => pr.state === 'open').length
        },
        contributors: contributors,
        loading: false,
        error: null,
        lastUpdated: new Date()
      });
    } catch (err) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: 'Failed to load dashboard data. Please check your GitHub token.'
      }));
    }
  };

  const openPRs = state.pullRequests.filter(pr => pr.state === 'open');
  const mergedPRs = state.pullRequests.filter(pr => pr.state === 'closed' && pr.merged_at);
  const openIssues = state.issues.filter(issue => issue.state === 'open');

  const filteredPRs = prFilter === 'all' 
    ? state.pullRequests 
    : state.pullRequests.filter(pr => pr.state === prFilter);

  const filteredIssues = issueFilter === 'all' 
    ? state.issues 
    : state.issues.filter(issue => issue.state === issueFilter);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-800/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <GitPullRequest className="w-8 h-8 text-blue-400" />
              <h1 className="text-3xl font-bold text-white">DAU-PWA Dashboard</h1>
            </div>
            <button
              onClick={loadDashboardData}
              disabled={state.loading}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${state.loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
          {state.lastUpdated && (
            <p className="text-sm text-slate-400 mt-2">
              Last updated: {state.lastUpdated.toLocaleTimeString()}
            </p>
          )}
        </div>
      </header>

      {/* Error Alert */}
      {state.error && (
        <div className="bg-red-500/20 border border-red-500/50 text-red-200 px-6 py-4 flex items-gap gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{state.error}</span>
        </div>
      )}

      {/* Navigation Tabs */}
      <nav className="border-b border-slate-700 bg-slate-800/30">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-8">
            {(['overview', 'prs', 'issues', 'contributors'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-4 font-medium border-b-2 transition capitalize ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-slate-400 hover:text-slate-300'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {state.loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <RefreshCw className="w-8 h-8 text-blue-400 animate-spin mx-auto mb-4" />
              <p className="text-slate-400">Loading dashboard data...</p>
            </div>
          </div>
        ) : (
          <>
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="space-y-8">
                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <StatCard
                    icon={GitPullRequest}
                    label="Open Pull Requests"
                    value={openPRs.length}
                    color="blue"
                  />
                  <StatCard
                    icon={TrendingUp}
                    label="Merged PRs"
                    value={mergedPRs.length}
                    color="green"
                  />
                  <StatCard
                    icon={AlertCircle}
                    label="Open Issues"
                    value={openIssues.length}
                    color="yellow"
                  />
                  <StatCard
                    icon={Users}
                    label="Contributors"
                    value={state.contributors.length}
                    color="purple"
                  />
                </div>

                {/* Charts */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <PRMetrics pullRequests={state.pullRequests} />
                  <ContributorChart contributors={state.contributors.slice(0, 10)} />
                </div>
              </div>
            )}

            {/* Pull Requests Tab */}
            {activeTab === 'prs' && (
              <div className="space-y-4">
                <div className="flex gap-2">
                  {(['all', 'open', 'closed'] as const).map(filter => (
                    <button
                      key={filter}
                      onClick={() => setPrFilter(filter)}
                      className={`px-4 py-2 rounded-lg font-medium transition capitalize ${
                        prFilter === filter
                          ? 'bg-blue-600 text-white'
                          : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      }`}
                    >
                      {filter}
                    </button>
                  ))}
                </div>
                <PRTable pullRequests={filteredPRs} />
              </div>
            )}

            {/* Issues Tab */}
            {activeTab === 'issues' && (
              <div className="space-y-4">
                <div className="flex gap-2">
                  {(['all', 'open', 'closed'] as const).map(filter => (
                    <button
                      key={filter}
                      onClick={() => setIssueFilter(filter)}
                      className={`px-4 py-2 rounded-lg font-medium transition capitalize ${
                        issueFilter === filter
                          ? 'bg-blue-600 text-white'
                          : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      }`}
                    >
                      {filter}
                    </button>
                  ))}
                </div>
                <IssueTable issues={filteredIssues} />
              </div>
            )}

            {/* Contributors Tab */}
            {activeTab === 'contributors' && (
              <ContributorsList contributors={state.contributors} />
            )}
          </>
        )}
      </main>
    </div>
  );
};

const ContributorsList: React.FC<{ contributors: Contributor[] }> = ({ contributors }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {contributors.map(contributor => (
      <div
        key={contributor.login}
        className="bg-slate-700/50 rounded-lg p-4 hover:bg-slate-700 transition border border-slate-600"
      >
        <div className="flex items-center gap-4">
          <img
            src={contributor.avatar_url}
            alt={contributor.login}
            className="w-12 h-12 rounded-full"
          />
          <div className="flex-1">
            <p className="font-medium text-white">{contributor.login}</p>
            <p className="text-sm text-slate-400">{contributor.contributions} contributions</p>
          </div>
        </div>
      </div>
    ))}
  </div>
);

export default Dashboard;
