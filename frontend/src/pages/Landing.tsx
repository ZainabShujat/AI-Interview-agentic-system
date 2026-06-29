import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowRight,
  BarChart3,
  BrainCircuit,
  Building2,
  FileSearch,
  GraduationCap,
  MessageSquare,
  ShieldCheck,
  Trophy,
  Users,
  Workflow,
} from 'lucide-react';

const fadeInUp = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.45, ease: 'easeOut' } },
};

const recruiterFlow = [
  'Create role intake',
  'Parse JD into hiring blueprint',
  'Screen parsed candidate profiles',
  'Review ranking, evidence, and full reports',
];

const platformSteps = [
  {
    icon: FileSearch,
    title: 'Resume and JD agents',
    body: 'Extract skills, experience, domain, seniority, responsibilities, and candidate evidence into structured records.',
  },
  {
    icon: BarChart3,
    title: 'Deterministic match analysis',
    body: 'The match score is computed from normalized structured data so recruiters can see exactly what matched and what is missing.',
  },
  {
    icon: Workflow,
    title: 'Interview planner',
    body: 'The system turns role gaps into an interview blueprint across resume validation, technical, scenario, behavioral, and leadership rounds.',
  },
  {
    icon: BrainCircuit,
    title: 'Adaptive interview engine',
    body: 'Questioning adapts to previous answers, difficulty, weak areas, and demonstrated strengths instead of following a fixed script.',
  },
  {
    icon: MessageSquare,
    title: 'Judge and memory agents',
    body: 'Every answer is evaluated for accuracy, depth, communication, practicality, problem solving, and role-specific signal.',
  },
  {
    icon: Trophy,
    title: 'Reports and leaderboard',
    body: 'Students see readiness and ranking. Recruiters see candidate ranking, skill heatmaps, transcripts, and full reports.',
  },
];

export default function Landing() {
  return (
    <div className="relative min-h-screen font-sans" style={{ backgroundColor: 'var(--color-bg-primary)', color: 'var(--color-text-primary)' }}>
      <section className="max-w-6xl mx-auto px-6 pt-2 pb-8 md:pt-4 md:pb-12">
        <motion.div initial="hidden" animate="visible" variants={fadeInUp} className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          <div className="lg:col-span-7 space-y-8">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md border border-blue-500/20 bg-blue-600/10 text-blue-400 text-xs font-bold uppercase tracking-widest">
              <ShieldCheck className="w-3.5 h-3.5" />
              Agentic hiring assessment platform
            </div>

            <div className="space-y-5">
              <h1 className="text-5xl md:text-6xl font-black leading-tight tracking-tight text-theme-primary">
                Screen candidates with adaptive AI interviews and evidence-backed hiring reports.
              </h1>
              <p className="text-lg leading-8 max-w-2xl text-theme-secondary">
                HireIntel is mostly built for recruiters: create role blueprints, parse candidates, run adaptive interviews, rank applicants, and review full diagnostic reports. Students can also self-assess against a target job and see where they rank.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <Link to="/recruiter" className="btn-base btn-primary px-6 py-3 gap-2">
                <Building2 className="w-4 h-4" />
                <span>Open Recruiter Workspace</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link to="/student" className="btn-base btn-secondary px-6 py-3 gap-2">
                <GraduationCap className="w-4 h-4" />
                <span>Student Self-Assessment</span>
              </Link>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
              {[
                ['JD Parsing', 'Structured role blueprint'],
                ['Resume Parsing', 'Candidate evidence'],
                ['Adaptive Interview', 'Follow-up questions'],
                ['Leaderboard', 'Ranked by job'],
              ].map(([label, body]) => (
                <div key={label} className="rounded-lg border border-subtle p-4" style={{ backgroundColor: 'var(--color-bg-secondary)' }}>
                  <span className="text-xs font-bold text-theme-primary block">{label}</span>
                  <span className="text-[11px] text-theme-secondary">{body}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="lg:col-span-5">
            <div className="card-premium p-6 space-y-5">
              <div className="flex items-start justify-between gap-4 pb-4 border-b border-subtle">
                <div>
                  <span className="text-[10px] uppercase tracking-widest font-bold text-theme-tertiary block mb-1">Recruiter Control Room</span>
                  <h2 className="text-xl font-bold text-theme-primary">Senior AI Engineer</h2>
                  <p className="text-xs text-theme-secondary mt-1">Healthcare GenAI platform role</p>
                </div>
                <span className="text-xs font-bold px-2.5 py-1 rounded-md border border-emerald-400/20 text-emerald-400 bg-emerald-500/10">
                  82% Match
                </span>
              </div>

              <div className="space-y-3">
                {recruiterFlow.map((item, index) => (
                  <div key={item} className="flex items-center gap-3 rounded-lg border border-subtle p-3" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
                    <div className="w-7 h-7 rounded-md bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-[11px] font-bold text-blue-400">
                      {index + 1}
                    </div>
                    <span className="text-sm font-semibold text-theme-primary">{item}</span>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-3 gap-3 pt-1">
                <MiniMetric label="Rank" value="#2" />
                <MiniMetric label="Score" value="88" />
                <MiniMetric label="Signal" value="Hire" />
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      <section className="border-y border-subtle" style={{ backgroundColor: 'var(--color-bg-secondary)' }}>
        <div className="max-w-6xl mx-auto px-6 py-10 grid grid-cols-1 md:grid-cols-3 gap-6">
          <ValueCard icon={Users} title="For recruiters" body="Screen many candidates against one job, compare them on a leaderboard, and open full reports with transcripts and scoring evidence." />
          <ValueCard icon={GraduationCap} title="For students" body="Upload a resume and target JD, measure readiness, complete the AI interview, and see your ranking for that job." />
          <ValueCard icon={ShieldCheck} title="For enterprises" body="Keep the process explainable: role blueprint, deterministic fit, adaptive interview evidence, and auditable recommendations." />
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 py-20 md:py-24">
        <div className="max-w-2xl mb-10">
          <span className="text-xs font-bold uppercase tracking-widest text-blue-400 block mb-3">Architecture</span>
          <h2 className="text-3xl md:text-4xl font-bold text-theme-primary tracking-tight">
            The platform follows the agentic interview architecture your team described.
          </h2>
          <p className="text-sm leading-7 text-theme-secondary mt-4">
            It starts with resume and JD parsing, computes transparent gap analysis, creates an interview roadmap, adapts through specialized interview agents, and ends with ranking and reports.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {platformSteps.map((step) => (
            <div key={step.title} className="card-premium p-6">
              <step.icon className="w-5 h-5 text-blue-400 mb-4" />
              <h3 className="text-base font-bold text-theme-primary mb-2">{step.title}</h3>
              <p className="text-xs leading-6 text-theme-secondary">{step.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 pb-24">
        <div className="card-premium p-8 md:p-10 flex flex-col lg:flex-row lg:items-center justify-between gap-8">
          <div>
            <span className="text-xs font-bold uppercase tracking-widest text-theme-tertiary block mb-3">Next action</span>
            <h2 className="text-3xl font-bold text-theme-primary tracking-tight">Start with the recruiter workspace.</h2>
            <p className="text-sm text-theme-secondary mt-3 max-w-2xl">
              The product is recruiter-centered, but the student path is available for practice and readiness measurement.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-3 flex-shrink-0">
            <Link to="/recruiter/create" className="btn-base btn-primary px-6 py-3 gap-2">
              <span>Create Assessment</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link to="/student" className="btn-base btn-secondary px-6 py-3">
              Student Path
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}

function ValueCard({ icon: Icon, title, body }: { icon: any; title: string; body: string }) {
  return (
    <div className="flex gap-4">
      <div className="w-10 h-10 rounded-lg bg-blue-600/10 border border-blue-500/20 flex items-center justify-center flex-shrink-0">
        <Icon className="w-5 h-5 text-blue-400" />
      </div>
      <div>
        <h3 className="text-sm font-bold text-theme-primary mb-1">{title}</h3>
        <p className="text-xs leading-6 text-theme-secondary">{body}</p>
      </div>
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-subtle p-3 text-center" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
      <span className="text-[10px] uppercase tracking-widest text-theme-tertiary block mb-1">{label}</span>
      <span className="text-lg font-bold text-theme-primary">{value}</span>
    </div>
  );
}
