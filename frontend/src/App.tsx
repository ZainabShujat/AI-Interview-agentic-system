import { useState, createContext, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import StudentAssessment from './pages/StudentAssessment';
import RoleReadiness from './pages/RoleReadiness';
import Interview from './pages/Interview';
import Report from './pages/Report';
import JobLeaderboard from './pages/JobLeaderboard';
import Login from './pages/Login';

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

// Role guard wrappers
function RecruiterRoute({ children }: { children: React.ReactNode }) {
  const role = localStorage.getItem('user_role');
  if (!role) {
    return <Navigate to="/login?role=recruiter" replace />;
  }
  if (role !== 'recruiter') {
    return <Navigate to="/student" replace />;
  }
  return <>{children}</>;
}

function StudentRoute({ children }: { children: React.ReactNode }) {
  const role = localStorage.getItem('user_role');
  if (!role) {
    return <Navigate to="/login?role=student" replace />;
  }
  if (role !== 'student') {
    return <Navigate to="/recruiter" replace />;
  }
  return <>{children}</>;
}

function CommonRoute({ children }: { children: React.ReactNode }) {
  const role = localStorage.getItem('user_role');
  if (!role) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
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
              <Route path="/login" element={<Login />} />
              
              {/* Student Portal Routes */}
              <Route path="/student" element={<StudentRoute><StudentAssessment /></StudentRoute>} />
              <Route path="/student/readiness" element={<StudentRoute><RoleReadiness /></StudentRoute>} />
              <Route path="/student/leaderboard" element={<StudentRoute><JobLeaderboard /></StudentRoute>} />
              <Route path="/assessment/take/:jdId" element={<StudentRoute><StudentAssessment /></StudentRoute>} />
              
              {/* Recruiter Portal Routes */}
              <Route path="/recruiter" element={<RecruiterRoute><Dashboard /></RecruiterRoute>} />
              <Route path="/recruiter/create" element={<RecruiterRoute><Upload /></RecruiterRoute>} />
              <Route path="/recruiter/report" element={<RecruiterRoute><Report /></RecruiterRoute>} />
              
              <Route path="/dashboard" element={<Navigate to="/recruiter" replace />} />
              <Route path="/upload" element={<Navigate to="/student" replace />} />
              <Route path="/match" element={<Navigate to="/student/readiness" replace />} />
              
              {/* Common protected session routes */}
              <Route path="/interview" element={<CommonRoute><Interview /></CommonRoute>} />
              <Route path="/report" element={<CommonRoute><Report /></CommonRoute>} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </Router>
    </SessionContext.Provider>
  );
}
