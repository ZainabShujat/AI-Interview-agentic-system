import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload as UploadIcon, FileText, ArrowRight, Loader2, Trophy, UserRoundCheck } from 'lucide-react';
import axios from 'axios';
import { useSession } from '../App';

export default function StudentAssessment() {
  const navigate = useNavigate();
  const { jdId: pathJdId } = useParams<{ jdId?: string }>();
  const { setResumeId, setJdId } = useSession();

  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState('');
  const [jdMode, setJdMode] = useState<'existing' | 'upload' | 'paste'>('existing');
  const [existingJds, setExistingJds] = useState<any[]>([]);
  const [preSelectedJd, setPreSelectedJd] = useState<any | null>(null);
  const [selectedJdId, setSelectedJdId] = useState('');
  const [loading, setLoading] = useState(false);
  const [progressMsg, setProgressMsg] = useState('');
  const [error, setError] = useState('');

  const handleResumeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files?.[0]) {
      setResumeFile(event.target.files[0]);
    }
  };

  useEffect(() => {
    const fetchJds = async () => {
      try {
        const res = await axios.get('/api/jd');
        setExistingJds(res.data || []);
        
        if (pathJdId) {
          const found = (res.data || []).find((j: any) => String(j.id) === String(pathJdId));
          if (found) {
            setPreSelectedJd(found);
            setSelectedJdId(pathJdId);
            setJdMode('existing');
          } else {
            // If ID is not in active list (e.g. newly loaded but not in top 50), try to fetch details
            try {
              // Wait, we can query details or default selection
              if (res.data?.[0]?.id) {
                setSelectedJdId(res.data[0].id);
              }
            } catch (err) {}
          }
        } else if (res.data?.[0]?.id) {
          setSelectedJdId(res.data[0].id);
        } else {
          setJdMode('paste');
        }
      } catch (err) {
        console.warn('Could not load existing JDs.', err);
        setJdMode('paste');
      }
    };

    fetchJds();
  }, [pathJdId]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const hasJdSource = (jdMode === 'existing' && selectedJdId) || (jdMode === 'upload' && jdFile) || (jdMode === 'paste' && jdText.trim());
    if (!resumeFile || !hasJdSource) return;

    setLoading(true);
    setError('');
    try {
      setProgressMsg('Parsing your resume...');
      const resumeFormData = new FormData();
      resumeFormData.append('file', resumeFile);

      const resumeRes = await axios.post('/api/resume', resumeFormData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const resumeId = resumeRes.data.id || resumeRes.data.resume_id;
      setResumeId(resumeId);

      setProgressMsg('Preparing the target job description...');
      let jdId = selectedJdId;
      if (jdMode === 'upload' && jdFile) {
        const jdFormData = new FormData();
        jdFormData.append('file', jdFile);
        const jdRes = await axios.post('/api/jd/upload', jdFormData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        jdId = jdRes.data.id || jdRes.data.jd_id;
      } else if (jdMode === 'paste') {
        const jdRes = await axios.post('/api/jd', { text: jdText });
        jdId = jdRes.data.id || jdRes.data.jd_id;
      }
      setJdId(jdId);

      setProgressMsg('Measuring readiness...');
      navigate('/student/readiness');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Assessment setup failed. Check the backend and Gemini API key, then try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="layout-container max-w-5xl">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <aside className="lg:col-span-4">
          <div className="card-premium p-7 space-y-6">
            <div className="w-12 h-12 rounded-xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center">
              <UserRoundCheck className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <span className="text-[10px] uppercase tracking-widest font-bold text-theme-tertiary block mb-2">
                Student Assessment
              </span>
              <h1 className="text-3xl font-bold text-theme-primary tracking-tight">
                Test your readiness for a real job.
              </h1>
              <p className="text-sm mt-3 text-theme-secondary">
                Upload your resume, choose a recruiter-created job or add a new JD, review your fit, complete the AI interview, and see where you rank for that job.
              </p>
            </div>
            <div className="space-y-3 text-xs">
              {[
                ['Readiness Match', 'Resume and JD are compared before the interview.'],
                ['AI Interview', 'Questions target the role and your gaps.'],
                ['Job Leaderboard', 'Your final rank is shown against other applicants.'],
              ].map(([title, body]) => (
                <div key={title} className="rounded-lg border border-subtle p-4" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
                  <span className="font-bold text-theme-primary block">{title}</span>
                  <span className="text-theme-secondary">{body}</span>
                </div>
              ))}
            </div>
          </div>
        </aside>

        <section className="lg:col-span-8">
          <form onSubmit={handleSubmit} className="card-premium p-8 space-y-8">
            <div>
              <span className="text-[10px] uppercase tracking-widest font-bold text-theme-tertiary block mb-2">
                Step 1
              </span>
              <h2 className="text-2xl font-bold text-theme-primary tracking-tight">Upload resume and target JD</h2>
              <p className="text-sm text-theme-secondary mt-1">
                The student side stays direct: give the system your profile and target role, then move into readiness.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="flex flex-col">
                <label className="text-sm font-semibold text-theme-primary mb-3 block">
                  Resume PDF
                </label>
                <div
                  className="flex-grow card-premium card-interactive flex flex-col items-center justify-center border-dashed py-12 px-6 text-center"
                  style={{
                    borderStyle: resumeFile ? 'solid' : 'dashed',
                    borderColor: resumeFile ? 'rgba(255, 255, 255, 0.2)' : 'var(--color-border-subtle)',
                    backgroundColor: 'var(--color-bg-primary)',
                  }}
                >
                  <input
                    type="file"
                    id="student-resume-upload"
                    className="hidden"
                    accept=".pdf"
                    onChange={handleResumeChange}
                  />
                  <label htmlFor="student-resume-upload" className="cursor-pointer w-full h-full flex flex-col items-center justify-center">
                    <AnimatePresence mode="wait">
                      {resumeFile ? (
                        <motion.div key="file" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col items-center">
                          <FileText className="w-8 h-8 text-blue-400 mb-4" />
                          <span className="text-sm font-semibold text-theme-primary max-w-[220px] truncate">{resumeFile.name}</span>
                          <span className="text-xs text-theme-tertiary mt-1">Click to replace</span>
                        </motion.div>
                      ) : (
                        <motion.div key="prompt" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col items-center">
                          <UploadIcon className="w-8 h-8 text-theme-secondary mb-4" />
                          <span className="text-sm font-semibold text-theme-primary">Upload resume</span>
                          <span className="text-xs text-theme-tertiary mt-1">PDF only</span>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </label>
                </div>
              </div>

              <div className="flex flex-col justify-between h-full">
                <label className="text-sm font-semibold text-theme-primary mb-3 block">
                  Target Job
                </label>
                {preSelectedJd ? (
                  <div className="rounded-xl border border-subtle p-5 flex-grow flex flex-col justify-center" style={{ backgroundColor: 'var(--color-bg-primary)', borderColor: 'var(--color-border-subtle)' }}>
                    <span className="text-[10px] uppercase tracking-widest font-bold text-blue-400 block mb-2">Assigned Recruiter Assessment</span>
                    <h4 className="text-base font-bold text-white leading-tight">{preSelectedJd.title}</h4>
                    <p className="text-xs text-theme-secondary mt-1">
                      {preSelectedJd.department || 'General'} • {preSelectedJd.seniority || 'Mid Level'}
                    </p>
                    <p className="text-[11px] mt-4 text-emerald-400 font-medium">
                      ✓ Target role requirements are recruiter-approved
                    </p>
                  </div>
                ) : (
                  <div className="rounded-xl border border-subtle p-4 space-y-4 flex-grow" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
                    <div className="grid grid-cols-3 gap-2">
                      {[
                        ['existing', 'Existing JD'],
                        ['upload', 'Upload JD'],
                        ['paste', 'Paste JD'],
                      ].map(([mode, label]) => (
                        <button
                          key={mode}
                          type="button"
                          onClick={() => setJdMode(mode as any)}
                          className="text-xs font-bold rounded-md border px-2 py-2"
                          style={{
                            borderColor: jdMode === mode ? 'var(--color-border-hover)' : 'var(--color-border-subtle)',
                            backgroundColor: jdMode === mode ? 'var(--color-mauve-strong)' : 'transparent',
                          }}
                        >
                          {label}
                        </button>
                      ))}
                    </div>

                    {jdMode === 'existing' && (
                      <div className="space-y-3">
                        {existingJds.length > 0 ? (
                          <select
                            className="input-base"
                            value={selectedJdId}
                            onChange={(event) => setSelectedJdId(event.target.value)}
                          >
                            {existingJds.map((jd) => (
                              <option key={jd.id} value={jd.id}>
                                {jd.title} {jd.seniority ? `- ${jd.seniority}` : ''}
                              </option>
                            ))}
                          </select>
                        ) : (
                          <p className="text-xs text-theme-secondary">
                            No recruiter-created JDs yet. Upload or paste a JD to create the first shared benchmark.
                          </p>
                        )}
                      </div>
                    )}

                    {jdMode === 'upload' && (
                      <div className="rounded-lg border border-dashed p-6 text-center" style={{ borderColor: 'var(--color-border-hover)' }}>
                        <input
                          id="student-jd-file"
                          type="file"
                          className="hidden"
                          accept=".pdf,.txt,.md"
                          onChange={(event) => setJdFile(event.target.files?.[0] || null)}
                        />
                        <label htmlFor="student-jd-file" className="cursor-pointer flex flex-col items-center">
                          <FileText className="w-8 h-8 mb-3" />
                          <span className="text-sm font-semibold text-theme-primary">{jdFile ? jdFile.name : 'Upload JD file'}</span>
                          <span className="text-xs text-theme-tertiary mt-1">PDF, TXT, or Markdown</span>
                        </label>
                      </div>
                    )}

                    {jdMode === 'paste' && (
                      <textarea
                        id="student-jd-input"
                        className="input-base resize-none text-sm min-h-[190px] p-4"
                        placeholder="Paste the job description you want to benchmark yourself against..."
                        value={jdText}
                        onChange={(event) => setJdText(event.target.value)}
                      />
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
              {error && (
                <div className="w-full rounded-lg border px-4 py-3 text-sm" style={{ borderColor: 'rgba(244, 63, 94, 0.3)', backgroundColor: 'rgba(244, 63, 94, 0.08)', color: 'var(--color-accent-coral)' }}>
                  {error}
                </div>
              )}
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-2 text-xs text-theme-secondary">
                <Trophy className="w-4 h-4 text-blue-400" />
                <span>After interview completion, your rank appears on the job leaderboard.</span>
              </div>
              <button
                type="submit"
                disabled={
                  !resumeFile ||
                  loading ||
                  !((jdMode === 'existing' && selectedJdId) || (jdMode === 'upload' && jdFile) || (jdMode === 'paste' && jdText.trim()))
                }
                className="btn-base btn-primary px-6 py-3 gap-2"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
                <span>{loading ? progressMsg : 'Measure Readiness'}</span>
              </button>
            </div>
          </form>
        </section>
      </div>
    </div>
  );
}
