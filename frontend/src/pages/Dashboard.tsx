import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Users, Award, CheckSquare, Target, BarChart3, Compass, Settings, 
  Search, Plus, ArrowUpRight, TrendingUp, Link as LinkIcon
} from 'lucide-react';
import { 
  ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, XAxis, 
  Tooltip
} from 'recharts';
import { useSession } from '../App';

export default function Dashboard() {
  const navigate = useNavigate();
  const { setInterviewId } = useSession();
  
  // Tab states for inside the dashboard
  const [activeTab, setActiveTab] = useState('Overview');
  const [timeRange, setTimeRange] = useState('This Month');
  const [searchQuery, setSearchQuery] = useState('');

  // Dynamic lists from backend
  const [jdsList, setJdsList] = useState<any[]>([]);
  const [candidatesList, setCandidatesList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const [jdsRes, reportsRes] = await Promise.all([
          axios.get('/api/jd'),
          axios.get('/api/interview/reports')
        ]);
        setJdsList(jdsRes.data || []);
        setCandidatesList(reportsRes.data || []);
      } catch (err) {
        console.error('Failed to load recruiter dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, []);

  // Compute metric cards from database data
  const totalAssessments = candidatesList.length;
  const completedInterviews = candidatesList.filter(c => c.status === 'Completed').length;
  const strongHires = candidatesList.filter(c => c.recommendation === 'Strong Hire').length;
  
  const averageScore = totalAssessments > 0
    ? Math.round(candidatesList.reduce((acc, curr) => acc + (curr.score || 0), 0) / totalAssessments * 10) / 10
    : 0;

  const metricCards = [
    { label: 'Total Assessments', value: String(totalAssessments), rate: '+12%', labelColor: 'var(--color-accent-indigo)' },
    { label: 'Completed Interviews', value: String(completedInterviews), rate: '+15%', labelColor: 'var(--color-accent-teal)' },
    { label: 'Strong Hire', value: String(strongHires), rate: '+8%', labelColor: 'var(--color-accent-teal)' },
    { label: 'Average Score', value: String(averageScore), rate: '+4.2%', labelColor: 'var(--color-accent-indigo)' }
  ];

  // Sort top candidates by score descending
  const topCandidates = [...candidatesList]
    .sort((a, b) => b.score - a.score)
    .slice(0, 5)
    .map(c => ({
      interview_id: c.interview_id,
      name: c.candidate_name,
      role: c.job_title,
      score: c.score,
      tag: c.recommendation || (c.score >= 85 ? 'Strong Hire' : c.score >= 70 ? 'Consider' : 'Needs Prep'),
      color: c.score >= 85 ? 'var(--color-accent-teal)' : c.score >= 70 ? 'rgb(251, 191, 36)' : 'var(--color-accent-coral)',
      bg: c.score >= 85 ? 'rgba(45, 212, 191, 0.08)' : c.score >= 70 ? 'rgba(251, 191, 36, 0.08)' : 'rgba(251, 113, 133, 0.08)'
    }));

  const skillsHeatmap = [
    { name: 'Python', levels: [4, 4, 3, 4, 4, 2, 4, 3] },
    { name: 'Machine Learning', levels: [3, 4, 4, 3, 2, 1, 3, 4] },
    { name: 'System Design', levels: [2, 3, 4, 4, 3, 2, 4, 2] },
    { name: 'AWS Cloud Services', levels: [4, 2, 3, 4, 2, 4, 3, 3] },
    { name: 'Data Structures', levels: [3, 4, 4, 3, 4, 3, 2, 4] },
    { name: 'Leadership & Alignment', levels: [2, 2, 3, 4, 3, 4, 4, 2] },
    { name: 'Communication Presence', levels: [4, 4, 4, 3, 4, 4, 3, 4] }
  ];

  const trendData = [
    { name: 'Week 1', completed: Math.max(1, Math.round(completedInterviews * 0.2)) },
    { name: 'Week 2', completed: Math.max(2, Math.round(completedInterviews * 0.4)) },
    { name: 'Week 3', completed: Math.max(3, Math.round(completedInterviews * 0.7)) },
    { name: 'Week 4', completed: completedInterviews }
  ];

  const pieData = [
    { name: 'Excellent (90-100)', value: totalAssessments > 0 ? Math.round(candidatesList.filter(c => c.score >= 90).length / totalAssessments * 100) : 25, color: '#2dd4bf' },
    { name: 'Good (75-89)', value: totalAssessments > 0 ? Math.round(candidatesList.filter(c => c.score >= 75 && c.score < 90).length / totalAssessments * 100) : 45, color: '#818cf8' },
    { name: 'Average (60-74)', value: totalAssessments > 0 ? Math.round(candidatesList.filter(c => c.score >= 60 && c.score < 75).length / totalAssessments * 100) : 20, color: '#fbbf24' },
    { name: 'Needs Improvement (<60)', value: totalAssessments > 0 ? Math.round(candidatesList.filter(c => c.score < 60).length / totalAssessments * 100) : 10, color: '#fb7185' }
  ];

  const hiringProcess = [
    { step: '1', title: 'Create role intake', body: 'Recruiter answers guided questions once.' },
    { step: '2', title: 'Approve hiring blueprint', body: 'JD Agent extracts and recruiter edits role expectations.' },
    { step: '3', title: 'Share assessment link', body: 'Copy shareable invitation link for candidates.' },
    { step: '4', title: 'Candidate screens self', body: 'AI asks role-specific questions and follow-ups dynamically.' },
    { step: '5', title: 'Review ranking and report', body: 'Leaderboard, heatmap, transcript, and recommendation are ready.' },
  ];

  const funnelData = [
    { label: 'Invited', count: totalAssessments, percentage: '100%', color: '#818cf8' },
    { label: 'Completed', count: completedInterviews, percentage: totalAssessments > 0 ? `${Math.round(completedInterviews / totalAssessments * 100)}%` : '0%', color: '#4f46e5' },
    { label: 'Shortlisted', count: strongHires, percentage: totalAssessments > 0 ? `${Math.round(strongHires / totalAssessments * 100)}%` : '0%', color: '#2dd4bf' }
  ];

  const handleCandidateClick = (cand: any) => {
    setInterviewId(cand.interview_id);
    navigate('/recruiter/report');
  };

  return (
    <div className="layout-container max-w-7xl pt-4 pb-16">
      
      {/* Page Title with action button */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-8 border-b border-subtle pb-6" style={{ borderColor: 'var(--color-border-subtle)' }}>
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white font-sans">
            Recruiter Workspace
          </h1>
          <p className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)' }}>
            Review parsed candidates, inspect screening evidence, and open full interview reports for every applicant.
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button 
            onClick={() => navigate('/recruiter/create')}
            className="btn-base btn-primary text-xs py-2.5 px-4 font-semibold gap-2"
          >
            <Plus className="w-4 h-4" />
            <span>Create Recruiter Assessment</span>
          </button>
        </div>
      </div>

      {/* Main Workspace Grid - Sidebar navigation + Content panel */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        
        {/* Left Sidebar Menu */}
        <div className="md:col-span-3 space-y-4">
          <div className="card-premium p-4 bg-dark-900/10 space-y-6">
            <div className="space-y-1.5 text-xs font-semibold">
              {[
                { icon: LayoutGridIcon, label: 'Overview' },
                { icon: Award, label: 'Active Jobs' },
                { icon: Users, label: 'Candidates List' },
                { icon: CheckSquare, label: 'Assessments Pool' },
                { icon: Target, label: 'Interview Modules' },
                { icon: BarChart3, label: 'Analytics' },
                { icon: Compass, label: 'Reports Hub' },
                { icon: Settings, label: 'Platform Settings' }
              ].map((item, idx) => {
                const Icon = item.icon;
                const isActive = activeTab === item.label;
                return (
                  <button
                    key={idx}
                    onClick={() => setActiveTab(item.label)}
                    className="w-full flex items-center justify-between px-3 py-2.5 rounded-md transition-colors text-left"
                    style={{
                      color: isActive ? 'white' : 'var(--color-text-secondary)',
                      backgroundColor: isActive ? 'rgba(255, 255, 255, 0.05)' : 'transparent',
                      border: isActive ? '1px solid var(--color-border-subtle)' : '1px solid transparent'
                    }}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className="w-4 h-4 opacity-80" />
                      <span>{item.label}</span>
                    </div>
                    {item.label === 'Candidates List' && totalAssessments > 0 && (
                      <span className="text-[10px] bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-full font-bold">
                        {totalAssessments}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            <div className="border-t border-subtle pt-4" style={{ borderColor: 'var(--color-border-subtle)' }}>
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-white/10 border border-white/10 flex items-center justify-center text-xs font-bold text-white">AJ</div>
                <div>
                  <span className="text-xs font-semibold text-white block">Arjun V.</span>
                  <span className="text-[10px] block" style={{ color: 'var(--color-text-tertiary)' }}>Talent Acquisition Lead</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Quick Stats Panel */}
          <div className="card-premium p-4 bg-dark-900/10 space-y-3">
            <span className="text-[10px] uppercase font-bold tracking-widest text-dark-500 block" style={{ color: 'var(--color-text-tertiary)' }}>
              Agent Health & Audit
            </span>
            <div className="space-y-2 text-[11px]">
              <div className="flex justify-between">
                <span style={{ color: 'var(--color-text-secondary)' }}>Evaluator Core:</span>
                <span className="text-emerald-400 font-semibold">Online</span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: 'var(--color-text-secondary)' }}>STAR Analyzer:</span>
                <span className="text-emerald-400 font-semibold">Online</span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: 'var(--color-text-secondary)' }}>System Load:</span>
                <span style={{ color: 'var(--color-text-primary)' }}>12%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Dashboard Area */}
        <div className="md:col-span-9 space-y-6">
          
          {/* Internal Title Header with Filter bar */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-lg font-bold text-white leading-tight">Good morning, Arjun 👋</h3>
              <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-secondary)' }}>Here is what is happening with your hiring pipeline today.</p>
            </div>
            
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-dark-400" />
                <input 
                  type="text" 
                  placeholder="Search candidates..." 
                  className="input-base !py-1.5 !pl-9 text-xs"
                  style={{ width: '180px' }}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <select 
                className="input-base !py-1.5 text-xs font-semibold cursor-pointer"
                style={{ width: '110px' }}
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
              >
                <option>This Month</option>
                <option>Last 30 Days</option>
                <option>All Time</option>
              </select>
            </div>
          </div>

          {loading ? (
            <div className="card-premium p-16 text-center space-y-3">
              <span className="text-xs tracking-wider uppercase text-theme-tertiary">Accessing Database Records...</span>
            </div>
          ) : activeTab === 'Active Jobs' ? (
            <div className="card-premium p-6 bg-dark-900/10 space-y-6">
              <div className="flex items-center justify-between border-b border-subtle pb-4" style={{ borderColor: 'var(--color-border-subtle)' }}>
                <div>
                  <h4 className="text-sm font-bold uppercase tracking-wider text-white">Active Assessments & Job Blueprints</h4>
                  <p className="text-[10px]" style={{ color: 'var(--color-text-secondary)' }}>Manage active JDs and copy candidate invitation links.</p>
                </div>
                <span className="text-xs bg-indigo-500/20 text-indigo-300 px-2.5 py-1 rounded-full font-bold">
                  {jdsList.length} Active Positions
                </span>
              </div>
              
              {jdsList.length === 0 ? (
                <div className="text-center py-10 text-xs text-theme-secondary">
                  No active assessments found. Click "Create Recruiter Assessment" to get started.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {jdsList.map((job) => {
                    const jobCandidates = candidatesList.filter(c => String(c.jd_id) === String(job.id));
                    const jobCompleted = jobCandidates.filter(c => c.status === 'Completed');
                    const scores = jobCandidates.map(c => c.score || 0);
                    const avgScore = scores.length > 0 ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0;
                    const topScore = scores.length > 0 ? Math.max(...scores) : 0;

                    return (
                      <div key={job.id} className="rounded-lg border border-subtle p-5 bg-dark-950/40 hover:border-slate-700 transition-all flex flex-col justify-between" style={{ borderColor: 'var(--color-border-subtle)' }}>
                        <div>
                          <div className="flex justify-between items-start gap-4">
                            <h5 className="text-base font-bold text-white leading-tight">{job.title}</h5>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded border border-blue-500/20 text-blue-400 bg-blue-600/10">
                              {job.seniority || 'Mid'}
                            </span>
                          </div>
                          <p className="text-xs text-theme-secondary mt-1">
                            {job.department || 'General'} • {job.industry || 'Tech'}
                          </p>

                          {/* ATS Micro Metrics Section */}
                          <div className="grid grid-cols-2 gap-2 mt-4 mb-4 pt-3 border-t border-subtle/40">
                            <div className="bg-white/5 p-2 rounded">
                              <span className="text-[9px] uppercase tracking-wider text-theme-tertiary block">Candidates</span>
                              <span className="text-sm font-bold text-white">{jobCandidates.length}</span>
                            </div>
                            <div className="bg-white/5 p-2 rounded">
                              <span className="text-[9px] uppercase tracking-wider text-theme-tertiary block">Completed</span>
                              <span className="text-sm font-bold text-white">{jobCompleted.length}</span>
                            </div>
                            <div className="bg-white/5 p-2 rounded">
                              <span className="text-[9px] uppercase tracking-wider text-theme-tertiary block">Avg Score</span>
                              <span className="text-sm font-bold text-white">{avgScore ? `${avgScore}%` : 'N/A'}</span>
                            </div>
                            <div className="bg-white/5 p-2 rounded">
                              <span className="text-[9px] uppercase tracking-wider text-theme-tertiary block">Top Score</span>
                              <span className="text-sm font-bold text-emerald-400">{topScore ? `${topScore}%` : 'N/A'}</span>
                            </div>
                          </div>
                          
                          {/* Shareable Link Box */}
                          <div className="p-3 bg-dark-900/60 rounded border border-subtle space-y-2" style={{ borderColor: 'var(--color-border-subtle)' }}>
                            <span className="text-[9px] uppercase tracking-widest font-bold text-theme-tertiary block">
                              Candidate Assessment Link
                            </span>
                            <div className="flex items-center gap-2">
                              <input 
                                readOnly 
                                className="input-base !bg-dark-950/60 !py-1.5 text-[11px] flex-grow text-theme-secondary"
                                value={`${window.location.protocol}//${window.location.host}/assessment/take/${job.id}`}
                              />
                              <button 
                                onClick={() => {
                                  navigator.clipboard.writeText(`${window.location.protocol}//${window.location.host}/assessment/take/${job.id}`);
                                  alert('Assessment invitation link copied!');
                                }}
                                className="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-[11px] font-bold transition-all"
                              >
                                Copy
                              </button>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex justify-between items-center mt-5 pt-3 border-t border-subtle" style={{ borderColor: 'var(--color-border-subtle)' }}>
                          <span className="text-[10px] text-theme-tertiary">
                            Created: {job.created_at ? job.created_at.split('T')[0] : 'N/A'}
                          </span>
                          <button 
                            onClick={() => {
                              setSearchQuery(job.title);
                              setActiveTab('Candidates List');
                            }}
                            className="px-3 py-1.5 bg-white/5 hover:bg-white/10 text-white rounded text-xs font-semibold transition-all border border-white/10"
                          >
                            Filter Candidates
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ) : activeTab === 'Candidates List' ? (
            /* Full Candidates Database View */
            <div className="card-premium p-6 bg-dark-900/10 space-y-6">
              <div className="flex items-center justify-between border-b border-subtle pb-4" style={{ borderColor: 'var(--color-border-subtle)' }}>
                <div>
                  <h4 className="text-sm font-bold uppercase tracking-wider text-white">Candidates Directory</h4>
                  <p className="text-[10px]" style={{ color: 'var(--color-text-secondary)' }}>Inspect parsed resumes, JD alignment, screening scores, and full candidate reports.</p>
                </div>
                <span className="text-xs bg-indigo-500/20 text-indigo-300 px-2.5 py-1 rounded-full font-bold">
                  {candidatesList.length} Total Profiles
                </span>
              </div>

              {candidatesList.length === 0 ? (
                <div className="text-center py-10 text-xs text-theme-secondary">
                  No candidate submissions found yet for active assessment jobs.
                </div>
              ) : (
                <div className="overflow-x-auto w-full">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-subtle/80 text-[10px] uppercase font-bold tracking-wider text-dark-500" style={{ color: 'var(--color-text-tertiary)' }}>
                        <th className="pb-3">Candidate</th>
                        <th className="pb-3">Target Role</th>
                        <th className="pb-3 text-center">Resume Parsed</th>
                        <th className="pb-3 text-center">Interview</th>
                        <th className="pb-3 text-center">Report</th>
                        <th className="pb-3 text-center font-bold">Score</th>
                        <th className="pb-3 text-center">Pipeline Status</th>
                        <th className="pb-3">Date Completed</th>
                        <th className="pb-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-subtle/40">
                      {candidatesList
                        .filter(c => c.candidate_name.toLowerCase().includes(searchQuery.toLowerCase()) || c.job_title.toLowerCase().includes(searchQuery.toLowerCase()))
                        .map((cand, idx) => {
                          const tag = cand.score >= 85 ? 'Strong Hire' : cand.score >= 70 ? 'Consider' : 'Needs Prep';
                          const color = cand.score >= 85 ? 'var(--color-accent-teal)' : cand.score >= 70 ? 'rgb(251, 191, 36)' : 'var(--color-accent-coral)';
                          const bg = cand.score >= 85 ? 'rgba(45, 212, 191, 0.08)' : cand.score >= 70 ? 'rgba(251, 191, 36, 0.08)' : 'rgba(251, 113, 133, 0.08)';
                          const isCompleted = cand.status === 'Completed';

                          return (
                            <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                              <td className="py-3.5 pr-2">
                                <span className="font-semibold text-white block">{cand.candidate_name}</span>
                                <span className="text-[10px] opacity-75" style={{ color: 'var(--color-text-secondary)' }}>{cand.candidate_email}</span>
                              </td>
                              <td className="py-3.5 text-white/90">{cand.job_title}</td>
                              <td className="py-3.5 text-center text-emerald-400 font-bold text-sm">✓</td>
                              <td className="py-3.5 text-center font-bold text-sm">
                                {isCompleted ? (
                                  <span className="text-emerald-400">✓</span>
                                ) : (
                                  <span className="text-amber-400 animate-pulse">•••</span>
                                )}
                              </td>
                              <td className="py-3.5 text-center font-bold text-sm">
                                {isCompleted ? (
                                  <span className="text-emerald-400">✓</span>
                                ) : (
                                  <span className="text-slate-600">-</span>
                                )}
                              </td>
                              <td className="py-3.5 text-center font-bold text-white text-sm">
                                {cand.score}%
                              </td>
                              <td className="py-3.5 text-center">
                                <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${isCompleted ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-300 border border-amber-500/20'}`}>
                                  {isCompleted ? 'Completed' : 'In Progress'}
                                </span>
                              </td>
                              <td className="py-3.5 text-dark-400" style={{ color: 'var(--color-text-secondary)' }}>{cand.date || 'N/A'}</td>
                              <td className="py-3.5 text-right">
                                <button
                                  onClick={() => handleCandidateClick(cand)}
                                  className="px-2.5 py-1.5 bg-white/5 hover:bg-white/10 text-white rounded font-medium transition-colors border border-white/10"
                                >
                                  Full Report
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ) : activeTab === 'Overview' ? (
            <>
              <div className="card-premium p-5">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-5">
                  <div>
                    <span className="text-[10px] uppercase tracking-widest font-bold text-theme-tertiary block mb-1">Recruiter workload reducer</span>
                    <h4 className="text-lg font-bold text-theme-primary">Full hiring process, step by step</h4>
                  </div>
                  <button onClick={() => navigate('/recruiter/create')} className="btn-base btn-secondary text-xs">
                    Create assessment
                  </button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                  {hiringProcess.map((item) => (
                    <div key={item.step} className="rounded-lg border border-subtle p-4" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
                      <span className="w-7 h-7 rounded-md flex items-center justify-center text-xs font-bold mb-3" style={{ backgroundColor: 'var(--color-mauve-strong)' }}>
                        {item.step}
                      </span>
                      <span className="text-xs font-bold text-theme-primary block mb-1">{item.title}</span>
                      <p className="text-[11px] leading-5 text-theme-secondary">{item.body}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Metric Summary Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {metricCards.map((card, idx) => (
                  <div key={idx} className="card-premium p-4 flex flex-col justify-between text-left">
                    <span className="text-[10px] font-bold uppercase tracking-wider block" style={{ color: 'var(--color-text-secondary)' }}>
                      {card.label}
                    </span>
                    <div className="flex items-baseline justify-between mt-3">
                      <span className="text-2xl font-bold text-white leading-none">{card.value}</span>
                      <span className="text-xs font-semibold flex items-center gap-0.5 text-emerald-400">
                        <TrendingUp className="w-3 h-3" />
                        {card.rate}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Core Analytics Grid */}
              <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
                
                {/* Left: Top Candidates Table */}
                <div className="md:col-span-7 card-premium p-5 flex flex-col justify-between">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-xs uppercase font-bold tracking-wider text-white">Top Candidates</span>
                    <span 
                      onClick={() => setActiveTab('Candidates List')}
                      className="text-xs text-indigo-400 font-semibold cursor-pointer hover:underline"
                    >
                      View All Candidates
                    </span>
                  </div>
                  {topCandidates.length === 0 ? (
                    <p className="text-xs text-theme-secondary py-4 text-center">No candidates screened yet.</p>
                  ) : (
                    <div className="space-y-3.5">
                      {topCandidates
                        .filter(c => c.name.toLowerCase().includes(searchQuery.toLowerCase()))
                        .map((cand, idx) => (
                          <div 
                            key={idx} 
                            onClick={() => handleCandidateClick(cand)}
                            className="flex items-center justify-between text-xs border-b border-subtle pb-2.5 last:border-0 last:pb-0 cursor-pointer hover:bg-white/[0.02] p-1.5 rounded transition-all"
                            style={{ borderColor: 'var(--color-border-subtle)' }}
                          >
                            <div>
                              <span className="font-semibold text-white block hover:text-indigo-300">{cand.name}</span>
                              <span className="text-[10px] block" style={{ color: 'var(--color-text-tertiary)' }}>{cand.role}</span>
                            </div>
                            <div className="flex items-center gap-3">
                              <span className="font-bold text-white text-sm">{cand.score}%</span>
                              <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase flex items-center gap-1" style={{ color: cand.color, backgroundColor: cand.bg }}>
                                {cand.tag}
                                <ArrowUpRight className="w-2.5 h-2.5" />
                              </span>
                            </div>
                          </div>
                        ))}
                    </div>
                  )}
                </div>

                {/* Right: Skills Heatmap */}
                <div className="md:col-span-5 card-premium p-5 flex flex-col justify-between">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-xs uppercase font-bold tracking-wider text-white font-sans">Skills Heatmap</span>
                    <span className="text-[10px] text-dark-500 font-semibold" style={{ color: 'var(--color-text-tertiary)' }}>Low ➔ High</span>
                  </div>
                  <div className="space-y-3">
                    {skillsHeatmap.slice(0, 6).map((skill, idx) => (
                      <div key={idx} className="flex items-center justify-between text-[11px] gap-2">
                        <span className="text-dark-400 font-semibold truncate w-24" style={{ color: 'var(--color-text-secondary)' }}>{skill.name}</span>
                        <div className="flex gap-1 flex-grow justify-end">
                          {skill.levels.map((lvl, lIdx) => {
                            const opacity = lvl === 4 ? 0.95 : lvl === 3 ? 0.65 : lvl === 2 ? 0.35 : 0.1;
                            return (
                              <div 
                                key={lIdx} 
                                className="w-3.5 h-3.5 rounded-sm" 
                                style={{ 
                                  backgroundColor: `rgba(129, 140, 248, ${opacity})` 
                                }} 
                              />
                            );
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

              </div>

              {/* Secondary Analytics Grid */}
              <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
                
                {/* Left: Pipeline Funnel Layout */}
                <div className="md:col-span-6 card-premium p-5 space-y-4">
                  <div className="flex items-center justify-between border-b border-subtle pb-3" style={{ borderColor: 'var(--color-border-subtle)' }}>
                    <span className="text-xs uppercase font-bold tracking-wider text-white">Candidate Pipeline</span>
                    <span className="text-[10px]" style={{ color: 'var(--color-text-tertiary)' }}>Full Stage Flow</span>
                  </div>
                  
                  <div className="space-y-3">
                    {funnelData.map((stage, idx) => (
                      <div key={idx} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="font-semibold text-white">{stage.label}</span>
                          <div className="flex items-center gap-2">
                            <span style={{ color: 'var(--color-text-secondary)' }}>{stage.count}</span>
                            <span className="text-[10px] font-bold text-dark-500" style={{ color: 'var(--color-text-tertiary)' }}>({stage.percentage})</span>
                          </div>
                        </div>
                        <div className="w-full bg-dark-950 h-2.5 rounded-full overflow-hidden border border-subtle" style={{ borderColor: 'var(--color-border-subtle)' }}>
                          <div 
                            className="h-full rounded-full transition-all duration-500"
                            style={{ 
                              width: stage.percentage, 
                              backgroundColor: stage.color,
                              boxShadow: `0 0 8px ${stage.color}40`
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Right: Assessment Insights Doughnut & Interview Trend */}
                <div className="md:col-span-6 card-premium p-5 flex flex-col justify-between">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-xs uppercase font-bold tracking-wider text-white">Assessment Insights</span>
                    <span className="text-[10px]" style={{ color: 'var(--color-text-tertiary)' }}>By Score Category</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-12 gap-4 items-center">
                    {/* Pie Chart display */}
                    <div className="sm:col-span-5 h-[120px] flex items-center justify-center">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={pieData}
                            cx="50%"
                            cy="50%"
                            innerRadius={36}
                            outerRadius={50}
                            paddingAngle={4}
                            dataKey="value"
                          >
                            {pieData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                        </PieChart>
                      </ResponsiveContainer>
                    </div>

                    {/* Legend list */}
                    <div className="sm:col-span-7 space-y-2 text-[10px] font-semibold">
                      {pieData.map((item, idx) => (
                        <div key={idx} className="flex items-center justify-between gap-2" style={{ whiteSpace: 'nowrap' }}>
                          <div className="flex items-center gap-1.5 min-w-0">
                            <div className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: item.color }} />
                            <span className="truncate" style={{ color: 'var(--color-text-secondary)' }}>{item.name}</span>
                          </div>
                          <span className="text-white flex-shrink-0" style={{ marginLeft: 'auto' }}>{item.value}%</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Trend Chart (Fast Preview) */}
                  <div className="border-t border-subtle pt-4 mt-4" style={{ borderColor: 'var(--color-border-subtle)' }}>
                    <span className="text-[10px] uppercase font-bold tracking-wider block mb-2" style={{ color: 'var(--color-text-tertiary)' }}>
                      Monthly Interview Trend
                    </span>
                    <div className="h-[80px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={trendData}>
                          <XAxis dataKey="name" tick={{ fill: 'var(--color-text-tertiary)', fontSize: 9 }} axisLine={false} tickLine={false} />
                          <Tooltip 
                            contentStyle={{ backgroundColor: 'var(--color-bg-secondary)', borderColor: 'var(--color-border-subtle)', borderRadius: 6 }} 
                            labelStyle={{ color: 'var(--color-text-primary)', fontSize: 10 }}
                            itemStyle={{ color: 'var(--color-accent-indigo)', fontSize: 10 }}
                          />
                          <Line 
                            type="monotone" 
                            dataKey="completed" 
                            stroke="var(--color-accent-indigo)" 
                            strokeWidth={2.5} 
                            dot={{ r: 3, stroke: 'var(--color-bg-primary)', strokeWidth: 1.5, fill: 'var(--color-accent-indigo)' }} 
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                </div>

              </div>
            </>
          ) : (
            /* Placeholder for Settings, Modules etc. */
            <div className="card-premium p-12 text-center bg-dark-900/10 space-y-4">
              <span className="text-xs uppercase font-bold tracking-wider px-2 py-0.5 rounded border border-subtle text-dark-400" style={{ borderColor: 'var(--color-border-subtle)', color: 'var(--color-text-secondary)' }}>
                Section in Development
              </span>
              <h4 className="text-sm font-semibold text-white">{activeTab} Workspaces</h4>
              <p className="text-xs max-w-sm mx-auto" style={{ color: 'var(--color-text-secondary)' }}>
                This module is currently integrated into the AI screening framework. Go to <strong>Overview</strong> or <strong>Candidates List</strong> to view active assessment diagnostic feeds.
              </p>
            </div>
          )}

        </div>

      </div>

    </div>
  );
}

// Icon helper since LayoutGrid is imported as layout from react
function LayoutGridIcon(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect width="7" height="9" x="3" y="3" rx="1" />
      <rect width="7" height="5" x="14" y="3" rx="1" />
      <rect width="7" height="9" x="14" y="10" rx="1" />
      <rect width="7" height="5" x="3" y="14" rx="1" />
    </svg>
  );
}
