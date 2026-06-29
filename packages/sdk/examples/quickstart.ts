// ─────────────────────────────────────────────────────────────────────────────
// @hireintel/sdk — Quickstart Example
//
// Run: npx tsx examples/quickstart.ts
// Requires: HireIntel backend running on http://localhost:8000
// ─────────────────────────────────────────────────────────────────────────────

import { HireIntel, driveInterview } from '../src/index.js';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

async function main() {
  // 1. Initialize client
  const client = new HireIntel({
    baseUrl: 'http://localhost:8000',
    debug: true,
  });

  // Register a logging interceptor
  client.use(async (req, next) => {
    const start = Date.now();
    const res = await next(req);
    console.log(`  ⏱ ${req.method} ${req.url} → ${res.status} (${Date.now() - start}ms)`);
    return res;
  });

  // 2. Health check
  console.log('\n── Health Check ──');
  const health = await client.healthCheck();
  console.log(`  Status: ${health.status}`);
  console.log(`  Version: ${health.version}`);

  // 3. Parse a resume (provide your own PDF path)
  console.log('\n── Resume Parse ──');
  const pdfPath = resolve(process.cwd(), 'test-resume.pdf');
  let resumeId: string;
  try {
    const pdfBuffer = readFileSync(pdfPath);
    const resume = await client.resumes.parse(pdfBuffer, { filename: 'test-resume.pdf' });
    resumeId = resume.id;
    console.log(`  ID: ${resume.id}`);
    console.log(`  Candidate: ${resume.parsed?.candidate_name}`);
    console.log(`  Skills: ${resume.parsed?.skills.slice(0, 5).join(', ')}`);
    console.log(`  Cached: ${resume.telemetry?.cached}`);
  } catch (err) {
    console.log('  ⚠ No test-resume.pdf found — skipping resume parse');
    console.log('  Place a test-resume.pdf in the examples/ directory to test');
    return;
  }

  // 4. Create a JD
  console.log('\n── JD Create ──');
  const jd = await client.jds.create({
    text: `
      Senior Full Stack Engineer
      5+ years experience with React, Node.js, TypeScript
      Experience with PostgreSQL, Redis, Docker
      Healthcare or fintech domain preferred
      Leadership experience managing 2-3 engineers
    `,
  });
  console.log(`  JD ID: ${jd.id}`);

  // 5. Match
  console.log('\n── Match Evaluate ──');
  const match = await client.match.evaluate(resumeId, jd.id);
  console.log(`  Score: ${match.matchScore}`);
  console.log(`  Justifications: ${match.justifications.length}`);
  match.justifications.slice(0, 3).forEach((j) => {
    console.log(`    ${j.type === 'success' ? '✓' : '△'} ${j.text}`);
  });

  // 6. Start interview and answer one question
  console.log('\n── Interview Start ──');
  const session = await client.interview.start({
    resume_id: resumeId,
    jd_id: jd.id,
  });
  console.log(`  Interview ID: ${session.interview_id}`);
  console.log(`  First question: ${session.question.slice(0, 80)}...`);
  console.log(`  Category: ${session.category}`);

  // Submit a single answer
  console.log('\n── Submit Answer ──');
  const result = await client.interview.submitAnswer({
    interview_id: session.interview_id,
    question_text: session.question,
    category: session.category,
    answer_text: 'I would approach this by first analyzing the requirements, then designing a scalable architecture using microservices with TypeScript and Node.js, ensuring proper error handling and monitoring.',
    signals: {
      responseTime: 35000,
      latencySeconds: 2.5,
      wordCount: 28,
      wordsPerMinute: 130,
      fillerCount: 0,
    },
  });
  console.log(`  Finished: ${result.finished}`);
  if (!result.finished) {
    console.log(`  Next question: ${result.question.slice(0, 80)}...`);
  }

  // 7. List reports
  console.log('\n── Reports List ──');
  const reports = await client.reports.list();
  console.log(`  Total reports: ${reports.length}`);
  reports.slice(0, 3).forEach((r) => {
    console.log(`    ${r.candidate_name} — ${r.score} — ${r.recommendation}`);
  });

  console.log('\n✅ Quickstart complete');
}

main().catch(console.error);
