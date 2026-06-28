import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  ArrowRight,
  BriefcaseBusiness,
  Building2,
  CheckCircle2,
  ClipboardCheck,
  FileText,
  Loader2,
  Pencil,
  Sparkles,
  Upload as UploadIcon,
  Users,
} from 'lucide-react';
import { useSession } from '../App';

type Intake = {
  companyName: string;
  industry: string;
  department: string;
  jobTitle: string;
  seniority: string;
  employmentType: string;
  expectedExperience: string;
  hiringTimeline: string;
  mandatorySkills: string;
};

type Blueprint = {
  title?: string;
  role?: string;
  industry?: string;
  seniority?: string;
  experience?: string;
  required_skills?: string[];
  preferred_skills?: string[];
  responsibilities?: string[];
  domain?: string;
  leadership_expectations?: string[];
  communication_expectations?: string[];
};

const intakeQuestions: Array<{
  key: keyof Intake;
  label: string;
  prompt: string;
  placeholder: string;
  options?: string[];
}> = [
  { key: 'companyName', label: 'Company', prompt: 'Which company is this assessment for?', placeholder: 'Example: Northstar Payments' },
  { key: 'industry', label: 'Industry', prompt: 'Which industry should the hiring context reflect?', placeholder: 'Example: Fintech, Healthcare, SaaS' },
  { key: 'department', label: 'Department', prompt: 'Which team owns this role?', placeholder: 'Example: Platform Engineering' },
  { key: 'jobTitle', label: 'Role', prompt: 'What is the exact job title?', placeholder: 'Example: Senior Backend Engineer' },
  { key: 'seniority', label: 'Seniority', prompt: 'What seniority level are you hiring for?', placeholder: 'Select seniority', options: ['Junior', 'Mid-level', 'Senior', 'Staff', 'Lead', 'Manager', 'Director'] },
  { key: 'employmentType', label: 'Employment', prompt: 'What type of employment is this?', placeholder: 'Select employment type', options: ['Full-time', 'Contract', 'Contract-to-hire', 'Part-time', 'Internship'] },
  { key: 'expectedExperience', label: 'Experience', prompt: 'How much experience should qualified candidates have?', placeholder: 'Example: 5+ years building production systems' },
  { key: 'hiringTimeline', label: 'Timeline', prompt: 'What is the hiring timeline?', placeholder: 'Select timeline', options: ['Immediate', '2-4 weeks', '1-2 months', 'This quarter', 'Flexible'] },
  { key: 'mandatorySkills', label: 'Must-haves', prompt: 'Any mandatory skills the JD must preserve?', placeholder: 'Example: Python, Kafka, AWS, PCI-DSS' },
];

const emptyIntake: Intake = {
  companyName: '',
  industry: '',
  department: '',
  jobTitle: '',
  seniority: '',
  employmentType: '',
  expectedExperience: '',
  hiringTimeline: '',
  mandatorySkills: '',
};

const fallbackBlueprint: Blueprint = {
  title: 'Senior Software Engineer',
  industry: 'Financial Technology',
  seniority: 'Senior',
  experience: '5+ years',
  required_skills: ['Python', 'FastAPI', 'Kafka', 'AWS'],
  preferred_skills: ['Kubernetes', 'PostgreSQL'],
  responsibilities: ['Own service architecture', 'Partner with product and security teams'],
  domain: 'Payments',
  leadership_expectations: ['Mentor engineers', 'Lead design reviews'],
  communication_expectations: ['Explain trade-offs clearly', 'Write crisp implementation plans'],
};

export default function Upload() {
  const navigate = useNavigate();
  const { setResumeId, setJdId, setInterviewId } = useSession();

  const [stage, setStage] = useState(-1);
  const [intake, setIntake] = useState<Intake>(emptyIntake);
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jdIdLocal, setJdIdLocal] = useState<string | null>(null);
  const [resumeIdLocal, setResumeIdLocal] = useState<string | null>(null);
  const [blueprint, setBlueprint] = useState<Blueprint>(fallbackBlueprint);
  const [resumeSummary, setResumeSummary] = useState<any>(null);
  const [matchAnalysis, setMatchAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  const currentQuestion = intakeQuestions[stage];
  const intakeComplete = stage >= intakeQuestions.length;
  const totalStages = 12;
  const progress = Math.min(100, Math.round(((stage + 2) / totalStages) * 100));

  const assessmentBlueprint = useMemo(() => {
    if (matchAnalysis?.assessmentBlueprint) return matchAnalysis.assessmentBlueprint;

    return {
      modules: [
        { name: 'Resume Validation', questions: 2, focus: 'Verify claimed ownership and project evidence.' },
        { name: 'Technical Questions', questions: 3, focus: 'Probe required skills and core delivery depth.' },
        { name: 'Scenario Questions', questions: 2, focus: 'Evaluate applied judgment in realistic role constraints.' },
        { name: 'Behavioral Questions', questions: 2, focus: 'Assess collaboration, accountability, and operating style.' },
        { name: 'Leadership Questions', questions: blueprint.seniority?.toLowerCase().includes('senior') ? 2 : 1, focus: 'Validate mentoring and stakeholder communication.' },
      ],
      estimatedDurationMinutes: 40,
      priorityGaps: matchAnalysis?.missing_skills || [],
    };
  }, [blueprint.seniority, matchAnalysis]);

  const updateIntake = (value: string) => {
    if (!currentQuestion) return;
    setIntake((prev) => ({ ...prev, [currentQuestion.key]: value }));
  };

  const currentValue = currentQuestion ? intake[currentQuestion.key] : '';

  const nextFromIntake = () => {
    setError('');
    if (stage >= 0 && currentQuestion && !currentValue.trim() && currentQuestion.key !== 'mandatorySkills') {
      setError('This field is required to create the assessment profile.');
      return;
    }
    setStage((prev) => prev + 1);
  };

  const applyIntakeToBlueprint = (parsed: Blueprint): Blueprint => {
    const mandatorySkills = intake.mandatorySkills
      .split(',')
      .map((skill) => skill.trim())
      .filter(Boolean);
    const required = Array.from(new Set([...(parsed.required_skills || []), ...mandatorySkills]));

    return {
      ...parsed,
      title: parsed.title || parsed.role || intake.jobTitle,
      industry: parsed.industry || intake.industry,
      seniority: parsed.seniority || intake.seniority,
      experience: parsed.experience || intake.expectedExperience,
      required_skills: required,
    };
  };

  const uploadJd = async () => {
    if (!jdFile) {
      setError('Upload a job description before running the JD Agent.');
      return;
    }

    setLoading(true);
    setError('');
    setStatus('JD Agent is extracting role requirements...');
    try {
      const formData = new FormData();
      formData.append('file', jdFile);
      const res = await axios.post('/api/jd/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const parsed = applyIntakeToBlueprint(res.data.parsed || fallbackBlueprint);
      setBlueprint(parsed);
      setJdIdLocal(res.data.id);
      setJdId(res.data.id);
      setStage(10);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'JD Agent could not parse this file. Try a PDF, TXT, or Markdown job description.');
    } finally {
      setLoading(false);
      setStatus('');
    }
  };

  const saveBlueprint = async () => {
    setLoading(true);
    setError('');
    setStatus('Saving recruiter-approved hiring blueprint...');
    try {
      if (jdIdLocal) {
        await axios.put(`/api/jd/${jdIdLocal}/blueprint`, { blueprint });
      }
      setStage(11);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Could not save the hiring blueprint.');
    } finally {
      setLoading(false);
      setStatus('');
    }
  };

  const uploadResume = async () => {
    if (!resumeFile) {
      setError('Upload a candidate resume before running the Resume Agent.');
      return;
    }

    setLoading(true);
    setError('');
    setStatus('Resume Agent is extracting candidate evidence...');
    try {
      const formData = new FormData();
      formData.append('file', resumeFile);
      const res = await axios.post('/api/resume', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResumeIdLocal(res.data.id);
      setResumeId(res.data.id);
      setResumeSummary(res.data.parsed);
      setStage(12);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Resume Agent could not parse this PDF.');
    } finally {
      setLoading(false);
      setStatus('');
    }
  };

  const runMatch = async () => {
    if (!resumeIdLocal || !jdIdLocal) return;
    setLoading(true);
    setError('');
    setStatus('Computing deterministic match analysis...');
    try {
      const res = await axios.post('/api/match', {
        resume_id: resumeIdLocal,
        jd_id: jdIdLocal,
      });
      setMatchAnalysis(res.data);
      setStage(13);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Could not compute match analysis.');
    } finally {
      setLoading(false);
      setStatus('');
    }
  };

  const startInterview = async () => {
    if (!resumeIdLocal || !jdIdLocal) return;
    setLoading(true);
    setError('');
    setStatus('Preparing interview session...');
    try {
      const res = await axios.post('/api/interview/start', {
        resume_id: resumeIdLocal,
        jd_id: jdIdLocal,
      });
      setInterviewId(res.data.id || res.data.interview_id);
      navigate('/interview');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Could not start the interview session.');
    } finally {
      setLoading(false);
      setStatus('');
    }
  };

  const setListField = (key: keyof Blueprint, value: string) => {
    setBlueprint((prev) => ({
      ...prev,
      [key]: value.split(',').map((item) => item.trim()).filter(Boolean),
    }));
  };

  return (
    <div className="layout-container max-w-6xl">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <aside className="lg:col-span-3">
          <div className="card-premium sticky top-28">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-blue-600/10 border border-blue-500/20 flex items-center justify-center">
                <BriefcaseBusiness className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-theme-primary">Create Assessment</h2>
                <p className="text-[10px] text-theme-tertiary">Recruiter setup workflow</p>
              </div>
            </div>

            <div className="h-2 rounded-full overflow-hidden mb-6" style={{ backgroundColor: 'var(--color-bg-tertiary)' }}>
              <div className="h-full bg-blue-600 transition-all" style={{ width: `${progress}%` }} />
            </div>

            <StepList activeStage={stage} />
          </div>
        </aside>

        <section className="lg:col-span-9">
          <AnimatePresence mode="wait">
            <motion.div
              key={stage}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.2 }}
            >
              {stage === -1 && (
                <Panel
                  eyebrow="Enterprise Recruiter Workspace"
                  title="Create a new assessment"
                  description="Start with role context first. The system will convert recruiter intent and job description evidence into a reviewable hiring blueprint before any candidate is screened."
                  icon={<Building2 className="w-6 h-6" />}
                >
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                    {[
                      ['Intake Assistant', 'Guided setup captures business context.'],
                      ['Agent Analysis', 'JD and resume evidence becomes structured data.'],
                      ['Transparent Match', 'Backend code computes fit from structured skills.'],
                    ].map(([title, desc]) => (
                      <div key={title} className="rounded-lg border border-subtle p-4" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
                        <span className="text-xs font-bold text-theme-primary block mb-1">{title}</span>
                        <p className="text-[11px] text-theme-secondary">{desc}</p>
                      </div>
                    ))}
                  </div>
                  <button onClick={() => setStage(0)} className="btn-base btn-primary px-6 py-3 gap-2">
                    <span>Launch Intake Assistant</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </Panel>
              )}

              {stage >= 0 && stage < intakeQuestions.length && currentQuestion && (
                <Panel
                  eyebrow={`AI Recruiter Intake Assistant / ${stage + 1} of ${intakeQuestions.length}`}
                  title={currentQuestion.prompt}
                  description="Answer one decision at a time. These details anchor the generated hiring blueprint so the JD parser does not lose recruiter intent."
                  icon={<Sparkles className="w-6 h-6" />}
                >
                  <div className="max-w-2xl">
                    <label className="text-xs font-bold uppercase tracking-widest text-theme-tertiary block mb-3">
                      {currentQuestion.label}
                    </label>
                    {currentQuestion.options ? (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {currentQuestion.options.map((option) => (
                          <button
                            key={option}
                            type="button"
                            onClick={() => updateIntake(option)}
                            className="text-left rounded-lg border px-4 py-3 text-sm font-semibold transition"
                            style={{
                              borderColor: currentValue === option ? 'var(--color-accent)' : 'var(--color-border-subtle)',
                              backgroundColor: currentValue === option ? 'rgba(37, 99, 235, 0.12)' : 'var(--color-bg-primary)',
                              color: 'var(--color-text-primary)',
                            }}
                          >
                            {option}
                          </button>
                        ))}
                      </div>
                    ) : (
                      <input
                        value={currentValue}
                        onChange={(event) => updateIntake(event.target.value)}
                        className="input-base text-base py-4"
                        placeholder={currentQuestion.placeholder}
                        autoFocus
                      />
                    )}
                  </div>
                  <FooterActions
                    backLabel={stage === 0 ? 'Back to assessment' : 'Previous'}
                    onBack={() => setStage((prev) => prev - 1)}
                    primaryLabel={stage === intakeQuestions.length - 1 ? 'Continue to JD Upload' : 'Continue'}
                    onPrimary={nextFromIntake}
                    error={error}
                  />
                </Panel>
              )}

              {intakeComplete && stage === 9 && (
                <Panel
                  eyebrow="Upload Job Description"
                  title="Run the JD Agent against the role document"
                  description="Upload a PDF, TXT, or Markdown job description. The agent will extract structured hiring requirements into an editable blueprint."
                  icon={<FileText className="w-6 h-6" />}
                >
                  <FileDrop file={jdFile} onFile={setJdFile} label="Job Description" accept=".pdf,.txt,.md" />
                  <FooterActions
                    onBack={() => setStage(8)}
                    primaryLabel="Analyze JD"
                    onPrimary={uploadJd}
                    loading={loading}
                    loadingLabel={status}
                    error={error}
                  />
                </Panel>
              )}

              {stage === 10 && (
                <Panel
                  eyebrow="JD Agent Analysis"
                  title="Review and edit the Hiring Blueprint"
                  description="This is the recruiter-approved operating definition for the role. Update anything the JD agent missed before screening the candidate."
                  icon={<Pencil className="w-6 h-6" />}
                >
                  <BlueprintEditor blueprint={blueprint} setBlueprint={setBlueprint} setListField={setListField} intake={intake} />
                  <FooterActions
                    onBack={() => setStage(9)}
                    primaryLabel="Approve Blueprint"
                    onPrimary={saveBlueprint}
                    loading={loading}
                    loadingLabel={status}
                    error={error}
                  />
                </Panel>
              )}

              {stage === 11 && (
                <Panel
                  eyebrow="Blueprint Created & Published"
                  title="Your assessment is ready!"
                  description="A structured hiring blueprint has been created for this role. Share the invitation link below with your candidates to screen them."
                  icon={<CheckCircle2 className="w-6 h-6" />}
                >
                  <div className="space-y-6">
                    <div className="rounded-lg border border-subtle p-5 bg-blue-600/10 border-blue-500/20">
                      <span className="text-[10px] uppercase tracking-widest font-bold text-blue-400 block mb-2">Shareable Candidate Invitation URL</span>
                      <div className="flex flex-col sm:flex-row items-stretch gap-2">
                        <input
                          readOnly
                          className="input-base !bg-dark-900/40 text-xs flex-grow"
                          value={`${window.location.protocol}//${window.location.host}/assessment/take/${jdIdLocal}`}
                        />
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(`${window.location.protocol}//${window.location.host}/assessment/take/${jdIdLocal}`);
                            alert('Link copied to clipboard!');
                          }}
                          className="btn-base btn-primary text-xs py-2 px-4 justify-center"
                        >
                          Copy Link
                        </button>
                      </div>
                      <p className="text-[11px] text-theme-secondary mt-2">
                        Candidates will upload their resumes, run fit analysis, and complete the adaptive interview under this specific job context.
                      </p>
                    </div>

                    <div className="rounded-lg border border-subtle p-5" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
                      <span className="text-[10px] uppercase tracking-widest font-bold text-theme-tertiary block mb-3">Assessment Role Blueprint Details</span>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                        <div>
                          <span className="font-semibold text-theme-tertiary block">Position</span>
                          <span className="text-white">{blueprint.title}</span>
                        </div>
                        <div>
                          <span className="font-semibold text-theme-tertiary block">Seniority</span>
                          <span className="text-white">{blueprint.seniority}</span>
                        </div>
                        <div>
                          <span className="font-semibold text-theme-tertiary block">Industry</span>
                          <span className="text-white">{blueprint.industry}</span>
                        </div>
                        <div>
                          <span className="font-semibold text-theme-tertiary block">Estimated Duration</span>
                          <span className="text-white">40 Minutes</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="pt-8 mt-8 border-t border-subtle flex justify-end">
                    <button
                      onClick={() => navigate('/recruiter')}
                      className="btn-base btn-primary px-6 gap-2"
                    >
                      <span>Return to Recruiter Dashboard</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </Panel>
              )}
            </motion.div>
          </AnimatePresence>
        </section>
      </div>
    </div>
  );
}

function Panel({
  eyebrow,
  title,
  description,
  icon,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="card-premium p-8 md:p-10">
      <div className="flex items-start gap-4 mb-8">
        <div className="w-12 h-12 rounded-xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400 flex-shrink-0">
          {icon}
        </div>
        <div>
          <span className="text-[10px] uppercase tracking-widest font-bold text-theme-tertiary block mb-2">{eyebrow}</span>
          <h1 className="text-3xl font-bold text-theme-primary tracking-tight mb-2">{title}</h1>
          <p className="text-sm max-w-2xl text-theme-secondary">{description}</p>
        </div>
      </div>
      {children}
    </div>
  );
}

function FooterActions({
  onBack,
  onPrimary,
  primaryLabel,
  backLabel = 'Back',
  loading,
  loadingLabel,
  error,
}: {
  onBack?: () => void;
  onPrimary: () => void;
  primaryLabel: string;
  backLabel?: string;
  loading?: boolean;
  loadingLabel?: string;
  error?: string;
}) {
  return (
    <div className="pt-8 mt-8 border-t border-subtle">
      {error && (
        <div className="mb-4 rounded-lg border px-4 py-3 text-sm" style={{ borderColor: 'rgba(244, 63, 94, 0.3)', backgroundColor: 'rgba(244, 63, 94, 0.08)', color: 'var(--color-accent-coral)' }}>
          {error}
        </div>
      )}
      <div className="flex flex-col sm:flex-row justify-between gap-3">
        {onBack ? (
          <button onClick={onBack} className="btn-base btn-secondary gap-2" disabled={loading}>
            <ArrowLeft className="w-4 h-4" />
            <span>{backLabel}</span>
          </button>
        ) : <span />}
        <button onClick={onPrimary} className="btn-base btn-primary px-6 gap-2" disabled={loading}>
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
          <span>{loading ? loadingLabel || 'Working...' : primaryLabel}</span>
        </button>
      </div>
    </div>
  );
}

function StepList({ activeStage }: { activeStage: number }) {
  const steps = [
    ['Create Assessment', activeStage >= -1],
    ['Recruiter Intake', activeStage >= 0],
    ['JD Agent Analysis', activeStage >= 9],
    ['Hiring Blueprint', activeStage >= 10],
    ['Blueprint Published', activeStage >= 11],
  ];

  return (
    <div className="space-y-3">
      {steps.map(([label, active]) => (
        <div key={String(label)} className="flex items-center gap-3">
          <div className="w-5 h-5 rounded-full border flex items-center justify-center" style={{ borderColor: active ? 'var(--color-accent)' : 'var(--color-border-subtle)', backgroundColor: active ? 'rgba(37, 99, 235, 0.16)' : 'transparent' }}>
            {active && <CheckCircle2 className="w-3.5 h-3.5 text-blue-400" />}
          </div>
          <span className="text-xs font-semibold" style={{ color: active ? 'var(--color-text-primary)' : 'var(--color-text-tertiary)' }}>
            {String(label)}
          </span>
        </div>
      ))}
    </div>
  );
}

function FileDrop({ file, onFile, label, accept }: { file: File | null; onFile: (file: File | null) => void; label: string; accept: string }) {
  return (
    <div className="rounded-xl border border-dashed p-8 text-center" style={{ borderColor: 'var(--color-border-hover)', backgroundColor: 'var(--color-bg-primary)' }}>
      <input
        id={`file-${label}`}
        type="file"
        className="hidden"
        accept={accept}
        onChange={(event) => onFile(event.target.files?.[0] || null)}
      />
      <label htmlFor={`file-${label}`} className="cursor-pointer flex flex-col items-center">
        <div className="w-12 h-12 rounded-xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center mb-4">
          <UploadIcon className="w-5 h-5 text-blue-400" />
        </div>
        <span className="text-sm font-bold text-theme-primary">{file ? file.name : `Upload ${label}`}</span>
        <span className="text-xs text-theme-tertiary mt-1">{file ? `${(file.size / (1024 * 1024)).toFixed(2)} MB` : `Accepted: ${accept}`}</span>
      </label>
    </div>
  );
}

function BlueprintEditor({
  blueprint,
  setBlueprint,
  setListField,
  intake,
}: {
  blueprint: Blueprint;
  setBlueprint: React.Dispatch<React.SetStateAction<Blueprint>>;
  setListField: (key: keyof Blueprint, value: string) => void;
  intake: Intake;
}) {
  const [listDrafts, setListDrafts] = useState<Record<string, string>>(() => ({
    required_skills: (blueprint.required_skills || []).join(', '),
    preferred_skills: (blueprint.preferred_skills || []).join(', '),
    responsibilities: (blueprint.responsibilities || []).join(', '),
    leadership_expectations: (blueprint.leadership_expectations || []).join(', '),
    communication_expectations: (blueprint.communication_expectations || []).join(', '),
  }));

  const textField = (key: keyof Blueprint, label: string, fallback = '') => (
    <div>
      <label className="text-[10px] uppercase tracking-widest font-bold text-theme-tertiary block mb-2">{label}</label>
      <input
        className="input-base"
        value={String(blueprint[key] || fallback)}
        onChange={(event) => setBlueprint((prev) => ({ ...prev, [key]: event.target.value }))}
      />
    </div>
  );

  const listField = (key: keyof Blueprint, label: string) => (
    <div>
      <label className="text-[10px] uppercase tracking-widest font-bold text-theme-tertiary block mb-2">{label}</label>
      <textarea
        className="input-base min-h-[92px]"
        value={listDrafts[String(key)] ?? ''}
        onChange={(event) => setListDrafts((prev) => ({ ...prev, [String(key)]: event.target.value }))}
        onBlur={(event) => setListField(key, event.target.value)}
        placeholder="Comma-separated values"
      />
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-subtle p-4" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
        <span className="text-[10px] uppercase tracking-widest font-bold text-theme-tertiary block mb-3">Recruiter Intake Context</span>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
          <Info label="Company" value={intake.companyName} />
          <Info label="Department" value={intake.department} />
          <Info label="Employment" value={intake.employmentType} />
          <Info label="Timeline" value={intake.hiringTimeline} />
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {textField('title', 'Role', intake.jobTitle)}
        {textField('industry', 'Industry', intake.industry)}
        {textField('experience', 'Experience', intake.expectedExperience)}
        {textField('domain', 'Domain')}
        {textField('seniority', 'Seniority', intake.seniority)}
        {listField('required_skills', 'Required Skills')}
        {listField('preferred_skills', 'Preferred Skills')}
        {listField('responsibilities', 'Responsibilities')}
        {listField('leadership_expectations', 'Leadership Expectations')}
        {listField('communication_expectations', 'Communication Expectations')}
      </div>
    </div>
  );
}

function ResumeSummary({ summary }: { summary: any }) {
  if (!summary) {
    return <p className="text-sm text-theme-secondary">No summary data available.</p>;
  }

  const links = [
    summary.linkedin && { label: 'LinkedIn', url: summary.linkedin },
    summary.github && { label: 'GitHub', url: summary.github },
    summary.portfolio && { label: 'Portfolio', url: summary.portfolio },
    summary.website && { label: 'Website', url: summary.website },
  ].filter(Boolean) as Array<{ label: string; url: string }>;

  return (
    <div className="space-y-6">
      {/* Basic Info Card */}
      <div className="rounded-lg border border-subtle p-5" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
        <span className="text-[10px] uppercase tracking-widest font-bold text-theme-tertiary block mb-2">Candidate Info</span>
        <h3 className="text-lg font-bold text-theme-primary">{summary.candidate_name || 'Name not found'}</h3>
        {summary.headline && <p className="text-sm text-theme-secondary font-medium mt-0.5">{summary.headline}</p>}
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 text-xs text-theme-secondary">
          {summary.email && (
            <div>
              <span className="font-semibold text-theme-tertiary block">Email</span>
              <span>{summary.email}</span>
            </div>
          )}
          {summary.phone && (
            <div>
              <span className="font-semibold text-theme-tertiary block">Phone</span>
              <span>{summary.phone}</span>
            </div>
          )}
          {summary.location && (
            <div>
              <span className="font-semibold text-theme-tertiary block">Location</span>
              <span>{summary.location}</span>
            </div>
          )}
        </div>

        {links.length > 0 && (
          <div className="mt-4 pt-4 border-t border-subtle flex flex-wrap gap-4 text-xs">
            {links.map((link) => (
              <a
                key={link.url}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:underline font-semibold"
              >
                {link.label}
              </a>
            ))}
          </div>
        )}
      </div>

      {/* Summary Block */}
      {summary.summary && (
        <div className="rounded-lg border border-subtle p-5" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
          <span className="text-[10px] uppercase tracking-widest font-bold text-theme-tertiary block mb-2">Professional Summary</span>
          <p className="text-sm text-theme-secondary leading-relaxed">{summary.summary}</p>
        </div>
      )}

      {/* Skills Group Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <SummaryBlock title="Core Skills" items={summary.skills} />
        {summary.technical_skills?.length > 0 && (
          <SummaryBlock title="Technical Skills" items={summary.technical_skills} />
        )}
        {summary.programming_languages?.length > 0 && (
          <SummaryBlock title="Programming Languages" items={summary.programming_languages} />
        )}
        {summary.frameworks?.length > 0 && (
          <SummaryBlock title="Frameworks" items={summary.frameworks} />
        )}
        {summary.databases?.length > 0 && (
          <SummaryBlock title="Databases" items={summary.databases} />
        )}
        {summary.cloud_platforms?.length > 0 && (
          <SummaryBlock title="Cloud Platforms" items={summary.cloud_platforms} />
        )}
        {summary.tools?.length > 0 && (
          <SummaryBlock title="Tools" items={summary.tools} />
        )}
        {summary.soft_skills?.length > 0 && (
          <SummaryBlock title="Soft Skills" items={summary.soft_skills} />
        )}
        {summary.certifications?.length > 0 && (
          <SummaryBlock title="Certifications" items={summary.certifications} />
        )}
      </div>

      {/* Projects */}
      <div className="rounded-lg border border-subtle p-5" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
        <span className="text-[10px] uppercase tracking-widest font-bold text-theme-tertiary block mb-4">Projects</span>
        {summary.projects?.length > 0 ? (
          <div className="space-y-4">
            {summary.projects.map((project: any, idx: number) => (
              <div key={idx} className="p-4 rounded-md border border-subtle bg-theme-secondary/20">
                <div className="flex justify-between items-start">
                  <h4 className="text-sm font-bold text-theme-primary">{project.title || 'Untitled Project'}</h4>
                  <div className="flex gap-3 text-xs">
                    {project.github && (
                      <a href={project.github} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">
                        GitHub
                      </a>
                    )}
                    {project.demo && (
                      <a href={project.demo} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">
                        Demo
                      </a>
                    )}
                  </div>
                </div>
                {project.description && (
                  <p className="text-xs text-theme-secondary mt-1">{project.description}</p>
                )}
                {project.technologies?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {project.technologies.map((tech: string, i: number) => (
                      <span key={i} className="text-[10px] px-2 py-0.5 rounded border" style={{ color: 'var(--color-text-secondary)', borderColor: 'var(--color-border-subtle)', backgroundColor: 'var(--color-bg-secondary)' }}>
                        {tech}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-theme-tertiary">No projects extracted.</p>
        )}
      </div>

      {/* Experience */}
      <div className="rounded-lg border border-subtle p-5" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
        <span className="text-[10px] uppercase tracking-widest font-bold text-theme-tertiary block mb-4">Work Experience</span>
        {summary.experience?.length > 0 ? (
          <div className="space-y-4">
            {summary.experience.map((exp: any, idx: number) => (
              <div key={idx} className="p-4 rounded-md border border-subtle bg-theme-secondary/20">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="text-sm font-bold text-theme-primary">{exp.title || 'Untitled Role'}</h4>
                    <p className="text-xs text-theme-secondary">{exp.company || 'Unknown Company'} {exp.employment_type ? `• ${exp.employment_type}` : ''}</p>
                  </div>
                  {exp.duration && (
                    <span className="text-xs text-theme-tertiary">{exp.duration}</span>
                  )}
                </div>
                {exp.responsibilities?.length > 0 && (
                  <ul className="list-disc list-inside text-xs text-theme-secondary mt-2 space-y-1">
                    {exp.responsibilities.map((resp: string, i: number) => (
                      <li key={i}>{resp}</li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-theme-tertiary">No experience extracted.</p>
        )}
      </div>
    </div>
  );
}

function MatchSummary({ data }: { data: any }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Metric label="Match" value={`${data.matchScore}%`} />
        <Metric label="Required" value={`${data.calculation?.requiredMatched || 0}/${data.calculation?.requiredTotal || 0}`} />
        <Metric label="Preferred" value={`${data.calculation?.preferredMatched || 0}/${data.calculation?.preferredTotal || 0}`} />
        <Metric label="Method" value="Deterministic" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <SummaryBlock title="Matched Skills" items={data.matched_skills} tone="good" />
        <SummaryBlock title="Missing Skills" items={data.missing_skills} tone="risk" />
        <SummaryBlock title="Additional Skills" items={data.additional_skills} />
      </div>
      <div className="rounded-lg border border-subtle p-5" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
        <span className="text-[10px] uppercase tracking-widest font-bold text-theme-tertiary block mb-4">Calculation Logic</span>
        <p className="text-sm text-theme-secondary">
          Required skills contribute {data.calculation?.requiredWeight || 70}%, preferred skills contribute {data.calculation?.preferredWeight || 20}%, and domain alignment contributes {data.calculation?.domainWeight || 10}%. The backend compares normalized skill sets from JD JSON and resume JSON.
        </p>
      </div>
    </div>
  );
}

function AssessmentBlueprint({ blueprint, matchAnalysis }: { blueprint: any; matchAnalysis: any }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Metric label="Estimated Duration" value={`${blueprint.estimatedDurationMinutes} min`} />
        <Metric label="Priority Gaps" value={`${blueprint.priorityGaps?.length || 0}`} />
        <Metric label="Match Score" value={`${matchAnalysis?.matchScore || 0}%`} />
      </div>
      <div className="space-y-3">
        {(blueprint.modules || []).map((module: any) => (
          <div key={module.name} className="rounded-lg border border-subtle p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
            <div>
              <span className="text-sm font-bold text-theme-primary">{module.name}</span>
              <p className="text-xs text-theme-secondary mt-1">{module.focus}</p>
            </div>
            <span className="text-xs font-bold px-3 py-1 rounded-md border border-blue-500/20 text-blue-400 bg-blue-600/10 flex-shrink-0">
              {module.questions} questions
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function SummaryBlock({ title, items, tone }: { title: string; items?: string[]; tone?: 'good' | 'risk' }) {
  const color = tone === 'good' ? 'var(--color-accent-teal)' : tone === 'risk' ? 'var(--color-accent-coral)' : 'var(--color-text-secondary)';

  return (
    <div className="rounded-lg border border-subtle p-5" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
      <span className="text-[10px] uppercase tracking-widest font-bold text-theme-tertiary block mb-3">{title}</span>
      <div className="flex flex-wrap gap-2">
        {items && items.length ? items.map((item, index) => (
          <span key={`${item}-${index}`} className="text-xs px-2.5 py-1 rounded-md border" style={{ color, borderColor: 'var(--color-border-subtle)', backgroundColor: 'var(--color-bg-secondary)' }}>
            {item}
          </span>
        )) : (
          <span className="text-xs text-theme-tertiary">No evidence extracted.</span>
        )}
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-subtle p-4" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
      <span className="text-[10px] uppercase tracking-widest font-bold text-theme-tertiary block mb-1">{label}</span>
      <span className="text-xl font-bold text-theme-primary">{value}</span>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="text-[10px] uppercase tracking-widest text-theme-tertiary block">{label}</span>
      <span className="text-xs font-semibold text-theme-primary">{value || 'Not specified'}</span>
    </div>
  );
}
