import { useRef } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowRight, ShieldCheck, CheckCircle2, MessageSquare, 
  Layers, Users, Sliders, Database, History, Eye
} from 'lucide-react';

export default function Landing() {
  const storySectionRef = useRef<HTMLDivElement>(null);

  const scrollToStory = () => {
    storySectionRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fadeInUpVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } }
  };

  return (
    <div className="relative min-h-screen font-sans selection:bg-blue-600 selection:text-white transition-colors duration-300 animate-glow" style={{ backgroundColor: 'var(--color-bg-primary)', color: 'var(--color-text-primary)' }}>
      {/* Background Soft Glow */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(37,99,235,0.08),transparent_60%)] pointer-events-none" />

      {/* --- HERO SECTION --- */}
      <section className="relative z-10 max-w-5xl mx-auto px-6 pt-20 pb-16 md:pt-28 md:pb-24 text-center">
        <motion.div
          initial="hidden"
          animate="visible"
          variants={fadeInUpVariants}
          className="space-y-10"
        >
          <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 text-xs font-semibold border border-blue-500/20">
            <span>Now in Public Beta</span>
          </div>

          <h1 className="text-hero tracking-tight max-w-4xl mx-auto font-black leading-tight text-theme-primary">
            Build interviews that think like your best hiring manager.
          </h1>

          <p className="text-body-large max-w-2xl mx-auto font-medium text-theme-secondary">
            An evidence-based screening suite that maps role requirements, conducts adaptive technical conversations, and delivers clear recommendations.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link 
              to="/upload" 
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm py-3.5 px-8 rounded-lg shadow-lg hover:shadow-blue-500/10 transition-all"
            >
              <span>Start Screening Session</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <button 
              onClick={scrollToStory}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-transparent border border-subtle hover:bg-slate-800/10 dark:hover:bg-white/5 font-medium text-sm py-3.5 px-8 rounded-lg transition-colors text-theme-secondary"
              style={{ borderColor: 'var(--color-border-subtle)' }}
            >
              <span>See how it works</span>
            </button>
          </div>
        </motion.div>
      </section>

      {/* --- SOCIAL PROOF STRIP --- */}
      <div className="border-y border-subtle py-8 text-center" style={{ borderColor: 'var(--color-border-subtle)', backgroundColor: 'var(--color-bg-secondary)' }}>
        <p className="text-xs uppercase tracking-widest font-semibold mb-4 text-theme-tertiary">
          Trusted by engineering-first teams
        </p>
        <div className="flex flex-wrap justify-center items-center gap-x-12 gap-y-4 text-sm font-bold text-theme-secondary">
          <span>Acme Corp</span>
          <span>·</span>
          <span>TechFlow</span>
          <span>·</span>
          <span>QuantumHR</span>
          <span>·</span>
          <span>BuildStack</span>
        </div>
      </div>

      {/* --- JOURNEY STORYLINE SECTIONS --- */}
      <div id="how-it-works" ref={storySectionRef} className="relative z-10 max-w-5xl mx-auto px-6 py-20 space-y-36">
        
        {/* Step 1: Assessment Creation */}
        <motion.section 
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeInUpVariants}
          className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center"
        >
          <div className="space-y-6">
            <span className="text-xs font-bold uppercase tracking-widest text-blue-600 dark:text-blue-400">Step 01</span>
            <h2 className="text-section-title text-theme-primary">
              Establish the baseline. Custom rubrics in seconds.
            </h2>
            <p className="text-body-large text-theme-secondary">
              Define the target role expectations. Our system generates precise resume screening parameters, core roadmap highlights, and target rubrics tailored exactly for your vacancy.
            </p>
          </div>

          <div className="p-8 rounded-2xl border border-subtle shadow-premium transition-all duration-300 hover:border-hover" style={{ backgroundColor: 'var(--color-bg-secondary)', borderColor: 'var(--color-border-subtle)' }}>
            <span className="text-xs font-bold text-blue-500 block uppercase tracking-widest mb-2">Role Input</span>
            <h3 className="text-lg font-bold mb-6 text-theme-primary">Senior Backend Engineer</h3>
            
            <div className="space-y-4">
              {[
                { title: 'Resume Criteria', desc: 'Auto-maps Java, Spring Boot, AWS, & 5+ Years experience.' },
                { title: 'Interview Roadmap', desc: 'Validates architectural design patterns & cloud scaling.' },
                { title: 'Technical Rubric', desc: 'Sets specific evaluation thresholds for system latency & security.' },
                { title: 'Evaluation Framework', desc: 'Prepares standardized questions tailored to target level.' }
              ].map((item, idx) => (
                <div key={idx} className="flex gap-3 items-start">
                  <CheckCircle2 className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-semibold text-theme-primary">{item.title}</h4>
                    <p className="text-xs mt-0.5 text-theme-secondary">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.section>

        {/* Step 2: Resume Intelligence */}
        <motion.section 
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeInUpVariants}
          className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center"
        >
          <div className="space-y-6 lg:order-2">
            <span className="text-xs font-bold uppercase tracking-widest text-blue-600 dark:text-blue-400">Step 02</span>
            <h2 className="text-section-title text-theme-primary">
              Understand candidate depth before the interview begins.
            </h2>
            <p className="text-body-large text-theme-secondary">
              We extract and structure capabilities cleanly. Skip raw text searching and identify core competencies immediately.
            </p>
          </div>

          <div className="p-8 rounded-2xl border border-subtle shadow-premium lg:order-1 transition-all duration-300 hover:border-hover" style={{ backgroundColor: 'var(--color-bg-secondary)', borderColor: 'var(--color-border-subtle)' }}>
            <div className="flex justify-between items-start mb-6">
              <div>
                <h3 className="text-lg font-bold text-theme-primary">Sarah Khan</h3>
                <span className="text-xs text-theme-secondary">Applicant for Senior Backend Engineer</span>
              </div>
              <span className="text-xs font-bold px-2.5 py-1 bg-blue-500/10 text-blue-600 dark:text-blue-400 rounded-md border border-blue-500/20">
                Parsed Profile
              </span>
            </div>

            <div className="space-y-4">
              <div>
                <span className="text-[10px] uppercase font-bold tracking-widest block mb-2 text-theme-tertiary">Extracted Core Skills</span>
                <div className="flex flex-wrap gap-2">
                  {['Java', 'Spring Boot', 'Kafka', 'AWS', 'Kubernetes'].map(skill => (
                    <span key={skill} className="px-3 py-1 rounded-md text-xs font-medium text-theme-primary border border-subtle" style={{ backgroundColor: 'var(--color-bg-primary)', borderColor: 'var(--color-border-subtle)' }}>
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
              <div className="pt-2 border-t border-subtle" style={{ borderColor: 'var(--color-border-subtle)' }}>
                <span className="text-[10px] uppercase font-bold tracking-widest block mb-1 text-theme-tertiary">Experience Summary</span>
                <p className="text-xs leading-relaxed text-theme-secondary">
                  Led high-throughput microservices migration. Managed cloud scaling architectures handling up to 50k concurrent requests.
                </p>
              </div>
            </div>
          </div>
        </motion.section>

        {/* Step 3: Adaptive Interview */}
        <motion.section 
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeInUpVariants}
          className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center"
        >
          <div className="space-y-6">
            <span className="text-xs font-bold uppercase tracking-widest text-blue-600 dark:text-blue-400">Step 03</span>
            <h2 className="text-section-title text-theme-primary">
              An AI interviewer that adapts in real time.
            </h2>
            <p className="text-body-large text-theme-secondary">
              No standardized script. The simulator follows up dynamically on gaps or specific details mentioned by the candidate, probing their actual engineering limits.
            </p>
          </div>

          <div className="p-8 rounded-2xl border border-subtle shadow-premium transition-all duration-300 hover:border-hover" style={{ backgroundColor: 'var(--color-bg-secondary)', borderColor: 'var(--color-border-subtle)' }}>
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                <MessageSquare className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-theme-primary">Simulation Transcript</h4>
                <p className="text-[10px] text-theme-secondary">Real-time dialog adjustments</p>
              </div>
            </div>

            <div className="space-y-4 text-xs leading-relaxed">
              <div className="p-3 rounded-lg border border-subtle" style={{ backgroundColor: 'var(--color-bg-primary)', borderColor: 'var(--color-border-subtle)' }}>
                <span className="font-bold text-blue-600 dark:text-blue-400 block mb-1">AI Interviewer</span>
                <p className="text-theme-primary">"Your projects mention migrating to Kafka for concurrency. How did you structure consumer offsets to prevent duplicate records?"</p>
              </div>
              <div className="p-3 rounded-lg border-l-2 pl-4 border-slate-400 dark:border-slate-700" style={{ backgroundColor: 'rgba(var(--color-bg-primary), 0.1)' }}>
                <span className="font-bold block mb-1 text-theme-secondary">Candidate Response</span>
                <p className="text-theme-secondary">"We configured manual committing on successful database writes and used idempotent business keys to deduplicate at the storage layer..."</p>
              </div>
              <div className="p-3 rounded-lg border border-subtle" style={{ backgroundColor: 'var(--color-bg-primary)', borderColor: 'var(--color-border-subtle)' }}>
                <span className="font-bold text-blue-600 dark:text-blue-400 block mb-1">AI Interviewer (Adaptive Follow-up)</span>
                <p className="text-theme-primary">"Manual offset commits can introduce high latency. How did you balance processing speeds with database transaction load during spike intervals?"</p>
              </div>
            </div>
          </div>
        </motion.section>

        {/* Step 4: Evidence Collection */}
        <motion.section 
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeInUpVariants}
          className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center"
        >
          <div className="space-y-6 lg:order-2">
            <span className="text-xs font-bold uppercase tracking-widest text-blue-600 dark:text-blue-400">Step 04</span>
            <h2 className="text-section-title text-theme-primary">
              Gather structured evidence. Eliminate guesswork.
            </h2>
            <p className="text-body-large text-theme-secondary">
              The engine structures responses against key performance criteria. Verify communication styles, technical accuracy, and STAR narrative validation logs.
            </p>
          </div>

          <div className="p-8 rounded-2xl border border-subtle shadow-premium lg:order-1 transition-all duration-300 hover:border-hover" style={{ backgroundColor: 'var(--color-bg-secondary)', borderColor: 'var(--color-border-subtle)' }}>
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-theme-primary">Evidence Analytics</h4>
                <p className="text-[10px] text-theme-secondary">STAR & Communication Quality check</p>
              </div>
            </div>

            <div className="space-y-3.5 text-xs">
              {[
                { title: 'Situation Validated', desc: 'Parsed clear infrastructure benchmarks & context scaling.', score: '100%' },
                { title: 'Action Verified', desc: 'Detailed individual engineering architecture tasks.', score: '95%' },
                { title: 'Technical Accuracy', desc: 'Correct mapping of distributed messaging queue properties.', score: '90%' },
                { title: 'Communication Depth', desc: 'Articulate logical delivery with zero filler-phrase reliance.', score: '88%' }
              ].map((item, idx) => (
                <div key={idx} className="flex justify-between items-center p-3 rounded-lg border border-subtle" style={{ backgroundColor: 'var(--color-bg-primary)', borderColor: 'var(--color-border-subtle)' }}>
                  <div>
                    <h5 className="font-semibold text-theme-primary">{item.title}</h5>
                    <p className="text-[10px] text-theme-secondary mt-0.5">{item.desc}</p>
                  </div>
                  <span className="text-xs font-bold text-blue-600 dark:text-blue-400">{item.score}</span>
                </div>
              ))}
            </div>
          </div>
        </motion.section>

        {/* Step 5: Hiring Recommendation (Climax) */}
        <motion.section 
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeInUpVariants}
          className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center"
        >
          <div className="space-y-6">
            <span className="text-xs font-bold uppercase tracking-widest text-blue-600 dark:text-blue-400">Step 05</span>
            <h2 className="text-section-title text-theme-primary">
              Synthesized hiring reports. A clear recommendation.
            </h2>
            <p className="text-body-large text-theme-secondary">
              No dashboards to configure. Receive high-level scorecard insights highlighting specific strengths and development areas immediately.
            </p>
          </div>

          <div className="p-8 rounded-2xl border border-subtle shadow-premium transition-all duration-300 hover:border-hover" style={{ backgroundColor: 'var(--color-bg-secondary)', borderColor: 'var(--color-border-subtle)' }}>
            <div className="flex justify-between items-center pb-5 mb-5 border-b border-subtle" style={{ borderColor: 'var(--color-border-subtle)' }}>
              <div>
                <h3 className="text-base font-bold text-theme-primary">Executive Evaluation</h3>
                <p className="text-[10px] text-theme-secondary">Recruiter reference file #4092</p>
              </div>
              <div className="text-right">
                <span className="px-3 py-1 text-xs font-bold bg-blue-500/10 text-blue-600 dark:text-blue-400 rounded-md border border-blue-500/20">
                  Strong Hire
                </span>
                <span className="block text-sm font-extrabold mt-1 text-theme-primary">92% Fit</span>
              </div>
            </div>

            <div className="space-y-4 text-xs">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-widest block mb-2 text-theme-tertiary">Verified Strengths</span>
                <ul className="space-y-1.5 text-theme-primary">
                  <li>✓ System Design & Concurrency Handling</li>
                  <li>✓ Leadership & Technical Strategy Mentoring</li>
                  <li>✓ Communication & Structural Explanations</li>
                </ul>
              </div>
              <div className="pt-4 border-t border-subtle" style={{ borderColor: 'var(--color-border-subtle)' }}>
                <span className="text-[10px] font-bold uppercase tracking-widest block mb-2 text-theme-tertiary">Development Areas</span>
                <ul className="space-y-1.5 text-theme-secondary">
                  <li>• Cloud Cost Optimization (lacks active budget control experience)</li>
                  <li>• Distributed Tracing (minimal deployment depth with OpenTelemetry)</li>
                </ul>
              </div>
            </div>
          </div>
        </motion.section>

        {/* Step 6: Enterprise Capabilities */}
        <motion.section 
          id="enterprise"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeInUpVariants}
          className="border-t border-subtle pt-24 space-y-16"
          style={{ borderColor: 'var(--color-border-subtle)' }}
        >
          <div className="text-center max-w-2xl mx-auto space-y-4">
            <span className="text-xs font-bold uppercase tracking-widest text-blue-600 dark:text-blue-400">Scale Securely</span>
            <h2 className="text-section-title text-theme-primary">
              Built for engineering and recruiting organizations.
            </h2>
            <p className="text-body-large text-theme-secondary">
              Enterprise controls to streamline high-volume talent pipelines while maintaining compliance.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              { icon: Users, title: 'Team Workspaces', desc: 'Coordinate assessments and share candidates across hiring groups.' },
              { icon: Layers, title: 'Role Templates', desc: 'Standardize expectations across departments for rapid hiring execution.' },
              { icon: Sliders, title: 'Candidate Pipelines', desc: 'Directly monitor candidate progressions from start to final recommendation.' },
              { icon: Database, title: 'Audit Trails', desc: 'Track rubric updates and interview outcomes securely.' },
              { icon: History, title: 'Hiring Collaboration', desc: 'Leave collaborative internal comments and scoring peer reviews.' },
              { icon: Eye, title: 'Department Analytics', desc: 'Examine pass-through metrics and recruiter throughput profiles.' }
            ].map((item, idx) => (
              <div key={idx} className="p-6 rounded-xl border border-subtle transition-all duration-300 hover:border-hover" style={{ backgroundColor: 'var(--color-bg-secondary)', borderColor: 'var(--color-border-subtle)' }}>
                <item.icon className="w-5 h-5 text-blue-600 mb-4" />
                <h4 className="text-sm font-bold mb-2 text-theme-primary">{item.title}</h4>
                <p className="text-xs leading-relaxed text-theme-secondary">{item.desc}</p>
              </div>
            ))}
          </div>
        </motion.section>

      </div>

      {/* --- CLOSING CTA --- */}
      <section className="relative z-10 border-t border-subtle" style={{ borderColor: 'var(--color-border-subtle)', backgroundColor: 'var(--color-bg-secondary)' }}>
        <div className="max-w-4xl mx-auto px-6 py-28 text-center space-y-8">
          <h2 className="text-3xl md:text-4xl font-extrabold text-theme-primary">
            Ready to make better hiring decisions?
          </h2>
          <p className="text-sm max-w-lg mx-auto text-theme-secondary">
            Initiate assessment screening sessions today. Standardize evaluation variables across all prospective applicants.
          </p>
          <div className="pt-4">
            <Link 
              to="/upload" 
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm py-3.5 px-8 rounded-lg shadow-lg hover:shadow-blue-500/10 transition-all"
            >
              <span>Get Started Immediately</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
