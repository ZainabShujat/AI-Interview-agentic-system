import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Users, Award, CheckSquare, Target, BarChart3, Compass, Settings, 
  Search, Plus, ArrowUpRight, TrendingUp
} from 'lucide-react';
import { 
  ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, XAxis, 
  Tooltip
} from 'recharts';

export default function Dashboard() {
  const navigate = useNavigate();
  
  // Tab states for inside the dashboard
  const [activeTab, setActiveTab] = useState('Overview');
  const [timeRange, setTimeRange] = useState('This Month');
  const [searchQuery, setSearchQuery] = useState('');

  // Sample data to populate charts and lists
  const metricCards = [
    { label: 'Total Assessments', value: '1,248', rate: '+18.5%', labelColor: 'var(--color-accent-indigo)' },
    { label: 'Completed Interviews', value: '842', rate: '+22.7%', labelColor: 'var(--color-accent-teal)' },
    { label: 'Strong Hire', value: '142', rate: '+15.3%', labelColor: 'var(--color-accent-teal)' },
    { label: 'Average Score', value: '78.4', rate: '+6.2%', labelColor: 'var(--color-accent-indigo)' }
  ];

  const topCandidates = [
    { name: 'Aarav Sharma', role: 'Senior AI Engineer', score: 94, tag: 'Strong Hire', color: 'var(--color-accent-teal)', bg: 'rgba(45, 212, 191, 0.08)' },
    { name: 'Neha Verma', role: 'AI Engineer', score: 89, tag: 'Strong Hire', color: 'var(--color-accent-teal)', bg: 'rgba(45, 212, 191, 0.08)' },
    { name: 'Rohan Mehta', role: 'ML Engineer', score: 86, tag: 'Consider', color: 'rgb(251, 191, 36)', bg: 'rgba(251, 191, 36, 0.08)' },
    { name: 'Ishita Kapoor', role: 'Data Scientist', score: 82, tag: 'Consider', color: 'rgb(251, 191, 36)', bg: 'rgba(251, 191, 36, 0.08)' },
    { name: 'Karan Bansal', role: 'Backend Engineer', score: 78, tag: 'Consider', color: 'rgb(251, 191, 36)', bg: 'rgba(251, 191, 36, 0.08)' }
  ];

  const fullCandidatesList = [
    { name: 'Aarav Sharma', email: 'aarav@google.com', role: 'Senior AI Engineer', score: 94, tag: 'Strong Hire', date: '2026-06-22', starRate: '4/4', status: 'Passed Proctoring', color: 'var(--color-accent-teal)', bg: 'rgba(45, 212, 191, 0.08)' },
    { name: 'Neha Verma', email: 'neha.v@stripe.com', role: 'AI Engineer', score: 89, tag: 'Strong Hire', date: '2026-06-23', starRate: '3/4', status: 'Passed Proctoring', color: 'var(--color-accent-teal)', bg: 'rgba(45, 212, 191, 0.08)' },
    { name: 'Rohan Mehta', email: 'rohan.mehta@amazon.com', role: 'ML Engineer', score: 86, tag: 'Consider', date: '2026-06-21', starRate: '3/4', status: 'Minor Warnings', color: 'rgb(251, 191, 36)', bg: 'rgba(251, 191, 36, 0.08)' },
    { name: 'Ishita Kapoor', email: 'ishita@outlook.com', role: 'Data Scientist', score: 82, tag: 'Consider', date: '2026-06-24', starRate: '2/4', status: 'Passed Proctoring', color: 'rgb(251, 191, 36)', bg: 'rgba(251, 191, 36, 0.08)' },
    { name: 'Karan Bansal', email: 'karan.b@gmail.com', role: 'Backend Engineer', score: 78, tag: 'Consider', date: '2026-06-20', starRate: '3/4', status: 'Passed Proctoring', color: 'rgb(251, 191, 36)', bg: 'rgba(251, 191, 36, 0.08)' },
    { name: 'Vikram Singh', email: 'vikram.s@github.com', role: 'DevOps Lead', score: 74, tag: 'Consider', date: '2026-06-19', starRate: '2/4', status: 'Passed Proctoring', color: 'rgb(251, 191, 36)', bg: 'rgba(251, 191, 36, 0.08)' },
    { name: 'Ananya Roy', email: 'ananya@yahoo.com', role: 'Frontend Engineer', score: 68, tag: 'Needs Prep', date: '2026-06-18', starRate: '2/4', status: 'Multiple Focus Lost Warnings', color: 'var(--color-accent-coral)', bg: 'rgba(251, 113, 133, 0.08)' },
    { name: 'Siddharth Sen', email: 'sid.sen@outlook.com', role: 'Full Stack Engineer', score: 62, tag: 'Needs Prep', date: '2026-06-17', starRate: '1/4', status: 'Passed Proctoring', color: 'var(--color-accent-coral)', bg: 'rgba(251, 113, 133, 0.08)' },
  ];

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
    { name: 'Week 1', completed: 180 },
    { name: 'Week 2', completed: 320 },
    { name: 'Week 3', completed: 480 },
    { name: 'Week 4', completed: 842 }
  ];

  const pieData = [
    { name: 'Excellent (90-100)', value: 25, color: '#2dd4bf' },
    { name: 'Good (75-89)', value: 45, color: '#818cf8' },
    { name: 'Average (60-74)', value: 20, color: '#fbbf24' },
    { name: 'Needs Improvement (<60)', value: 10, color: '#fb7185' }
  ];

  // Pipeline funnel steps
  const funnelData = [
    { label: 'Invited', count: 1248, percentage: '100%', color: '#818cf8' },
    { label: 'In Progress', count: 842, percentage: '67.4%', color: '#6366f1' },
    { label: 'Completed', count: 562, percentage: '45.0%', color: '#4f46e5' },
    { label: 'Shortlisted', count: 142, percentage: '11.3%', color: '#2dd4bf' },
    { label: 'Hired', count: 28, percentage: '2.2%', color: '#10b981' }
  ];

  const handleCandidateClick = (_cand: any) => {
    // Navigate to report page to view details
    navigate('/report');
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
            Conduct assessment reviews, monitor agent evaluation funnels, and examine structured diagnostics.
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button 
            onClick={() => navigate('/upload')}
            className="btn-base btn-primary text-xs py-2.5 px-4 font-semibold gap-2"
          >
            <Plus className="w-4 h-4" />
            <span>New Candidate Assessment</span>
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
                    {item.label === 'Candidates List' && (
                      <span className="text-[10px] bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-full font-bold">
                        12
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

          {activeTab === 'Candidates List' ? (
            /* Full Candidates Database View */
            <div className="card-premium p-6 bg-dark-900/10 space-y-6">
              <div className="flex items-center justify-between border-b border-subtle pb-4" style={{ borderColor: 'var(--color-border-subtle)' }}>
                <div>
                  <h4 className="text-sm font-bold uppercase tracking-wider text-white">Candidates Directory</h4>
                  <p className="text-[10px]" style={{ color: 'var(--color-text-secondary)' }}>Review detailed mock screening scores and anti-cheat indicators.</p>
                </div>
                <span className="text-xs bg-indigo-500/20 text-indigo-300 px-2.5 py-1 rounded-full font-bold">
                  {fullCandidatesList.length} Total Profiles
                </span>
              </div>

              <div className="overflow-x-auto w-full">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-subtle/80 text-[10px] uppercase font-bold tracking-wider text-dark-500" style={{ color: 'var(--color-text-tertiary)' }}>
                      <th className="pb-3">Candidate</th>
                      <th className="pb-3">Target Role</th>
                      <th className="pb-3 text-center">Score</th>
                      <th className="pb-3 text-center">STAR Rate</th>
                      <th className="pb-3">Proctoring Status</th>
                      <th className="pb-3">Date Completed</th>
                      <th className="pb-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-subtle/40">
                    {fullCandidatesList
                      .filter(c => c.name.toLowerCase().includes(searchQuery.toLowerCase()) || c.role.toLowerCase().includes(searchQuery.toLowerCase()))
                      .map((cand, idx) => (
                        <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                          <td className="py-3.5 pr-2">
                            <span className="font-semibold text-white block">{cand.name}</span>
                            <span className="text-[10px] opacity-75" style={{ color: 'var(--color-text-secondary)' }}>{cand.email}</span>
                          </td>
                          <td className="py-3.5 text-white/90">{cand.role}</td>
                          <td className="py-3.5 text-center">
                            <span className="font-bold text-white text-sm mr-2">{cand.score}</span>
                            <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase" style={{ color: cand.color, backgroundColor: cand.bg }}>
                              {cand.tag}
                            </span>
                          </td>
                          <td className="py-3.5 text-center font-medium text-white/90">{cand.starRate}</td>
                          <td className="py-3.5">
                            <span className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                              cand.status.includes('Violations') 
                                ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' 
                                : cand.status.includes('Warnings') 
                                ? 'bg-amber-500/10 text-amber-300 border border-amber-500/20' 
                                : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            }`}>
                              {cand.status}
                            </span>
                          </td>
                          <td className="py-3.5 text-dark-400" style={{ color: 'var(--color-text-secondary)' }}>{cand.date}</td>
                          <td className="py-3.5 text-right">
                            <button
                              onClick={() => handleCandidateClick(cand)}
                              className="px-2.5 py-1.5 bg-white/5 hover:bg-white/10 text-white rounded font-medium transition-colors border border-white/10"
                            >
                              View Diagnostics
                            </button>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : activeTab === 'Overview' ? (
            <>
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
                      className="text-xs text-indigo-400 font-semibold cursor-pointer hover:underline cursor-pointer"
                    >
                      View All Candidates
                    </span>
                  </div>
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
                            <span className="font-bold text-white text-sm">{cand.score}</span>
                            <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase flex items-center gap-1" style={{ color: cand.color, backgroundColor: cand.bg }}>
                              {cand.tag}
                              <ArrowUpRight className="w-2.5 h-2.5" />
                            </span>
                          </div>
                        </div>
                      ))}
                  </div>
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
                            labelStyle={{ color: 'white', fontSize: 10 }}
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
