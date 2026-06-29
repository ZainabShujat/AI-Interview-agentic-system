import { useNavigate } from 'react-router-dom';
import { ArrowRight, Medal, Trophy, TrendingUp, UserRoundCheck } from 'lucide-react';

const leaderboardRows = [
  { rank: 1, name: 'Aarav Sharma', score: 94, status: 'Interview Complete', delta: '+8' },
  { rank: 2, name: 'Neha Verma', score: 89, status: 'Interview Complete', delta: '+4' },
  { rank: 3, name: 'You', score: 84, status: 'New Submission', delta: '+12', current: true },
  { rank: 4, name: 'Rohan Mehta', score: 81, status: 'Interview Complete', delta: '-1' },
  { rank: 5, name: 'Ishita Kapoor', score: 78, status: 'Interview Complete', delta: '+2' },
  { rank: 6, name: 'Karan Bansal', score: 72, status: 'Interview Complete', delta: '-3' },
];

export default function JobLeaderboard() {
  const navigate = useNavigate();

  return (
    <div className="layout-container max-w-5xl">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <aside className="lg:col-span-4">
          <div className="card-premium p-7 space-y-6">
            <div className="w-12 h-12 rounded-xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center">
              <Trophy className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <span className="text-[10px] uppercase tracking-widest font-bold text-theme-tertiary block mb-2">
                Job Leaderboard
              </span>
              <h1 className="text-3xl font-bold text-theme-primary tracking-tight">
                You ranked #3 for this role.
              </h1>
              <p className="text-sm mt-3 text-theme-secondary">
                Ranking combines readiness match, interview performance, communication quality, and role-specific gap coverage.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Metric label="Your Score" value="84" />
              <Metric label="Percentile" value="82nd" />
              <Metric label="Role" value="Senior SWE" />
              <Metric label="Status" value="Ranked" />
            </div>
            <button onClick={() => navigate('/report')} className="btn-base btn-secondary w-full gap-2">
              <span>View My Report</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </aside>

        <section className="lg:col-span-8">
          <div className="card-premium p-8">
            <div className="p-3 mb-5 text-[11px] rounded-lg border flex items-start gap-2.5" style={{ backgroundColor: 'rgba(99, 102, 241, 0.1)', borderColor: 'rgba(99, 102, 241, 0.25)', color: 'var(--color-text-primary)' }}>
              <div className="mt-0.5 text-indigo-400">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              </div>
              <p className="leading-normal">
                <strong>Demo Workspace Notice:</strong> To demonstrate the ranking engine immediately, this leaderboard includes **sample candidate scores**. Your score will dynamically position itself here once you complete the interview.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 border-b border-subtle pb-5">
              <div>
                <span className="text-[10px] uppercase tracking-widest font-bold text-theme-tertiary block mb-2">
                  Senior Software Engineer
                </span>
                <h2 className="text-2xl font-bold text-theme-primary tracking-tight">Candidate Ranking</h2>
              </div>
              <div className="flex items-center gap-2 text-xs text-theme-secondary">
                <TrendingUp className="w-4 h-4 text-blue-400" />
                <span>Updated after every completed interview</span>
              </div>
            </div>

            <div className="space-y-3">
              {leaderboardRows.map((row) => (
                <div
                  key={row.rank}
                  className="rounded-lg border p-4 flex items-center justify-between gap-4"
                  style={{
                    borderColor: row.current ? 'rgba(59, 130, 246, 0.45)' : 'var(--color-border-subtle)',
                    backgroundColor: row.current ? 'rgba(37, 99, 235, 0.12)' : 'var(--color-bg-primary)',
                  }}
                >
                  <div className="flex items-center gap-4 min-w-0">
                    <div className="w-10 h-10 rounded-lg border border-subtle flex items-center justify-center text-sm font-bold text-theme-primary">
                      {row.rank <= 3 ? <Medal className="w-5 h-5 text-blue-400" /> : row.rank}
                    </div>
                    <div className="min-w-0">
                      <span className="text-sm font-bold text-theme-primary block truncate">{row.name}</span>
                      <span className="text-xs text-theme-secondary">{row.status}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-5 flex-shrink-0">
                    <span className="text-xs font-semibold text-theme-secondary">{row.delta}</span>
                    <span className="text-xl font-bold text-theme-primary">{row.score}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 rounded-lg border border-subtle p-5" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
              <div className="flex items-start gap-3">
                <UserRoundCheck className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <p className="text-xs leading-relaxed text-theme-secondary">
                  Recruiters see this candidate in their screening dashboard with the parsed resume, JD match evidence, interview transcript, scoring rationale, and full report.
                </p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-subtle p-4" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
      <span className="text-[10px] uppercase tracking-widest font-bold text-theme-tertiary block mb-1">{label}</span>
      <span className="text-lg font-bold text-theme-primary">{value}</span>
    </div>
  );
}
