import axios from 'axios';

// The base URL relies on the Vite proxy in development (/api)
// or can be explicitly set for production.
const api = axios.create({
  baseURL: '/',
  headers: {
    'Content-Type': 'application/json'
  }
});

// ==========================================
// RESUME AGENT
// ==========================================
export const uploadResume = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/api/resume', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return data;
};

// ==========================================
// JD AGENT
// ==========================================
export const listJds = async () => {
  const { data } = await api.get('/api/jd');
  return data;
};

export const uploadJdText = async (payload: any) => {
  const { data } = await api.post('/api/jd', payload);
  return data;
};

export const uploadJdFile = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/api/jd/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return data;
};

export const updateJdBlueprint = async (jdId: string, blueprint: any) => {
  const { data } = await api.put(`/api/jd/${jdId}/blueprint`, { blueprint });
  return data;
};

// ==========================================
// READINESS MATCH AGENT
// ==========================================
export const matchResumeJd = async (payload: any) => {
  const { data } = await api.post('/api/match', payload);
  return data;
};

export const rawMatchResumeJd = async (payload: any) => {
  const { data } = await api.post('/api/match/raw', payload);
  return data;
};

// ==========================================
// INTERVIEW & JUDGE AGENTS
// ==========================================
export const startInterview = async (payload: any) => {
  const { data } = await api.post('/api/interview/start', payload);
  return data;
};

export const startAutonomousInterview = async (payload: any) => {
  const { data } = await api.post('/api/interview/start-autonomous', payload);
  return data;
};

export const submitInterviewAnswer = async (payload: any) => {
  const { data } = await api.post('/api/interview/answer', payload);
  return data;
};

export const submitAudioAnswer = async (formData: FormData) => {
  const { data } = await api.post('/api/interview/audio-answer', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return data;
};

export const getInterviewReport = async (interviewId: string) => {
  const { data } = await api.get(`/api/interview/report?interview_id=${interviewId}`);
  return data;
};

export const downloadReportPdf = async (interviewId: string) => {
  const { data } = await api.get(`/api/interview/report/pdf?interview_id=${interviewId}`, {
    responseType: 'blob'
  });
  return data;
};

export const listInterviewReports = async () => {
  const { data } = await api.get('/api/interview/reports');
  return data;
};

export const judgeAnswer = async (payload: any) => {
  const { data } = await api.post('/api/interview/judge', payload);
  return data;
};

export const generateRawReport = async (payload: any) => {
  const { data } = await api.post('/api/interview/report/raw', payload);
  return data;
};

// ==========================================
// ROADMAP / PLANNER AGENT
// ==========================================
export const getCareerRoadmap = async (payload: any) => {
  const { data } = await api.post('/api/roadmap', payload);
  return data;
};

// ==========================================
// SCHEDULING AGENT
// ==========================================
export const scheduleMeeting = async (payload: any) => {
  const { data } = await api.post('/api/schedule', payload);
  return data;
};

export const listScheduledMeetings = async (email?: string) => {
  const url = email ? `/api/schedule/meetings?email=${email}` : '/api/schedule/meetings';
  const { data } = await api.get(url);
  return data;
};

export const getMeeting = async (meetingId: string) => {
  const { data } = await api.get(`/api/schedule/${meetingId}`);
  return data;
};

export const cancelMeeting = async (meetingId: string) => {
  const { data } = await api.delete(`/api/schedule/${meetingId}`);
  return data;
};

export const rescheduleMeeting = async (meetingId: string, payload: any) => {
  const { data } = await api.post(`/api/schedule/${meetingId}/reschedule`, payload);
  return data;
};

// ==========================================
// WORKFLOW / ORCHESTRATOR
// ==========================================
export const submitWorkflowSlots = async (payload: any) => {
  const { data } = await api.post('/workflow/submit-slots', payload);
  return data;
};

export const getWorkflowStatus = async (interviewId: string) => {
  const { data } = await api.get(`/workflow/status/${interviewId}`);
  return data;
};

export const testOrchestrator = async (payload: any) => {
  const { data } = await api.post('/workflow/test-orchestrator', payload);
  return data;
};

export default api;
