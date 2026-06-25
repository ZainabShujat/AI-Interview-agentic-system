import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload as UploadIcon, FileText, ArrowRight, Loader2 } from 'lucide-react';
import { useSession } from '../App';
import axios from 'axios';

export default function Upload() {
  const navigate = useNavigate();
  const { setResumeId, setJdId } = useSession();

  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState('');
  const [loading, setLoading] = useState(false);
  const [progressMsg, setProgressMsg] = useState('');

  const handleResumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setResumeFile(e.target.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'application/pdf') {
        setResumeFile(file);
      } else {
        alert('Please upload a PDF file.');
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resumeFile) return;

    setLoading(true);
    try {
      // Step 1: Upload Resume
      setProgressMsg('Extracting resume content...');
      const resumeFormData = new FormData();
      resumeFormData.append('file', resumeFile);

      let resumeIdRes = 'mock-resume-123';
      try {
        const res = await axios.post('/api/resume', resumeFormData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        resumeIdRes = res.data.id || res.data.resume_id;
      } catch (err) {
        console.warn('Backend not running or upload failed. Using mock data.', err);
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }
      setResumeId(resumeIdRes);

      // Step 2: Upload JD
      setProgressMsg('Analyzing target Job Description...');
      let jdIdRes = 'mock-jd-123';
      if (jdText.trim()) {
        try {
          const res = await axios.post('/api/jd', { text: jdText });
          jdIdRes = res.data.id || res.data.jd_id;
        } catch (err) {
          console.warn('Backend not running or JD upload failed. Using mock data.', err);
          await new Promise((resolve) => setTimeout(resolve, 1000));
        }
      } else {
        // Fallback JD text
        await new Promise((resolve) => setTimeout(resolve, 800));
      }
      setJdId(jdIdRes);

      setProgressMsg('Finalizing analysis mapping...');
      await new Promise((resolve) => setTimeout(resolve, 600));

      setLoading(false);
      navigate('/match');
    } catch (error) {
      console.error('Error during upload sequence:', error);
      setLoading(false);
      alert('An error occurred during file parsing. Proceeding with demo data.');
      setResumeId('mock-resume-123');
      setJdId('mock-jd-123');
      navigate('/match');
    }
  };

  return (
    <div className="layout-container max-w-4xl">
      <div className="text-center mb-12">
        <h1 className="text-3xl font-bold tracking-tight text-white mb-3" style={{ fontFamily: "'Outfit', sans-serif" }}>
          Begin Assessment Session
        </h1>
        <p className="text-sm max-w-lg mx-auto" style={{ color: 'var(--color-text-secondary)' }}>
          Provide your current resume and the target role details. We will perform a gap analysis and construct a tailored mock simulation.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Resume Upload Panel */}
          <div className="flex flex-col">
            <label className="text-sm font-semibold text-white mb-3 block" style={{ fontFamily: "'Outfit', sans-serif" }}>
              Upload Resume (PDF only)
            </label>
            <div
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              className={`flex-grow card-premium card-interactive flex flex-col items-center justify-center border-dashed py-12 px-6 text-center transition-all ${
                resumeFile ? 'border-solid border-white/20 bg-dark-900/20' : 'border-dark-700 hover:border-dark-500'
              }`}
              style={{
                borderStyle: resumeFile ? 'solid' : 'dashed',
                borderColor: resumeFile ? 'rgba(255, 255, 255, 0.2)' : 'var(--color-border-subtle)',
                backgroundColor: resumeFile ? 'rgba(22, 25, 32, 0.2)' : 'var(--color-bg-secondary)',
              }}
            >
              <input
                type="file"
                id="resume-upload"
                className="hidden"
                accept=".pdf"
                onChange={handleResumeChange}
              />
              <label htmlFor="resume-upload" className="cursor-pointer w-full h-full flex flex-col items-center justify-center">
                <AnimatePresence mode="wait">
                  {resumeFile ? (
                    <motion.div
                      key="file"
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      className="flex flex-col items-center"
                    >
                      <div className="w-12 h-12 rounded-full bg-white/5 border border-white/10 flex items-center justify-center mb-4">
                        <FileText className="w-6 h-6 text-white" />
                      </div>
                      <span className="text-sm font-medium text-white max-w-[200px] truncate mb-1">
                        {resumeFile.name}
                      </span>
                      <span className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                        {(resumeFile.size / (1024 * 1024)).toFixed(2)} MB • Click to replace
                      </span>
                    </motion.div>
                  ) : (
                    <motion.div
                      key="prompt"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="flex flex-col items-center"
                    >
                      <div className="w-12 h-12 rounded-full bg-dark-950 border border-subtle flex items-center justify-center mb-4" style={{ borderColor: 'var(--color-border-subtle)' }}>
                        <UploadIcon className="w-5 h-5 text-dark-400" style={{ color: 'var(--color-text-secondary)' }} />
                      </div>
                      <span className="text-sm font-medium text-white mb-1">
                        Drag and drop your resume
                      </span>
                      <span className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                        or click to browse from device
                      </span>
                    </motion.div>
                  )}
                </AnimatePresence>
              </label>
            </div>
          </div>

          {/* Job Description Text Area */}
          <div className="flex flex-col">
            <label htmlFor="jd-input" className="text-sm font-semibold text-white mb-3 block" style={{ fontFamily: "'Outfit', sans-serif" }}>
              Target Job Description
            </label>
            <div className="flex-grow flex flex-col">
              <textarea
                id="jd-input"
                className="input-base flex-grow resize-none font-sans text-sm min-h-[220px] p-4"
                placeholder="Paste the Job Description or requirements of the role you are preparing for..."
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex justify-center pt-4">
          <button
            type="submit"
            disabled={!resumeFile || loading}
            className="btn-base btn-primary text-base px-8 py-3.5 gap-3"
            style={{ minWidth: '220px' }}
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>{progressMsg}</span>
              </>
            ) : (
              <>
                <span>Run Match Analysis</span>
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
