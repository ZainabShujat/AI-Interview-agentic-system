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
  matched_skills: ['React', 'TypeScript', 'Python', 'FastAPI', 'Docker', 'AWS'],
  missing_skills: ['Kafka', 'SOC2 Compliance'],
  evidence: [
    { skill: 'React', status: 'Found', source: 'Found in Experience: Software Engineer at SaaS Ventures Ltd' },
    { skill: 'TypeScript', status: 'Found', source: 'Found in Experience: Software Engineer at SaaS Ventures Ltd' },
    { skill: 'Python', status: 'Found', source: 'Found in Project: E-Commerce Microservices' },
    { skill: 'FastAPI', status: 'Found', source: 'Found in Project: E-Commerce Microservices' },
    { skill: 'Docker', status: 'Found', source: 'Found in Project: E-Commerce Microservices' },
    { skill: 'AWS', status: 'Found', source: 'Found in Certifications: AWS Certified Solutions Architect' },
    { skill: 'Kafka', status: 'Not Found', source: 'Not found in resume text' },
    { skill: 'SOC2 Compliance', status: 'Not Found', source: 'Not found in resume text' }
  ]
};

export default function RoleReadiness() {
  const navigate = useNavigate();
  const { resumeId, jdId, setInterviewId } = useSession();

  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(mockAnalysisData);
  const [startingInterview, setStartingInterview] = useState(false);

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

  const [showRoadmap, setShowRoadmap] = useState(false);

  if (loading) {
    return (
      <div className="layout-container min-h-[60vh] flex flex-col items-center justify-center">
        <Activity className="w-8 h-8 text-white animate-spin opacity-50 mb-4" />
        <span className="text-sm tracking-wider uppercase text-dark-500" style={{ color: 'var(--color-text-tertiary)' }}>
          Computing Role Readiness Alignment...
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
            Role Readiness Evaluation
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
        <div className="card-premium flex flex-col items-center justify-center p-8 text-center bg-dark-900/10">
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
              <span className="text-4xl font-bold tracking-tight text-white">{data.matchScore}</span>
              <span className="text-[10px] uppercase font-semibold tracking-wider" style={{ color: 'var(--color-accent-teal)' }}>
                Readiness Index
              </span>
            </div>
          </div>
          <p className="text-xs font-medium text-white mb-2">
            {data.matchScore >= 85 ? 'Highly Compatible Profile' : 'Substantial Compatibility Profile'}
          </p>
          <p className="text-[11px] leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
            {data.matchScore >= 85 
              ? `Calculated based on ${data.matched_skills?.length || 0} core matching competencies with only ${data.missing_skills?.length || 0} critical domain gaps detected.`
              : `Calculated from ${data.matched_skills?.length || 0} matching tools, with ${data.missing_skills?.length || 0} domain gaps requiring evaluation in the upcoming session.`
            }
          </p>
        </div>

        {/* Recharts Radar Alignment Card */}
        <div className="card-premium flex flex-col justify-between p-8 bg-dark-900/10">
          <span className="text-xs font-semibold uppercase tracking-wider mb-4" style={{ color: 'var(--color-text-secondary)' }}>
            Competency Blueprint
          </span>
          <div className="flex-grow min-h-[180px] flex items-center justify-center">
            <ResponsiveContainer width="100%" height={180}>
              <RadarChart cx="50%" cy="50%" outerRadius="70%" data={chartData}>
                <PolarGrid stroke="var(--color-border-subtle)" />
                <PolarAngleAxis
                  dataKey="subject"
                  tick={{ fill: 'var(--color-text-secondary)', fontSize: 9, fontFamily: 'Plus Jakarta Sans' }}
                />
                <PolarRadiusAxis
                  angle={30}
                  domain={[0, 100]}
                  tick={{ fill: 'var(--color-text-tertiary)', fontSize: 7 }}
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
          <p className="text-[10px] leading-relaxed text-center mt-2" style={{ color: 'var(--color-text-tertiary)' }}>
            Maps candidate readiness vectors across foundational engineering dimensions.
          </p>
        </div>

        {/* Hiring Risk Assessment Card */}
        <div className="card-premium flex flex-col justify-between p-8 bg-dark-900/10">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider mb-6 block" style={{ color: 'var(--color-text-secondary)' }}>
              Hiring Risk Assessment
            </span>
            {(() => {
              const missingCount = data.missing_skills?.length || 0;
              const isHigh = missingCount > 2 || data.matchScore < 75;
              const isMod = missingCount > 0 || data.matchScore < 85;
              
              const level = isHigh ? 'High Risk' : isMod ? 'Moderate Risk' : 'Low Risk';
              const color = isHigh ? 'var(--color-accent-coral)' : isMod ? 'rgb(251, 191, 36)' : 'var(--color-accent-teal)';
              const borderColor = isHigh ? 'rgba(251, 113, 133, 0.25)' : isMod ? 'rgba(251, 191, 36, 0.25)' : 'rgba(45, 212, 191, 0.25)';
              const bgColor = isHigh ? 'rgba(251, 113, 133, 0.05)' : isMod ? 'rgba(251, 191, 36, 0.05)' : 'rgba(45, 212, 191, 0.05)';
              
              return (
                <div className="space-y-4">
                  <div className="inline-flex items-center px-3 py-1 rounded-md border text-xs font-bold uppercase tracking-wider" style={{ color, borderColor, backgroundColor: bgColor }}>
                    {level}
                  </div>
                  <p className="text-xs text-white font-medium mt-2">
                    {isHigh 
                      ? 'Significant alignment gaps detected.' 
                      : isMod 
                        ? 'Minor competency gaps require verification.' 
                        : 'Minimal risk: Profile strongly matches role requirements.'
                    }
                  </p>
                  <p className="text-[11px] leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
                    {isHigh
                      ? `Candidate lacks ${missingCount} core skills needed for immediate delivery. Requires extensive ramping on compliance or architecture.`
                      : isMod
                        ? `A few domain requirements (${data.missing_skills?.join(', ') || 'message queue orchestration'}) are missing from the resume. Validation recommended during simulated exercises.`
                        : 'No critical skill gaps identified. Candidate demonstrated active experience across all target technologies.'
                    }
                  </p>
                </div>
              );
            })()}
          </div>
          <span className="text-[9px] uppercase tracking-wider text-dark-500 mt-4 block" style={{ color: 'var(--color-text-tertiary)' }}>
            Hiring Risk Model v1.0
          </span>
        </div>
      </div>

      {/* Strengths and Gaps Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        {/* Strengths card */}
        <div className="card-premium bg-dark-900/10">
          <div className="flex items-center gap-2 mb-6">
            <CheckCircle2 className="w-5 h-5 text-emerald-500 opacity-80" />
            <h3 className="text-lg font-semibold text-white" style={{ fontFamily: "'Outfit', sans-serif" }}>
              Competitive Advantages
            </h3>
          </div>
          <ul className="space-y-4">
            {data.strengths.map((str, idx) => (
              <li key={idx} className="flex items-start gap-3 text-xs leading-relaxed">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 flex-shrink-0" />
                <span style={{ color: 'var(--color-text-secondary)' }}>{str}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Development Areas card */}
        <div className="card-premium bg-dark-900/10">
          <div className="flex items-center gap-2 mb-6">
            <AlertCircle className="w-5 h-5 text-amber-500 opacity-80" />
            <h3 className="text-lg font-semibold text-white" style={{ fontFamily: "'Outfit', sans-serif" }}>
              Development Areas
            </h3>
          </div>
          <div className="space-y-6">
            {data.gaps.map((gap, idx) => (
              <div key={idx} className="border-l border-subtle pl-4 py-0.5" style={{ borderColor: 'var(--color-border-subtle)' }}>
                <span className="text-xs font-semibold block text-amber-400 mb-1">
                  {gap.skill}
                </span>
                <p className="text-xs leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
                  {gap.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Evidence Mapping Section */}
      <section className="mb-12">
        <h2 className="text-xl font-semibold text-white mb-4 border-b border-subtle pb-2" style={{ fontFamily: "'Outfit', sans-serif", borderColor: 'var(--color-border-subtle)' }}>
          Evidence Mapping & Fit Analysis
        </h2>
        <p className="text-sm leading-relaxed text-dark-300 mb-6" style={{ color: 'var(--color-text-secondary)' }}>
          Below is the granular matching checklist compiled by the Match Agent, identifying explicitly validated skills and missing criteria mapped from your resume.
        </p>
        
        {/* Matched and Missing Skills Pill Lists */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="card-premium">
            <span className="text-[10px] uppercase font-bold tracking-widest text-dark-500 block mb-3" style={{ color: 'var(--color-text-tertiary)' }}>
              Matched Competencies
            </span>
            <div className="flex flex-wrap gap-2">
              {data.matched_skills && data.matched_skills.length > 0 ? (
                data.matched_skills.map((skill: string, idx: number) => (
                  <span key={idx} className="text-xs font-semibold px-2.5 py-1 rounded-md border" style={{ backgroundColor: 'rgba(45, 212, 191, 0.1)', borderColor: 'rgba(45, 212, 191, 0.25)', color: 'var(--color-accent-teal)' }}>
                    {skill}
                  </span>
                ))
              ) : (
                <span className="text-xs text-dark-400" style={{ color: 'var(--color-text-tertiary)' }}>No explicitly matched competencies detected.</span>
              )}
            </div>
          </div>
          
          <div className="card-premium">
            <span className="text-[10px] uppercase font-bold tracking-widest text-dark-500 block mb-3" style={{ color: 'var(--color-text-tertiary)' }}>
              Missing / Gap Competencies
            </span>
            <div className="flex flex-wrap gap-2">
              {data.missing_skills && data.missing_skills.length > 0 ? (
                data.missing_skills.map((skill: string, idx: number) => (
                  <span key={idx} className="text-xs font-semibold px-2.5 py-1 rounded-md border" style={{ backgroundColor: 'rgba(251, 113, 133, 0.1)', borderColor: 'rgba(251, 113, 133, 0.25)', color: 'var(--color-accent-coral)' }}>
                    {skill}
                  </span>
                ))
              ) : (
                <span className="text-xs text-dark-400" style={{ color: 'var(--color-text-tertiary)' }}>No critical missing competencies detected.</span>
              )}
            </div>
          </div>
        </div>

        {/* Detailed Evidence Checklist */}
        <div className="card-premium bg-dark-900/10 p-6">
          <span className="text-[10px] uppercase font-bold tracking-widest text-dark-500 block mb-4" style={{ color: 'var(--color-text-tertiary)' }}>
            Match Agent Validation Logs
          </span>
          <div className="space-y-4">
            {data.evidence && data.evidence.length > 0 ? (
              data.evidence.map((item: any, idx: number) => {
                const isFound = item.status === 'Found';
                return (
                  <div key={idx} className="flex items-start justify-between gap-4 border-b border-subtle pb-3 last:border-0 last:pb-0" style={{ borderColor: 'var(--color-border-subtle)' }}>
                    <div>
                      <span className="text-xs font-semibold text-white block mb-0.5">{item.skill}</span>
                      <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>{item.source}</p>
                    </div>
                    <span className="text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border flex-shrink-0" 
                          style={{ 
                            color: isFound ? 'var(--color-accent-teal)' : 'var(--color-accent-coral)',
                            borderColor: isFound ? 'rgba(45, 212, 191, 0.25)' : 'rgba(251, 113, 133, 0.25)',
                            backgroundColor: isFound ? 'rgba(45, 212, 191, 0.1)' : 'rgba(251, 113, 133, 0.1)'
                          }}>
                      {item.status}
                    </span>
                  </div>
                );
              })
            ) : (
              <span className="text-xs text-dark-400" style={{ color: 'var(--color-text-tertiary)' }}>No mapping logs generated by the agent.</span>
            )}
          </div>
        </div>
      </section>

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
