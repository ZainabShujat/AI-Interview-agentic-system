import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  ArrowRight,
  BriefcaseBusiness,
  Building2,
  CheckCircle2,
  FileText,
  Loader2,
  Pencil,
  Sparkles,
  Upload as UploadIcon,
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
  const { setJdId } = useSession();

  const [stage, setStage] = useState(-1);
  const [intake, setIntake] = useState<Intake>(emptyIntake);
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [jdIdLocal, setJdIdLocal] = useState<string | null>(null);
  const [blueprint, setBlueprint] = useState<Blueprint>(fallbackBlueprint);
  const [passingScore, setPassingScore] = useState(75);
  const [availableSlots, setAvailableSlots] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  const currentQuestion = intakeQuestions[stage];
  const intakeComplete = stage >= intakeQuestions.length;
  const totalStages = 12;
  const progress = Math.min(100, Math.round(((stage + 2) / totalStages) * 100));

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
      formData.append('passing_score', passingScore.toString());
      if (availableSlots.trim()) {
        const slotsArray = availableSlots.split(',').map(s => s.trim()).filter(Boolean);
        formData.append('available_slots', JSON.stringify(slotsArray));
      }
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
                  
                  <div className="mt-6 space-y-4">
                    <div>
                      <label className="text-xs font-bold uppercase tracking-widest text-theme-tertiary block mb-2">
                        Minimum Qualifying Score ({passingScore}%)
                      </label>
                      <input 
                        type="range" 
                        min="50" max="100" step="5"
                        value={passingScore}
                        onChange={(e) => setPassingScore(Number(e.target.value))}
                        className="w-full accent-blue-500"
                      />
                      <p className="text-[10px] text-theme-secondary mt-1">Candidates scoring {passingScore}% or above will be auto-scheduled.</p>
                    </div>
                    
                    <div>
                      <label className="text-xs font-bold uppercase tracking-widest text-theme-tertiary block mb-2">
                        Available Interview Slots
                      </label>
                      <input 
                        type="text" 
                        className="input-base text-sm py-3"
                        placeholder="e.g. Mon 9-11 AM, Thu 2-4 PM"
                        value={availableSlots}
                        onChange={(e) => setAvailableSlots(e.target.value)}
                      />
                      <p className="text-[10px] text-theme-secondary mt-1">Used by the Autonomous Orchestrator to propose times to qualified candidates.</p>
                    </div>
                  </div>
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

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="text-[10px] uppercase tracking-widest text-theme-tertiary block">{label}</span>
      <span className="text-xs font-semibold text-theme-primary">{value || 'Not specified'}</span>
    </div>
  );
}
