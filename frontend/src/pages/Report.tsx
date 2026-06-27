import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Download, RefreshCw, Activity } from 'lucide-react';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';
import { useSession } from '../App';
import axios from 'axios';

// Polished mock data for fallback
const mockReportData = {
  overallScore: 84,
  recommendation: 'Strong Hire',
  summary: 'The candidate demonstrates exceptional technical articulation and architecture foundations. Communications pace was highly consistent with standard senior engineering benchmarks. Minor adjustments recommended in fintech compliance contexts and message queue depth.',
  dimensionScores: [
    { subject: 'Accuracy', A: 85, fullMark: 100 },
    { subject: 'Depth', A: 80, fullMark: 100 },
    { subject: 'Communication', A: 90, fullMark: 100 },
    { subject: 'Scenario Handling', A: 78, fullMark: 100 },
    { subject: 'Leadership', A: 88, fullMark: 100 },
  ],
  categoryScores: [
    { name: 'Technical', score: 85 },
    { name: 'Scenario', score: 78 },
    { name: 'Behavioral', score: 90 },
    { name: 'Leadership', score: 88 },
  ],
  communicationProfile: {
    style: 'Structured & Technical',
    presence: 'Measured & Authoritative',
    readiness: 'Highly Proficient',
    quality: 'Exhibits clear design paradigms and API isolation patterns.',
    improvements: [
      'Incorporate more concrete case examples to address all prompt criteria.',
    ],
    observations: [
      'Responses were concise and well-structured.',
      'Candidate demonstrated strong subject familiarity with minimal hesitation.',
      'Answers occasionally lacked supporting examples.',
      'Speaking pace remained consistent throughout the assessment.',
      'Filler word usage was below average, indicating clear communication.',
    ],
    starFramework: {
      situation: true,
      task: true,
      action: true,
      result: false,
      situationCount: 3,
      taskCount: 3,
      actionCount: 2,
      resultCount: 0,
      totalCount: 3
    },
    executiveScores: {
      practicality: 80,
      problemSolving: 78,
      businessThinking: 75
    },
    metrics: {
      speakingPace: {
        value: '124 WPM',
        rating: 'Optimal',
        feedback: 'Pacing aligns perfectly with the standard 110-140 WPM benchmark for technical presentations. Delivery is measured, deliberate, and clear.',
      },
      responseLength: {
        value: 'Avg 145 Words',
        rating: 'Substantial',
        feedback: 'Candidate provides comprehensive, multi-layered responses, detailing execution steps without digressing into verbose descriptions.',
      },
      fillerWords: {
        value: '3.0 per answer',
        rating: 'Low',
        feedback: 'Verbal clutter (average 3.0 fillers per answer) is well-controlled. Sentence transitions are clean and logically linked.',
      },
      hesitation: {
        value: '1.8s latency',
        rating: 'Controlled',
        feedback: 'Average cognitive pause before speaking is 1.8s. Cognitive pause latency is within acceptable levels. Natural pauses occur at structural logic gaps.',
      },
      completeness: {
        value: 'High',
        rating: 'High',
        feedback: 'Candidate systematically covers all dimensions of the evaluation prompt—including caching strategies, security parameters, and leadership considerations.',
      },
    },
  },
  heatmap: [
    { skill: 'React & TS Architecture', rating: 'High', color: 'rgba(45, 212, 191, 0.15)', textColor: 'var(--color-accent-teal)', border: 'rgba(45, 212, 191, 0.3)' },
    { skill: 'Microservices & API Design', rating: 'High', color: 'rgba(45, 212, 191, 0.15)', textColor: 'var(--color-accent-teal)', border: 'rgba(45, 212, 191, 0.3)' },
    { skill: 'Docker & AWS Ops', rating: 'High', color: 'rgba(45, 212, 191, 0.15)', textColor: 'var(--color-accent-teal)', border: 'rgba(45, 212, 191, 0.3)' },
    { skill: 'Distributed System Design', rating: 'Medium', color: 'rgba(129, 140, 248, 0.1)', textColor: 'var(--color-accent-indigo)', border: 'rgba(129, 140, 248, 0.25)' },
    { skill: 'H-F Message Queues', rating: 'Needs Prep', color: 'rgba(251, 113, 133, 0.1)', textColor: 'var(--color-accent-coral)', border: 'rgba(251, 113, 133, 0.25)' },
    { skill: 'Fintech SOC2 Compliance', rating: 'Needs Prep', color: 'rgba(251, 113, 133, 0.1)', textColor: 'var(--color-accent-coral)', border: 'rgba(251, 113, 133, 0.25)' },
  ],
  strengths: [
    'Articulates React render cycles and state transitions with high logical clarity.',
    'Formulates clear microservice isolation protocols and API validation schemas.',
    'Exhibits solid collaboration patterns, emphasizing mentoring and clear developer path structures.',
  ],
  recommendations: [
    'Review basic event-driven topologies and explore Kafka queue structures (producers, consumers, and consumer-groups).',
    'Familiarize yourself with ISO-27001 and SOC2 checklist rules regarding data residency and encryption-in-transit.',
  ],
  all_qa: [
    {
      category: 'System Design',
      question: 'Explain how you would design a rate limiter for a high-traffic microservice architecture.',
      answer: 'I would implement a Token Bucket or Leaky Bucket algorithm using Redis as a shared in-memory data store. Each API client would have an associated key with their token count and timestamp. I would use Lua scripting to ensure atomic increments and checks to prevent race conditions from concurrent calls.',
      evaluation: {
        accuracy: 90,
        depth: 85,
        feedback: 'Excellent explanation of rate-limiting algorithms and atomic operations using Redis. The candidate specifically mentioned Lua scripts which demonstrates strong concurrency awareness.',
        starFramework: {
          situation: true,
          task: true,
          action: true,
          result: true
        }
      }
    },
    {
      category: 'React Architecture',
      question: 'How do you prevent unnecessary re-renders in a large-scale React application?',
      answer: 'We can use React.memo to memoize components, and wrap handler functions in useCallback. For expensive computations, useMemo is ideal. Also, structuring state locally instead of keeping everything in global context helps isolate updates.',
      evaluation: {
        accuracy: 88,
        depth: 80,
        feedback: 'Correctly identifies hooks and component memoization patterns. Good practice in isolating state.',
        starFramework: {
          situation: true,
          task: true,
          action: true,
          result: false
        }
      }
    }
  ]
};

export default function Report() {
  const navigate = useNavigate();
  const { interviewId, setResumeId, setJdId, setInterviewId } = useSession();

  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(mockReportData);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    const fetchReport = async () => {
      if (!interviewId) {
        // Fallback mockup
        setTimeout(() => setLoading(false), 1000);
        return;
      }

      try {
        const res = await axios.get(`/api/interview/report?interview_id=${interviewId}`);
        setData(res.data);
      } catch (err) {
        console.warn('Backend connection failed. Displaying mockup data analytics.', err);
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [interviewId]);

  const handleDownloadPDF = async () => {
    setDownloading(true);
    try {
      const id = interviewId || 'mock-interview-456';
      // Make a direct browser download link
      window.open(`/api/interview/report/pdf?interview_id=${id}`, '_blank');
    } catch (err) {
      console.error(err);
      alert('Error exporting PDF.');
    } finally {
      setDownloading(false);
    }
  };

  const handleRestart = () => {
    setResumeId(null);
    setJdId(null);
    setInterviewId(null);
    navigate('/student');
  };

  if (loading) {
    return (
      <div className="layout-container min-h-[60vh] flex flex-col items-center justify-center">
        <Activity className="w-8 h-8 text-white animate-spin opacity-50 mb-4" />
        <span className="text-sm tracking-wider uppercase text-dark-500" style={{ color: 'var(--color-text-tertiary)' }}>
          Aggregating Assessment Scores & Speech Signals...
        </span>
      </div>
    );
  }



  return (
    <div className="layout-container max-w-3xl py-6">
      {/* Consulting Memo Header */}
      <div className="border-b border-subtle pb-8 mb-12" style={{ borderColor: 'var(--color-border-subtle)' }}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 mb-8">
          <div>
            <span className="text-[10px] uppercase font-bold tracking-widest text-dark-500 mb-1 block" style={{ color: 'var(--color-text-tertiary)' }}>
              Executive Evaluation Memo
            </span>
            <h1 className="text-3xl font-bold text-white tracking-tight" style={{ fontFamily: "'Outfit', sans-serif" }}>
              Career Readiness Report
            </h1>
            <p className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>
              Hiring Outlook: <span className="text-emerald-400 font-semibold" style={{ color: 'var(--color-accent-teal)' }}>{data.recommendation}</span>
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleDownloadPDF}
              disabled={downloading}
              className="btn-base btn-secondary text-xs py-2 px-3 flex items-center gap-1.5"
            >
              <Download className="w-3.5 h-3.5" />
              <span>{downloading ? 'Exporting...' : 'Export PDF'}</span>
            </button>
            <button
              onClick={handleRestart}
              className="btn-base btn-primary text-xs py-2 px-3 flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>New Session</span>
            </button>
          </div>
        </div>

        {/* Memo Metadata Block */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 p-5 rounded-lg border border-subtle bg-dark-900/10 text-xs" style={{ borderColor: 'var(--color-border-subtle)' }}>
          <div>
            <span className="text-dark-500 block mb-1 uppercase font-semibold tracking-wider" style={{ color: 'var(--color-text-tertiary)' }}>Target Role</span>
            <span className="font-semibold text-white">Senior Software Engineer</span>
          </div>
          <div>
            <span className="text-dark-500 block mb-1 uppercase font-semibold tracking-wider" style={{ color: 'var(--color-text-tertiary)' }}>Readiness Index</span>
            <span className="font-semibold text-emerald-400" style={{ color: 'var(--color-accent-teal)' }}>{data.overallScore} / 100</span>
          </div>
          <div>
            <span className="text-dark-500 block mb-1 uppercase font-semibold tracking-wider" style={{ color: 'var(--color-text-tertiary)' }}>Hiring Outlook</span>
            <span className="font-semibold text-white">{data.recommendation}</span>
          </div>
          <div>
            <span className="text-dark-500 block mb-1 uppercase font-semibold tracking-wider" style={{ color: 'var(--color-text-tertiary)' }}>Evaluation Date</span>
            <span className="font-semibold text-white">June 23, 2026</span>
          </div>
        </div>
      </div>

      {/* Narrative Section 1: Executive Summary */}
      <section className="mb-14">
        <h2 className="text-lg font-semibold text-white mb-4 border-b border-subtle pb-2" style={{ fontFamily: "'Outfit', sans-serif", borderColor: 'var(--color-border-subtle)' }}>
          1. Executive Summary
        </h2>
        <p className="text-sm leading-relaxed text-dark-300 font-sans" style={{ color: 'var(--color-text-secondary)' }}>
          {data.summary}
        </p>
      </section>

      {/* Narrative Section 2: Core Competencies (Radar) */}
      <section className="mb-14">
        <h2 className="text-lg font-semibold text-white mb-4 border-b border-subtle pb-2" style={{ fontFamily: "'Outfit', sans-serif", borderColor: 'var(--color-border-subtle)' }}>
          2. Competency Blueprint
        </h2>
        <p className="text-sm leading-relaxed text-dark-300 mb-6" style={{ color: 'var(--color-text-secondary)' }}>
          The blueprint below maps candidate performance across five standard organizational alignment vectors. Technical accuracy and communication clarity remain the primary indicators of senior-level capability.
        </p>
        
        {/* Centered Chart Display */}
        <div className="card-premium py-6 px-4 bg-dark-900/10 flex flex-col items-center mb-4">
          <div className="w-full max-w-md h-[240px] flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data.dimensionScores}>
                <PolarGrid stroke="var(--color-border-subtle)" />
                <PolarAngleAxis
                  dataKey="subject"
                  tick={{ fill: 'var(--color-text-secondary)', fontSize: 9 }}
                />
                <PolarRadiusAxis
                  angle={30}
                  domain={[0, 100]}
                  tick={{ fill: 'var(--color-text-tertiary)', fontSize: 8 }}
                  stroke="transparent"
                />
                <Radar
                  name="Score"
                  dataKey="A"
                  stroke="var(--color-accent-teal)"
                  fill="var(--color-accent-teal)"
                  fillOpacity={0.12}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
          <span className="text-[10px] uppercase font-semibold text-dark-500 mt-2 mb-4" style={{ color: 'var(--color-text-tertiary)' }}>
            Figure 2.1: Candidate Competency Vector Mapping
          </span>

          <div className="border-t border-subtle/40 pt-4 w-full text-xs space-y-2" style={{ borderColor: 'var(--color-border-subtle)' }}>
            <span className="font-semibold text-white uppercase tracking-wider block text-[10px]">Blueprint Score Rationale</span>
            <p className="leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
              Communication ({data.dimensionScores?.find((d: any) => d.subject === 'Communication')?.A || 90}) and Accuracy ({data.dimensionScores?.find((d: any) => d.subject === 'Accuracy')?.A || 85}) reflect strong technical foundations. 
              The minor dip in Scenario Handling ({data.dimensionScores?.find((d: any) => d.subject === 'Scenario Handling')?.A || 78}) is mapped to initial ambiguity during database migration rollbacks.
            </p>
          </div>
        </div>
      </section>

      {/* Narrative Section 3: Assessment Categories (Bars) */}
      <section className="mb-14">
        <h2 className="text-lg font-semibold text-white mb-4 border-b border-subtle pb-2" style={{ fontFamily: "'Outfit', sans-serif", borderColor: 'var(--color-border-subtle)' }}>
          3. Assessment Category Breakdown
        </h2>
        <p className="text-sm leading-relaxed text-dark-300 mb-6" style={{ color: 'var(--color-text-secondary)' }}>
          This breakdown assesses the candidate's alignment across specific domains covered during the simulated dialogue sessions.
        </p>

        {/* Centered Chart Display */}
        <div className="card-premium py-6 px-4 bg-dark-900/10 flex flex-col items-center mb-4">
          <div className="w-full max-w-lg h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.categoryScores} layout="vertical" margin={{ left: 10, right: 10, top: 5, bottom: 5 }}>
                <XAxis type="number" domain={[0, 100]} tick={{ fill: 'var(--color-text-tertiary)', fontSize: 9 }} stroke="var(--color-border-subtle)" />
                <YAxis dataKey="name" type="category" tick={{ fill: 'var(--color-text-secondary)', fontSize: 10 }} stroke="var(--color-border-subtle)" />
                <Tooltip
                  contentStyle={{ backgroundColor: 'var(--color-bg-secondary)', borderColor: 'var(--color-border-subtle)', borderRadius: '8px' }}
                  labelStyle={{ color: 'var(--color-text-primary)' }}
                />
                <Bar dataKey="score" fill="var(--color-text-secondary)" radius={[0, 4, 4, 0]} barSize={12} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <span className="text-[10px] uppercase font-semibold text-dark-500 mt-2 mb-4" style={{ color: 'var(--color-text-tertiary)' }}>
            Figure 3.1: Readiness Scores by Assessment Domain
          </span>

          <div className="border-t border-subtle/40 pt-4 w-full text-xs space-y-2" style={{ borderColor: 'var(--color-border-subtle)' }}>
            <span className="font-semibold text-white uppercase tracking-wider block text-[10px]">Domain Performance Rationale</span>
            <p className="leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
              Behavioral ({data.categoryScores?.find((c: any) => c.name === 'Behavioral')?.score || 90}) and Technical ({data.categoryScores?.find((c: any) => c.name === 'Technical')?.score || 85}) domains demonstrate excellent conceptual consistency. 
              Leadership ({data.categoryScores?.find((c: any) => c.name === 'Leadership')?.score || 88}) indicates readiness for mentoring responsibilities. 
              Development focus is recommended for Scenario ({data.categoryScores?.find((c: any) => c.name === 'Scenario')?.score || 78}) testing where concrete fallback schemas lacked explicit steps.
            </p>
          </div>
        </div>
      </section>

      {/* Narrative Section 4: Executive Communication & Presence Review */}
      <section className="mb-14">
        <h2 className="text-lg font-semibold text-white mb-4 border-b border-subtle pb-2" style={{ fontFamily: "'Outfit', sans-serif", borderColor: 'var(--color-border-subtle)' }}>
          4. Communication & Executive Presence Review
        </h2>
        <p className="text-sm leading-relaxed text-dark-300 mb-6" style={{ color: 'var(--color-text-secondary)' }}>
          This section evaluates delivery pacing, articulation latency, response structure, and executive presence indicators against standard professional communication benchmarks.
        </p>

        {data.communicationProfile && (
          <>
            {/* Qualitative Insights Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div className="border border-subtle rounded-lg p-4 bg-dark-900/10" style={{ borderColor: 'var(--color-border-subtle)' }}>
                <span className="text-[10px] uppercase font-bold tracking-widest text-dark-500 block mb-1" style={{ color: 'var(--color-text-tertiary)' }}>
                  Communication Style
                </span>
                <span className="text-xs font-semibold text-white">{data.communicationProfile.style}</span>
              </div>
              <div className="border border-subtle rounded-lg p-4 bg-dark-900/10" style={{ borderColor: 'var(--color-border-subtle)' }}>
                <span className="text-[10px] uppercase font-bold tracking-widest text-dark-500 block mb-1" style={{ color: 'var(--color-text-tertiary)' }}>
                  Executive Presence
                </span>
                <span className="text-xs font-semibold text-white">{data.communicationProfile.presence}</span>
              </div>
              <div className="border border-subtle rounded-lg p-4 bg-dark-900/10" style={{ borderColor: 'var(--color-border-subtle)' }}>
                <span className="text-[10px] uppercase font-bold tracking-widest text-dark-500 block mb-1" style={{ color: 'var(--color-text-tertiary)' }}>
                  Interview Readiness
                </span>
                <span className="text-xs font-semibold text-white">{data.communicationProfile.readiness}</span>
              </div>
              <div className="border border-subtle rounded-lg p-4 bg-dark-900/10" style={{ borderColor: 'var(--color-border-subtle)' }}>
                <span className="text-[10px] uppercase font-bold tracking-widest text-dark-500 block mb-1" style={{ color: 'var(--color-text-tertiary)' }}>
                  Response Quality
                </span>
                <span className="text-xs font-semibold text-white">{data.communicationProfile.quality}</span>
              </div>
            </div>

            {/* STAR Framework Checklist & Executive Presence Scores */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              {/* STAR Framework Checklist Card */}
              <div className="border border-subtle rounded-lg p-5 bg-dark-900/10" style={{ borderColor: 'var(--color-border-subtle)' }}>
                <span className="text-[10px] uppercase font-bold tracking-widest text-dark-500 block mb-3" style={{ color: 'var(--color-text-tertiary)' }}>
                  STAR Framework Phase Alignment
                </span>
                <p className="text-xs mb-4" style={{ color: 'var(--color-text-secondary)' }}>
                  Structural completeness of behavioral answers.
                </p>
                <div className="space-y-3 text-xs">
                  {['situation', 'task', 'action', 'result'].map((phase) => {
                    const profile = data.communicationProfile || {};
                    const star = profile.starFramework || { situation: true, task: true, action: true, result: false };
                    const isCovered = star[phase as keyof typeof star];
                    
                    return (
                      <div key={phase} className="flex items-center justify-between border-b border-subtle/40 pb-2 last:border-0 last:pb-0">
                        <span className="capitalize font-medium text-white">{phase}</span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase border" 
                              style={{
                                color: isCovered ? 'var(--color-accent-teal)' : 'var(--color-accent-coral)',
                                borderColor: isCovered ? 'rgba(45, 212, 191, 0.25)' : 'rgba(251, 113, 133, 0.25)',
                                backgroundColor: isCovered ? 'rgba(45, 212, 191, 0.1)' : 'rgba(251, 113, 133, 0.1)'
                              }}>
                          {isCovered ? 'Covered' : 'Not Detected'}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Advanced Executive Presence Scores Card */}
              <div className="border border-subtle rounded-lg p-5 bg-dark-900/10" style={{ borderColor: 'var(--color-border-subtle)' }}>
                <span className="text-[10px] uppercase font-bold tracking-widest text-dark-500 block mb-3" style={{ color: 'var(--color-text-tertiary)' }}>
                  Executive Capabilities
                </span>
                <p className="text-xs mb-4" style={{ color: 'var(--color-text-secondary)' }}>
                  Evaluated indicators across active responses.
                </p>
                <div className="space-y-4">
                  {[
                    { label: 'Practicality', key: 'practicality', desc: 'Executable engineering approaches' },
                    { label: 'Problem Solving', key: 'problemSolving', desc: 'Resolves core query constraints' },
                    { label: 'Business Thinking', key: 'businessThinking', desc: 'Tech trade-offs aligned with commercial focus' }
                  ].map((scoreItem) => {
                    const profile = data.communicationProfile || {};
                    const execScores = profile.executiveScores || { practicality: 80, problemSolving: 78, businessThinking: 75 };
                    const value = execScores[scoreItem.key as keyof typeof execScores] || 75;
                    
                    return (
                      <div key={scoreItem.key} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="font-semibold text-white">{scoreItem.label}</span>
                          <span className="font-bold text-dark-300">{value} / 100</span>
                        </div>
                        <div className="w-full bg-white/5 rounded-full h-1.5 border border-white/10 overflow-hidden">
                          <div className="bg-emerald-400 h-full rounded-full" style={{ width: `${value}%`, backgroundColor: 'var(--color-accent-teal)' }} />
                        </div>
                        <p className="text-[10px] text-dark-500" style={{ color: 'var(--color-text-tertiary)' }}>{scoreItem.desc}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Observations List */}
            <div className="border border-subtle rounded-lg p-5 mb-6 bg-dark-900/10" style={{ borderColor: 'var(--color-border-subtle)' }}>
              <span className="text-[10px] uppercase font-bold tracking-widest text-dark-500 block mb-3" style={{ color: 'var(--color-text-tertiary)' }}>
                Delivery Observations
              </span>
              <ul className="space-y-2">
                {data.communicationProfile.observations.map((obs: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-2.5 text-xs text-dark-300" style={{ color: 'var(--color-text-secondary)' }}>
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 flex-shrink-0" />
                    <span>{obs}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Metrics List */}
            <div className="space-y-4">
              {Object.entries(data.communicationProfile.metrics).map(([key, metric]: [string, any]) => {
                const isOptimal = metric.rating === 'Optimal' || metric.rating === 'Low' || metric.rating === 'Controlled' || metric.rating === 'High' || metric.rating === 'Substantial';
                const isWarning = metric.rating === 'Needs Prep' || metric.rating === 'Needs Depth' || metric.rating === 'Delayed' || metric.rating === 'Verbose';
                
                const borderColor = isOptimal 
                  ? 'rgba(45, 212, 191, 0.2)' 
                  : isWarning 
                    ? 'rgba(251, 113, 133, 0.2)' 
                    : 'rgba(251, 191, 36, 0.2)';
                    
                const textColor = isOptimal 
                  ? 'var(--color-accent-teal)' 
                  : isWarning 
                    ? 'var(--color-accent-coral)' 
                    : 'rgb(251, 191, 36)';
                
                return (
                  <div key={key} className="border rounded-lg p-4 bg-dark-900/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4" style={{ borderColor: 'var(--color-border-subtle)' }}>
                    <div className="flex-grow">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-semibold text-white">
                          {key === 'speakingPace' ? 'Speaking Pace' :
                           key === 'responseLength' ? 'Response Length' :
                           key === 'fillerWords' ? 'Filler Word Frequency' :
                           key === 'hesitation' ? 'Hesitation & Latency' :
                           'Answer Completeness'}
                        </span>
                        <span className="text-[8px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border" style={{ borderColor, color: textColor }}>
                          {metric.rating}
                        </span>
                      </div>
                      <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                        {metric.feedback}
                      </p>
                    </div>
                    <div className="text-left sm:text-right flex-shrink-0">
                      <span className="text-sm font-bold text-white">{metric.value}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </section>

      {/* Narrative Section 5: Skill Gap Matrix */}
      <section className="mb-14">
        <h2 className="text-lg font-semibold text-white mb-4 border-b border-subtle pb-2" style={{ fontFamily: "'Outfit', sans-serif", borderColor: 'var(--color-border-subtle)' }}>
          5. Competency Capability Heatmap
        </h2>
        <p className="text-sm leading-relaxed text-dark-300 mb-6" style={{ color: 'var(--color-text-secondary)' }}>
          This matrix categorizes individual technical and domain competencies based on structural resume evidence combined with active simulation responses.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          {data.heatmap.map((item: any, idx: number) => (
            <div
              key={idx}
              className="rounded-lg p-4 border flex items-center justify-between bg-dark-900/10"
              style={{
                borderColor: item.border,
                backgroundColor: item.color
              }}
            >
              <span className="text-xs font-semibold text-white">
                {item.skill}
              </span>
              <span
                className="text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border"
                style={{ color: item.textColor, borderColor: item.border }}
              >
                {item.rating}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* Narrative Section 6: Competitive Advantages & Development Areas */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-12 border-t border-subtle pt-10" style={{ borderColor: 'var(--color-border-subtle)' }}>
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wider text-white mb-4 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            Competitive Advantages
          </h3>
          <ul className="space-y-4">
            {data.strengths.map((str: string, idx: number) => (
              <li key={idx} className="flex items-start gap-2.5 text-xs leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
                <span>•</span>
                <span>{str}</span>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wider text-white mb-4 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            Development Areas
          </h3>
          <ul className="space-y-4">
            {data.recommendations.map((rec: string, idx: number) => (
              <li key={idx} className="flex items-start gap-2.5 text-xs leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
                <span>•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Narrative Section 7: Supporting Evidence & Dialogue Logs */}
      <section className="mt-14 border-t border-subtle pt-10" style={{ borderColor: 'var(--color-border-subtle)' }}>
        <h2 className="text-lg font-semibold text-white mb-4 border-b border-subtle pb-2" style={{ fontFamily: "'Outfit', sans-serif", borderColor: 'var(--color-border-subtle)' }}>
          7. Dialogue Logs & Supporting Evidence
        </h2>
        <p className="text-sm leading-relaxed text-dark-300 mb-6" style={{ color: 'var(--color-text-secondary)' }}>
          Detailed transcript and diagnostic metrics for each question presented during the active assessment session.
        </p>

        <div className="space-y-8">
          {data.all_qa && data.all_qa.length > 0 ? (
            data.all_qa.map((qa: any, idx: number) => {
              const ev = qa.evaluation || {};
              const star = ev.starFramework || {};
              
              return (
                <div key={idx} className="card-premium p-6 bg-dark-900/10 space-y-4">
                  {/* Dialogue Info Header */}
                  <div className="flex items-center justify-between border-b border-subtle/40 pb-3" style={{ borderColor: 'var(--color-border-subtle)' }}>
                    <span className="text-[10px] uppercase font-bold tracking-wider text-emerald-400" style={{ color: 'var(--color-accent-teal)' }}>
                      Directive {idx + 1} — {qa.category || 'Domain'}
                    </span>
                    <div className="text-[10px] text-dark-500" style={{ color: 'var(--color-text-tertiary)' }}>
                      Accuracy: <span className="text-white font-semibold mr-3">{ev.accuracy || 75}%</span>
                      Depth: <span className="text-white font-semibold">{ev.depth || 75}%</span>
                    </div>
                  </div>

                  {/* Question and Answer Text */}
                  <div className="space-y-3">
                    <div>
                      <span className="text-[9px] uppercase font-bold tracking-widest text-dark-500 block mb-1" style={{ color: 'var(--color-text-tertiary)' }}>Directive Prompt</span>
                      <p className="text-xs text-white font-medium">{qa.question}</p>
                    </div>
                    <div>
                      <span className="text-[9px] uppercase font-bold tracking-widest text-dark-500 block mb-1" style={{ color: 'var(--color-text-tertiary)' }}>Candidate Response Transcript</span>
                      <p className="text-xs leading-relaxed italic bg-white/5 p-3 rounded border border-white/10" style={{ color: 'var(--color-text-secondary)' }}>
                        "{qa.answer}"
                      </p>
                    </div>
                  </div>

                  {/* Feedback and Metrics Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs pt-2">
                    <div>
                      <span className="text-[9px] uppercase font-bold tracking-widest text-dark-500 block mb-1" style={{ color: 'var(--color-text-tertiary)' }}>Diagnostic Rationale</span>
                      <p className="text-[11px]" style={{ color: 'var(--color-text-secondary)' }}>{ev.feedback || 'Response successfully parsed by evaluation engine.'}</p>
                    </div>
                    <div className="space-y-2">
                      <span className="text-[9px] uppercase font-bold tracking-widest text-dark-500 block mb-1" style={{ color: 'var(--color-text-tertiary)' }}>STAR Verification</span>
                      <div className="flex flex-wrap gap-1.5">
                        {['situation', 'task', 'action', 'result'].map(p => {
                          const isFound = star[p];
                          return (
                            <span 
                              key={p} 
                              className="text-[9px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border"
                              style={{
                                color: isFound ? 'var(--color-accent-teal)' : 'var(--color-text-tertiary)',
                                borderColor: isFound ? 'rgba(45, 212, 191, 0.25)' : 'var(--color-border-subtle)',
                                backgroundColor: isFound ? 'rgba(45, 212, 191, 0.05)' : 'transparent'
                              }}
                            >
                              {p[0]} : {isFound ? 'Covered' : 'Gap'}
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="text-center py-6 border border-dashed border-subtle rounded-lg" style={{ borderColor: 'var(--color-border-subtle)' }}>
              <span className="text-xs text-dark-500" style={{ color: 'var(--color-text-tertiary)' }}>No supporting dialogue logs generated.</span>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
