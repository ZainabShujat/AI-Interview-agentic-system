import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, Send, Loader2, Timer, Video, VideoOff, Volume2, VolumeX, Camera, AlertTriangle } from 'lucide-react';
import { useSession } from '../App';
import axios from 'axios';

// Removed local SpeechRecognition in favor of Deepgram backend

export default function Interview() {
  const navigate = useNavigate();
  const { interviewId } = useSession();

  // Interview state
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [totalQuestions] = useState(3);
  const [questionText, setQuestionText] = useState('How do you design a robust caching layer in a high-frequency financial system?');
  const [category, setCategory] = useState('Technical');
  const [answerText, setAnswerText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Camera feed states
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [videoMuted, setVideoMuted] = useState(false);
  const [audioMuted, setAudioMuted] = useState(false);


  // Speech and timing states
  const [isRecording, setIsRecording] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [firstInputTime, setFirstInputTime] = useState<number | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<BlobPart[]>([]);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const startTimeRef = useRef<number>(0);

  // Proctoring state
  const [tabSwitches, setTabSwitches] = useState(0);
  const [showProctorWarning, setShowProctorWarning] = useState(false);

  useEffect(() => {
    const handleBlur = () => {
      setTabSwitches(prev => {
        const next = prev + 1;
        setShowProctorWarning(true);
        return next;
      });
    };

    window.addEventListener('blur', handleBlur);
    return () => {
      window.removeEventListener('blur', handleBlur);
    };
  }, []);

  // Initialize camera feed on mount
  useEffect(() => {
    async function startCamera() {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        setStream(mediaStream);
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
        }
        setCameraActive(true);
      } catch (err) {
        console.warn("Camera or audio access denied or unavailable:", err);
        setCameraActive(false);
      }
    }
    startCamera();

    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const toggleVideoMute = () => {
    if (stream) {
      const videoTracks = stream.getVideoTracks();
      videoTracks.forEach(track => {
        track.enabled = !track.enabled;
      });
      setVideoMuted(!videoMuted);
    }
  };

  const toggleAudioMute = () => {
    if (stream) {
      const audioTracks = stream.getAudioTracks();
      audioTracks.forEach(track => {
        track.enabled = !track.enabled;
      });
      setAudioMuted(!audioMuted);
    }
  };

  // Clear audio blob when question changes
  useEffect(() => {
    setAudioBlob(null);
  }, [currentQuestionIndex]);

  // Start/Stop question timer
  useEffect(() => {
    // Reset timer for new question
    setElapsedTime(0);
    setFirstInputTime(null);
    setAnswerText('');
    startTimeRef.current = Date.now();

    timerRef.current = setInterval(() => {
      setElapsedTime((prev) => prev + 1);
    }, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [currentQuestionIndex]);

  const toggleRecording = () => {
    if (!stream) {
      alert('Microphone access is required to record audio.');
      return;
    }

    if (isRecording && mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    } else {
      setAudioBlob(null);
      setAnswerText(''); // Clear typed text if they choose to record
      audioChunksRef.current = [];
      const mediaRecorder = new MediaRecorder(stream);
      
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        setAnswerText('[Audio Recording Saved - Ready to Submit]');
      };

      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
      if (firstInputTime === null) {
        setFirstInputTime(Date.now() - startTimeRef.current);
      }
    }
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setAnswerText(e.target.value);
    if (firstInputTime === null && e.target.value.length > 0) {
      setFirstInputTime(Date.now() - startTimeRef.current);
    }
  };

  const calculateConfidenceSignals = () => {
    // Measure response parameters
    const text = answerText.trim();
    const wordCount = text.split(/\s+/).filter(Boolean).length;
    const durationMinutes = elapsedTime / 60 || 0.1;
    const wpm = Math.round(wordCount / durationMinutes);

    // List common filler words
    const fillerWords = ['um', 'uh', 'like', 'actually', 'basically', 'so', 'you know'];
    let fillerCount = 0;
    fillerWords.forEach((word) => {
      const regex = new RegExp(`\\b${word}\\b`, 'gi');
      const matches = text.match(regex);
      if (matches) fillerCount += matches.length;
    });

    return {
      responseTime: elapsedTime,
      latencySeconds: firstInputTime ? Number((firstInputTime / 1000).toFixed(2)) : elapsedTime,
      wordCount,
      wordsPerMinute: wpm,
      fillerCount,
    };
  };

  const handleSubmitResponse = async () => {
    if (!answerText.trim() && !audioBlob) return;

    if (timerRef.current) clearInterval(timerRef.current);
    if (isRecording && mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }

    setLoading(true);
    setError('');
    const signals = calculateConfidenceSignals();

    try {
      if (!interviewId) {
        throw new Error('No active interview session was found. Start from the student or recruiter assessment flow.');
      }

      let res;
      if (audioBlob) {
        // Submit via Deepgram backend
        const formData = new FormData();
        formData.append('interview_id', interviewId);
        formData.append('question_text', questionText);
        formData.append('category', category);
        formData.append('signals', JSON.stringify(signals));
        formData.append('audio_file', audioBlob, 'answer.webm');

        res = await axios.post('/api/interview/audio-answer', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      } else {
        // Submit typed text
        res = await axios.post('/api/interview/answer', {
          interview_id: interviewId,
          question_text: questionText,
          category,
          answer_text: answerText,
          signals,
        });
      }

      const nextQuestionRes = res.data;

      if (nextQuestionRes.finished || currentQuestionIndex >= totalQuestions - 1) {
        navigate('/student/leaderboard');
      } else {
        setQuestionText(nextQuestionRes.question);
        setCategory(nextQuestionRes.category);
        setCurrentQuestionIndex((prev) => prev + 1);
      }
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : 'Could not submit response. Check the backend/API key and try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const remainingSecs = secs % 60;
    return `${mins.toString().padStart(2, '0')}:${remainingSecs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="layout-container max-w-6xl relative">
      {/* Floating Proctoring Warning Banner */}
      <AnimatePresence>
        {showProctorWarning && (
          <motion.div
            initial={{ opacity: 0, y: -50, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            className="fixed top-20 left-1/2 -translate-x-1/2 z-50 bg-rose-950/95 border border-rose-500 text-rose-200 px-5 py-3.5 rounded-lg shadow-2xl flex items-start gap-3 max-w-md"
            style={{ boxShadow: '0 10px 25px -5px rgba(244, 63, 94, 0.4)' }}
          >
            <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
            <div className="text-xs space-y-1">
              <span className="font-bold text-white block text-[11px] tracking-wide">PROCTORING ALERT (FOCUS LOST)</span>
              <p className="leading-relaxed opacity-90">
                Leaving the assessment tab or window is monitored. Your workspace switches are recorded and reported to recruiters.
              </p>
              <div className="flex items-center justify-between pt-1.5 border-t border-rose-500/20 mt-1.5">
                <span className="text-[10px] text-rose-300">Total Violations: <strong className="text-white">{tabSwitches}</strong></span>
                <button 
                  onClick={() => setShowProctorWarning(false)}
                  className="px-2 py-0.5 bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 text-[9px] font-bold uppercase rounded transition-colors"
                >
                  Acknowledge
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        
        {/* Left Column: Progress Sidebar & Assessment Context */}
        <div className="lg:col-span-1 space-y-6">
          <div className="card-premium p-5 bg-dark-900/10 space-y-5">
            <div>
              <span className="text-[10px] uppercase font-bold tracking-widest text-dark-500 block mb-3" style={{ color: 'var(--color-text-tertiary)' }}>
                Assessment Modules
              </span>
              <div className="space-y-2 text-xs">
                {[
                  { name: 'Technical', label: '1. Technical Validation' },
                  { name: 'Scenario', label: '2. Scenario Orchestration' },
                  { name: 'Behavioral', label: '3. Behavioral Alignment' },
                  { name: 'Leadership', label: '4. Leadership Assessment' }
                ].map((mod) => {
                  const isActive = category === mod.name;
                  return (
                    <div 
                      key={mod.name} 
                      className="px-3 py-2 rounded-md border transition-colors font-medium"
                      style={{
                        backgroundColor: isActive ? 'rgba(45, 212, 191, 0.05)' : 'transparent',
                        borderColor: isActive ? 'var(--color-accent-teal)' : 'var(--color-border-subtle)',
                        color: isActive ? 'var(--color-accent-teal)' : 'var(--color-text-secondary)'
                      }}
                    >
                      {mod.label}
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="border-t border-subtle pt-4" style={{ borderColor: 'var(--color-border-subtle)' }}>
              <span className="text-[10px] uppercase font-bold tracking-widest text-dark-500 block mb-2" style={{ color: 'var(--color-text-tertiary)' }}>
                Active Criteria
              </span>
              <p className="text-[11px] leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
                {category === 'Technical' && 'Evaluates architecture depth, coding fundamentals, caching layers, and database synchronization.'}
                {category === 'Scenario' && 'Evaluates blue-green deployment strategies, high-frequency queues, zero-downtime, and recovery.'}
                {category === 'Behavioral' && 'Evaluates answer structural completeness using the STAR framework, detailing Situation, Task, Action, and Result.'}
                {category === 'Leadership' && 'Evaluates project ownership capacity, senior mentoring capabilities, and conflict mitigation skills.'}
              </p>
            </div>

            <div className="border-t border-subtle pt-4" style={{ borderColor: 'var(--color-border-subtle)' }}>
              <span className="text-[10px] uppercase font-bold tracking-widest text-dark-500 block mb-1" style={{ color: 'var(--color-text-tertiary)' }}>
                Response Guidelines
              </span>
              <ul className="list-disc list-inside text-[10px] space-y-1" style={{ color: 'var(--color-text-tertiary)' }}>
                <li>Provide supporting examples</li>
                <li>Avoid verbose descriptions</li>
                <li>Detail tech trade-offs</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Right Column: Active Assessment Console */}
        <div className="lg:col-span-3 space-y-6">
          {/* Top Header Grid */}
          <div className="flex items-center justify-between border-b border-subtle pb-4" style={{ borderColor: 'var(--color-border-subtle)' }}>
            <div>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border border-subtle text-dark-400 mr-2" style={{ borderColor: 'var(--color-border-subtle)', color: 'var(--color-text-secondary)' }}>
                Active Console
              </span>
              <span className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                Question {currentQuestionIndex + 1} of {totalQuestions}
              </span>
            </div>
            <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--color-text-secondary)' }}>
              <Timer className="w-4 h-4 opacity-70" />
              <span>{formatTime(elapsedTime)}</span>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
            
            {/* Left part: Question & Response Console */}
            <div className="xl:col-span-8 space-y-6">
              <AnimatePresence mode="wait">
                {loading ? (
                  <motion.div
                    key="loading"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="card-premium flex flex-col items-center justify-center py-24 text-center bg-dark-900/10"
                  >
                    <Loader2 className="w-10 h-10 text-white animate-spin opacity-50 mb-6" />
                    <h3 className="text-lg font-semibold text-white mb-2" style={{ fontFamily: "'Outfit', sans-serif" }}>
                      Processing Response Diagnostics
                    </h3>
                    <p className="text-xs max-w-xs" style={{ color: 'var(--color-text-secondary)' }}>
                      Aggregating accuracy, structural depth, and communication pacing matrices...
                    </p>
                  </motion.div>
                ) : (
                  <motion.div
                    key="question"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] as const }}
                    className="space-y-6"
                  >
                    {/* Question Display Card */}
                    <div className="card-premium py-8 px-8 relative overflow-hidden bg-dark-900/10 border-l-4" style={{ borderLeftColor: 'var(--color-accent-teal)' }}>
                      <span className="text-[9px] uppercase font-bold tracking-widest text-dark-500 mb-2 block" style={{ color: 'var(--color-text-tertiary)' }}>
                        Assessment Request Directive
                      </span>
                      <h2 className="text-lg md:text-xl text-white font-medium tracking-tight leading-relaxed" style={{ fontFamily: "'Outfit', sans-serif" }}>
                        {questionText}
                      </h2>
                    </div>

                    {/* Answer Box Panel */}
                    <div className="space-y-4">
                      <div className="flex flex-col">
                        <label htmlFor="assessment-response" className="text-xs font-semibold uppercase tracking-wider text-dark-500 mb-2 block" style={{ color: 'var(--color-text-secondary)' }}>
                          Response Input
                        </label>
                        <div className="relative">
                          <textarea
                            id="assessment-response"
                            className="input-base min-h-[220px] p-5 pr-14 text-sm font-sans leading-relaxed bg-dark-950/20"
                            placeholder="Detail your engineering approach. State your structural strategy, outline data synchronization schemas, and address deployment risks..."
                            value={answerText}
                            onChange={handleTextChange}
                          />

                          {/* Waveform graphic when recording */}
                          {isRecording && (
                            <div className="absolute bottom-4 right-4 flex items-center gap-1">
                              <span className="w-1 h-3 bg-white opacity-40 animate-pulse" />
                              <span className="w-1 h-5 bg-white opacity-60 animate-pulse delay-75" />
                              <span className="w-1 h-4 bg-white opacity-80 animate-pulse delay-150" />
                              <span className="w-1 h-2 bg-white opacity-40 animate-pulse" />
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Action Buttons Panel */}
                      {error && (
                        <div className="rounded-lg border px-4 py-3 text-xs" style={{ borderColor: 'rgba(244, 63, 94, 0.3)', backgroundColor: 'rgba(244, 63, 94, 0.08)', color: 'var(--color-accent-coral)' }}>
                          {error}
                        </div>
                      )}
                      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                        <button
                          type="button"
                          onClick={toggleRecording}
                          className={`btn-base btn-secondary w-full sm:w-auto text-xs py-2.5 px-4 flex items-center justify-center gap-2 transition-colors ${
                            isRecording
                              ? 'border-rose-500/20 text-rose-400 bg-rose-500/5 hover:bg-rose-500/10'
                              : 'hover:border-white/20'
                          }`}
                          style={{
                            borderColor: isRecording ? 'rgba(244, 63, 94, 0.2)' : 'var(--color-border-subtle)',
                            color: isRecording ? 'var(--color-accent-coral)' : 'var(--color-text-primary)',
                            backgroundColor: isRecording ? 'rgba(244, 63, 94, 0.05)' : 'transparent',
                          }}
                        >
                          {isRecording ? (
                            <>
                              <MicOff className="w-4 h-4" />
                              <span>Stop Voice Input</span>
                            </>
                          ) : (
                            <>
                              <Mic className="w-4 h-4 opacity-75" />
                              <span>Start Voice Input</span>
                            </>
                          )}
                        </button>

                        <button
                          onClick={handleSubmitResponse}
                          disabled={!answerText.trim()}
                          className="btn-base btn-primary w-full sm:w-auto text-xs py-2.5 px-6 gap-2"
                        >
                          <span>Submit Response</span>
                          <Send className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Right part: Live Video / Audio feed simulation */}
            <div className="xl:col-span-4 space-y-4">
              <div className="card-premium p-4 bg-dark-900/10 border border-subtle flex flex-col justify-between" style={{ minHeight: '340px' }}>
                <div className="space-y-3">
                  <span className="text-[10px] uppercase font-bold tracking-widest text-dark-500 block" style={{ color: 'var(--color-text-tertiary)' }}>
                    Live Assessment Feed
                  </span>

                  {/* Video Box */}
                  <div className="relative aspect-video w-full rounded-lg bg-dark-950 overflow-hidden border border-subtle flex items-center justify-center" style={{ borderColor: 'var(--color-border-subtle)' }}>
                    {cameraActive && !videoMuted ? (
                      <video 
                        ref={videoRef} 
                        autoPlay 
                        playsInline 
                        muted 
                        className="w-full h-full object-cover transform -scale-x-100"
                      />
                    ) : (
                      <div className="flex flex-col items-center justify-center p-6 text-center space-y-2">
                        <div className="w-12 h-12 rounded-full bg-white/5 border border-white/10 flex items-center justify-center">
                          <Camera className="w-6 h-6 text-dark-400" style={{ color: 'var(--color-text-secondary)' }} />
                        </div>
                        <span className="text-xs font-semibold text-white">Camera Standby</span>
                        <span className="text-[9px]" style={{ color: 'var(--color-text-tertiary)' }}>
                          {videoMuted ? 'Video stream muted by candidate' : 'Enable camera permissions in browser for proctoring verification'}
                        </span>
                      </div>
                    )}

                    {/* Status Badge overlay */}
                    <div className="absolute top-2 left-2 px-2 py-0.5 bg-black/60 backdrop-blur rounded text-[8px] font-bold uppercase tracking-wider flex items-center gap-1.5 text-white">
                      <span className={`w-1.5 h-1.5 rounded-full ${cameraActive && !videoMuted ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
                      {cameraActive && !videoMuted ? 'REC LIVE' : 'FEED MUTED'}
                    </div>

                    {/* Microphone feedback bar overlay */}
                    {isRecording && (
                      <div className="absolute bottom-2 left-2 right-2 bg-black/40 backdrop-blur-sm p-1.5 rounded flex items-center gap-2">
                        <span className="text-[8px] font-bold text-white uppercase tracking-wider">AUDIO LEVEL</span>
                        <div className="flex-grow flex items-center gap-0.5 h-1">
                          <div className="h-full bg-emerald-400 animate-pulse" style={{ width: '10%' }} />
                          <div className="h-full bg-emerald-400 animate-pulse delay-75" style={{ width: '30%' }} />
                          <div className="h-full bg-emerald-400 animate-pulse delay-150" style={{ width: '50%' }} />
                          <div className="h-full bg-emerald-400 animate-pulse delay-300" style={{ width: '20%' }} />
                          <div className="h-full bg-emerald-400 animate-pulse" style={{ width: '40%' }} />
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Audio-Video Mute Toggles */}
                  <div className="flex items-center gap-2 pt-1">
                    <button
                      onClick={toggleVideoMute}
                      className="flex-grow btn-base btn-secondary !py-1.5 text-[10px] font-semibold gap-1.5"
                    >
                      {videoMuted ? (
                        <>
                          <VideoOff className="w-3.5 h-3.5 text-rose-400" />
                          <span>Unmute Camera</span>
                        </>
                      ) : (
                        <>
                          <Video className="w-3.5 h-3.5 text-white/80" />
                          <span>Mute Camera</span>
                        </>
                      )}
                    </button>

                    <button
                      onClick={toggleAudioMute}
                      className="flex-grow btn-base btn-secondary !py-1.5 text-[10px] font-semibold gap-1.5"
                    >
                      {audioMuted ? (
                        <>
                          <VolumeX className="w-3.5 h-3.5 text-rose-400" />
                          <span>Unmute Mic</span>
                        </>
                      ) : (
                        <>
                          <Volume2 className="w-3.5 h-3.5 text-white/80" />
                          <span>Mute Mic</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                <div className="border-t border-subtle pt-4 mt-4 text-[10px] space-y-2" style={{ borderColor: 'var(--color-border-subtle)' }}>
                  <span className="font-bold text-white uppercase tracking-wider block">AI Proctoring Status</span>
                  
                  <div className="space-y-1.5 text-[10px]" style={{ color: 'var(--color-text-secondary)' }}>
                    <div className="flex justify-between">
                      <span>Facial Alignment:</span>
                      <span className={cameraActive && !videoMuted ? 'text-emerald-400 font-semibold' : 'text-amber-400'}>
                        {cameraActive && !videoMuted ? 'Verified' : 'Pending Feed'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Ambient Noise:</span>
                      <span className="text-emerald-400 font-semibold">Low (Optimal)</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Identity Verification:</span>
                      <span className="text-emerald-400 font-semibold">Match 99.4%</span>
                    </div>
                    <div className="flex justify-between border-t border-white/5 pt-1 mt-1">
                      <span>Window Focus Loss:</span>
                      <span className={tabSwitches > 0 ? 'text-rose-400 font-bold animate-pulse' : 'text-emerald-400 font-semibold'}>
                        {tabSwitches} {tabSwitches === 1 ? 'Violation' : 'Violations'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>


      </div>
    </div>
  );
}
