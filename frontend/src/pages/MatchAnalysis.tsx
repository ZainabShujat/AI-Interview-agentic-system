import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle2, AlertCircle, ArrowRight, BookOpen, ChevronRight, Activity } from 'lucide-react';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { useSession } from '../App';
import axios from 'axios';

// Polished mock data for fallback
const mockAnalysisData = {
  matchScore: 82,
  roleInfo: {
    title: 'Senior Software Engineer',
    industry: 'Financial Technology',
    seniority: 'Senior',
  },
  readinessDetails: [
    { name: 'Core Coding & Architecture', score: 85 },
    { name: 'System Design & Scalability', score: 75 },
    { name: 'Team Leadership & Culture', score: 90 },
    { name: 'Domain Experience (Fintech)', score: 70 },
    { name: 'Tooling & CI/CD Pipelines', score: 90 },
  ],
  strengths: [
    'Deep expertise in React, TypeScript, and state management architectures (Redux, Zustand).',
    'Proven track record of designing REST and GraphQL APIs with Python-based microservices.',
    'Extensive leadership experience mentoring junior engineers and leading agile sprint groups.',
    'Strong deployment and operations expertise using Docker, Kubernetes, and AWS Cloud services.',
  ],
  gaps: [
    {
      skill: 'High-Frequency Messaging Networks',
      description: 'The job requires familiarity with Apache Kafka or RabbitMQ. Your profile highlights database caching but lacks message queue orchestration.',
    },
    {
      skill: 'Fintech Security Compliance',
      description: 'The description emphasizes PCI-DSS or SOC2 compliance experience. Your background is primarily in consumer product SaaS without direct audit exposure.',
    },
  ],
};

export default function MatchAnalysis() {
  const navigate = useNavigate();
  const { resumeId, jdId, setInterviewId } = useSession();

  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(mockAnalysisData);
  const [startingInterview, setStartingInterview] = useState(false);
  const [showRoadmap, setShowRoadmap] = useState(false);

  useEffect(() => {
    const fetchMatch = async () => {
      if (!resumeId || !jdId) {
        // If not uploaded, just show mock after a brief loading state
        setTimeout(() => setLoading(false), 800);
        return;
      }

      try {
        const res = await axios.post('/api/match', {
          resume_id: resumeId,
          jd_id: jdId,
        });
        setData(res.data);
      } catch (err) {
        console.warn('Backend failed or not connected. Using fallback mockup.', err);
      } finally {
        setLoading(false);
      }
    };

    fetchMatch();
  }, [resumeId, jdId]);

  const handleStartSimulation = async () => {
    setStartingInterview(true);
    try {
      let interviewIdRes = 'mock-interview-456';
      try {
        const res = await axios.post('/api/interview/start', {
          resume_id: resumeId || 'mock-resume-123',
          jd_id: jdId || 'mock-jd-123',
        });
        interviewIdRes = res.data.id || res.data.interview_id;
      } catch (err) {
        console.warn('Backend connection failed. Using mock interview.', err);
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }
      setInterviewId(interviewIdRes);
      setShowRoadmap(true);
    } catch (err) {
      console.error(err);
      setInterviewId('mock-interview-456');
      setShowRoadmap(true);
    } finally {
      setStartingInterview(false);
    }
  };

  if (loading) {
    return (
      <div className="layout-container min-h-[60vh] flex flex-col items-center justify-center">
        <Activity className="w-8 h-8 text-white animate-spin opacity-50 mb-4" />
        <span className="text-sm tracking-wider uppercase text-dark-500" style={{ color: 'var(--color-text-tertiary)' }}>
          Computing Role Match Alignment...
        </span>
      </div>
    );
  }

  // Radar chart formatting
  const chartData = data.readinessDetails.map((item) => ({
    subject: item.name,
    score: item.score,
    fullMark: 100,
  }));

  if (showRoadmap) {
    return (
      <div className="layout-container max-w-xl py-6">
        <div className="text-center mb-10">
          <span className="text-[10px] uppercase font-bold tracking-widest text-dark-500 mb-1 block" style={{ color: 'var(--color-text-tertiary)' }}>
            Assessment Roadmap
          </span>
          <h1 className="text-3xl font-bold text-white tracking-tight" style={{ fontFamily: "'Outfit', sans-serif" }}>
            Simulation Plan
          </h1>
          <p className="text-sm mt-2" style={{ color: 'var(--color-text-secondary)' }}>
            Configured by the Interview Planner Agent based on your role match gap data.
          </p>
        </div>

        <div className="card-premium space-y-6 p-8">
          <div className="border-l-2 border-subtle pl-4 py-1" style={{ borderColor: 'var(--color-border-hover)' }}>
            <span className="text-xs uppercase font-bold tracking-wider text-dark-400 block" style={{ color: 'var(--color-text-tertiary)' }}>Module 1</span>
            <span className="text-sm font-semibold text-white mt-1 block">Technical Architecture Validation</span>
            <p className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)' }}>
              Evaluates core coding principles, caching protocols, and framework design depth.
            </p>
          </div>

          <div className="border-l-2 border-subtle pl-4 py-1" style={{ borderColor: 'var(--color-border-hover)' }}>
            <span className="text-xs uppercase font-bold tracking-wider text-dark-400 block" style={{ color: 'var(--color-text-tertiary)' }}>Module 2</span>
            <span className="text-sm font-semibold text-white mt-1 block">Dynamic Scenario Orchestration</span>
            <p className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)' }}>
              Presents real-world database migration problems and system scale limits.
            </p>
          </div>

          <div className="border-l-2 border-subtle pl-4 py-1" style={{ borderColor: 'var(--color-border-hover)' }}>
            <span className="text-xs uppercase font-bold tracking-wider text-dark-400 block" style={{ color: 'var(--color-text-tertiary)' }}>Module 3</span>
            <span className="text-sm font-semibold text-white mt-1 block">Behavioral Alignment Review</span>
            <p className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)' }}>
              Assesses developer collaboration patterns, code quality, and senior advocacy.
            </p>
          </div>

          <div className="pt-6 border-t border-subtle flex justify-center" style={{ borderColor: 'var(--color-border-subtle)' }}>
            <button
              onClick={() => navigate('/interview')}
              className="btn-base btn-primary text-sm font-semibold py-3 px-8 gap-2 w-full justify-center"
            >
              <span>Begin Assessment Session</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="layout-container max-w-5xl">
      {/* Title block */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 mb-12">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-dark-500 mb-2 block" style={{ color: 'var(--color-text-tertiary)' }}>
            Comparative Evaluation
          </span>
          <h1 className="text-3xl font-bold text-white tracking-tight" style={{ fontFamily: "'Outfit', sans-serif" }}>
            Role Match Analysis
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>
            Targeting: <span className="text-white font-medium">{data.roleInfo.title}</span> • {data.roleInfo.seniority} Level
          </p>
        </div>

        <button
          onClick={handleStartSimulation}
          disabled={startingInterview}
          className="btn-base btn-primary text-sm font-semibold py-3 px-6 gap-2"
        >
          {startingInterview ? (
            <>
              <Loader2Icon />
              <span>Building Roadmap...</span>
            </>
          ) : (
            <>
              <span>Proceed to Interview Simulation</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
        {/* Score Ring Card */}
        <div className="card-premium flex flex-col items-center justify-center p-8 text-center">
          <span className="text-xs font-semibold uppercase tracking-wider mb-6" style={{ color: 'var(--color-text-secondary)' }}>
            Overall Alignment
          </span>
          <div className="relative w-36 h-36 flex items-center justify-center mb-6">
            {/* Custom SVG Radial Progress */}
            <svg className="w-full h-full transform -rotate-90">
              <circle
                cx="72"
                cy="72"
                r="64"
                stroke="var(--color-border-subtle)"
                strokeWidth="6"
                fill="transparent"
              />
              <circle
                cx="72"
                cy="72"
                r="64"
                stroke="var(--color-accent-teal)"
                strokeWidth="6"
                fill="transparent"
                strokeDasharray={2 * Math.PI * 64}
                strokeDashoffset={2 * Math.PI * 64 * (1 - data.matchScore / 100)}
                strokeLinecap="round"
                style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center">
              <span className="text-4xl font-bold tracking-tight text-white">{data.matchScore}%</span>
              <span className="text-[10px] uppercase font-semibold tracking-wider" style={{ color: 'var(--color-accent-teal)' }}>
                Match Score
              </span>
            </div>
          </div>
          <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
            Your profile demonstrates strong structural compatibility. Some minor gaps identified.
          </p>
        </div>

        {/* Recharts Radar Alignment Card */}
        <div className="card-premium lg:col-span-2 flex flex-col">
          <span className="text-xs font-semibold uppercase tracking-wider mb-4" style={{ color: 'var(--color-text-secondary)' }}>
            Competency Blueprint
          </span>
          <div className="flex-grow min-h-[220px] flex items-center justify-center">
            <ResponsiveContainer width="100%" height={240}>
              <RadarChart cx="50%" cy="50%" outerRadius="75%" data={chartData}>
                <PolarGrid stroke="var(--color-border-subtle)" />
                <PolarAngleAxis
                  dataKey="subject"
                  tick={{ fill: 'var(--color-text-secondary)', fontSize: 10, fontFamily: 'Plus Jakarta Sans' }}
                />
                <PolarRadiusAxis
                  angle={30}
                  domain={[0, 100]}
                  tick={{ fill: 'var(--color-text-tertiary)', fontSize: 8 }}
                  stroke="transparent"
                />
                <Radar
                  name="Candidate"
                  dataKey="score"
                  stroke="var(--color-accent-indigo)"
                  fill="var(--color-accent-indigo)"
                  fillOpacity={0.15}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Strengths and Gaps Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        {/* Strengths card */}
        <div className="card-premium">
          <div className="flex items-center gap-2 mb-6">
            <CheckCircle2 className="w-5 h-5 text-emerald-500 opacity-80" />
            <h3 className="text-lg font-semibold text-white" style={{ fontFamily: "'Outfit', sans-serif" }}>
              Identified Core Strengths
            </h3>
          </div>
          <ul className="space-y-4">
            {data.strengths.map((str, idx) => (
              <li key={idx} className="flex items-start gap-3 text-sm">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-2 flex-shrink-0" />
                <span style={{ color: 'var(--color-text-secondary)' }}>{str}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Development Areas card */}
        <div className="card-premium">
          <div className="flex items-center gap-2 mb-6">
            <AlertCircle className="w-5 h-5 text-amber-500 opacity-80" />
            <h3 className="text-lg font-semibold text-white" style={{ fontFamily: "'Outfit', sans-serif" }}>
              Development Gaps
            </h3>
          </div>
          <div className="space-y-6">
            {data.gaps.map((gap, idx) => (
              <div key={idx} className="border-l border-subtle pl-4 py-0.5" style={{ borderColor: 'var(--color-border-subtle)' }}>
                <span className="text-xs font-semibold block text-amber-400 mb-1">
                  {gap.skill}
                </span>
                <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                  {gap.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Promo Alert */}
      <div className="card-premium card-glass flex flex-col md:flex-row items-center justify-between gap-6 p-6 text-center md:text-left">
        <div className="flex items-start gap-4 text-left">
          <div className="w-10 h-10 rounded-full bg-white/5 border border-white/10 flex items-center justify-center flex-shrink-0 mt-1">
            <BookOpen className="w-5 h-5 text-white" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white">Simulation Practice Ready</h4>
            <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
              Based on the compliance and messaging gaps detected, we have configured a customized 3-question session to evaluate your adaptive responses.
            </p>
          </div>
        </div>
        <button
          onClick={handleStartSimulation}
          disabled={startingInterview}
          className="btn-base btn-secondary text-xs !py-2 !px-4 flex-shrink-0 flex items-center gap-1.5"
        >
          <span>Start Simulation</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}

function Loader2Icon() {
  return (
    <svg className="w-4 h-4 animate-spin text-dark-950" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" strokeDasharray="30" strokeDashoffset="0" />
    </svg>
  );
}
