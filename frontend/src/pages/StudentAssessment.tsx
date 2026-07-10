import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload as UploadIcon, FileText, ArrowRight, Loader2, UserRoundCheck } from 'lucide-react';
import axios from 'axios';
import { useSession } from '../App';

export default function StudentAssessment() {
  const navigate = useNavigate();
  const { jdId: pathJdId } = useParams<{ jdId?: string }>();
  const { setResumeId, setJdId, setInterviewId } = useSession();

  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [progressMsg, setProgressMsg] = useState('');
  const [error, setError] = useState('');

  const handleResumeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files?.[0]) {
      setResumeFile(event.target.files[0]);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!resumeFile) return;

    if (!pathJdId) {
      setError('No Job Description ID found in the URL. Please use the exact link provided by the recruiter.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      setProgressMsg('Uploading resume and starting assessment...');
      const formData = new FormData();
      formData.append('jd_id', pathJdId);
      formData.append('resume_file', resumeFile);

      const res = await axios.post('/api/interview/start-autonomous', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      
      const { interview_id, resume_id } = res.data;
      
      setResumeId(resume_id);
      setJdId(pathJdId);
      setInterviewId(interview_id);

      setProgressMsg('Entering interview room...');
      // Wait a moment for UX
      setTimeout(() => navigate('/interview'), 1500);
      
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Assessment setup failed. Please try again.');
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
                Autonomous Interview Flow
              </h1>
              <p className="text-sm mt-3 text-theme-secondary">
                You've been invited to apply for this role. Upload your resume and the system will automatically parse your background, evaluate your fit, and launch an adaptive AI interview.
              </p>
            </div>
            <div className="space-y-3 text-xs">
              {[
                ['Resume Intelligence', 'Your resume is instantly parsed and matched to the job.'],
                ['Adaptive Interview', 'Complete a real-time, dynamic AI interview session.'],
                ['Autonomous Next Steps', 'If you qualify, you will automatically receive an invitation to meet the team.'],
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
              <h2 className="text-2xl font-bold text-theme-primary tracking-tight">Upload your resume to begin</h2>
              <p className="text-sm text-theme-secondary mt-1">
                The entire process is fully automated. You do not need to manually configure anything.
              </p>
            </div>

            <div className="flex flex-col">
              <label className="text-sm font-semibold text-theme-primary mb-3 block">
                Resume PDF
              </label>
              <div
                className="card-premium card-interactive flex flex-col items-center justify-center border-dashed py-16 px-6 text-center"
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
                        <FileText className="w-12 h-12 text-blue-400 mb-4" />
                        <span className="text-sm font-semibold text-theme-primary max-w-[300px] truncate">{resumeFile.name}</span>
                        <span className="text-xs text-theme-tertiary mt-2">Click to replace</span>
                      </motion.div>
                    ) : (
                      <motion.div key="prompt" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col items-center">
                        <UploadIcon className="w-12 h-12 text-theme-secondary mb-4" />
                        <span className="text-base font-semibold text-theme-primary">Upload resume</span>
                        <span className="text-xs text-theme-tertiary mt-2">PDF only</span>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </label>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
              {error && (
                <div className="w-full rounded-lg border px-4 py-3 text-sm" style={{ borderColor: 'rgba(244, 63, 94, 0.3)', backgroundColor: 'rgba(244, 63, 94, 0.08)', color: 'var(--color-accent-coral)' }}>
                  {error}
                </div>
              )}
            </div>

            <div className="flex justify-end pt-4 border-t border-subtle">
              <button
                type="submit"
                disabled={!resumeFile || loading}
                className="btn-base btn-primary px-8 py-3 gap-2"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
                <span>{loading ? progressMsg : 'Start Interview'}</span>
              </button>
            </div>
          </form>
        </section>
      </div>
    </div>
  );
}
