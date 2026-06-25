import { useState, createContext, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import RoleReadiness from './pages/RoleReadiness';
import Interview from './pages/Interview';
import Report from './pages/Report';

// Define a simple context to store session/upload data
interface SessionContextType {
  resumeId: string | null;
  setResumeId: (id: string | null) => void;
  jdId: string | null;
  setJdId: (id: string | null) => void;
  interviewId: string | null;
  setInterviewId: (id: string | null) => void;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
}

export default function App() {
  const [resumeId, setResumeId] = useState<string | null>(null);
  const [jdId, setJdId] = useState<string | null>(null);
  const [interviewId, setInterviewId] = useState<string | null>(null);

  return (
    <SessionContext.Provider value={{ resumeId, setResumeId, jdId, setJdId, interviewId, setInterviewId }}>
      <Router>
        <div className="page-wrapper min-h-screen flex flex-col" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
          <Header />
          <main className="main-content flex-grow pt-24 pb-16">
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/upload" element={<Upload />} />
              <Route path="/match" element={<RoleReadiness />} />
              <Route path="/interview" element={<Interview />} />
              <Route path="/report" element={<Report />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </Router>
    </SessionContext.Provider>
  );
}
