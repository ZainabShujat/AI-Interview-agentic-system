# @hireintel/sdk

TypeScript SDK for the **HireIntel** agentic hiring platform.

Zero dependencies. Works in Node.js 18+ and modern browsers.

## Install

```bash
npm install @hireintel/sdk
```

## Quick Start

```typescript
import { HireIntel } from '@hireintel/sdk';

const client = new HireIntel({
  apiKey: process.env.HIREINTEL_API_KEY,
  baseUrl: 'http://localhost:8000',
});

// Parse a resume
const resume = await client.resumes.parse(pdfBuffer, { filename: 'cv.pdf' });

// Create a job blueprint
const jd = await client.jds.create({ text: 'Senior Python Engineer...' });

// Match
const match = await client.match.evaluate(resume.id, jd.id);
console.log(match.matchScore);        // 82
console.log(match.justifications);    // [{ type: 'success', text: '...' }]

// Interview
const session = await client.interview.start({ resume_id: resume.id, jd_id: jd.id });
const result  = await client.interview.submitAnswer({ ... });
const report  = await client.interview.getReport(session.interview_id);
```

## API Namespaces

| Namespace | Methods |
|-----------|---------|
| `client.resumes` | `parse()`, `batchParse()` |
| `client.jds` | `list()`, `create()`, `upload()`, `updateBlueprint()` |
| `client.match` | `evaluate()`, `evaluateRaw()` |
| `client.interview` | `start()`, `submitAnswer()`, `getReport()`, `getReportPdf()` |
| `client.reports` | `list()`, `generateRaw()` |
| `client.judge` | `evaluate()` |
| `client.roadmap` | `generate()` |

## Configuration

```typescript
const client = new HireIntel({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.hireintel.com',
  timeout: 30_000,
  retryMaxAttempts: 3,
  retryDelayMs: 1_000,
  debug: true,
  onRequest: (req) => console.log(`→ ${req.method} ${req.url}`),
  onResponse: (res) => console.log(`← ${res.status} (${res.durationMs}ms)`),
});
```

## Interceptors

```typescript
client.use(async (req, next) => {
  req.headers['X-Custom-Header'] = 'value';
  const res = await next(req);
  console.log(`${req.method} ${req.url} → ${res.status}`);
  return res;
});
```

## Error Handling

```typescript
import { HireIntel, NotFoundError, RateLimitError } from '@hireintel/sdk';

try {
  await client.match.evaluate('bad-id', 'bad-id');
} catch (err) {
  if (err instanceof NotFoundError) {
    console.log('Resource not found:', err.detail);
  } else if (err instanceof RateLimitError) {
    console.log(`Rate limited. Retry after ${err.retryAfterSeconds}s`);
  }
}
```

## Batch Resume Parsing

```typescript
const results = await client.resumes.batchParse([
  { file: pdf1, filename: 'alice.pdf' },
  { file: pdf2, filename: 'bob.pdf' },
], { concurrency: 5 });

results.forEach(r => {
  if ('error' in r) console.log(`Failed: ${r.filename}`);
  else console.log(`Parsed: ${r.parsed?.candidate_name}`);
});
```

## Interview Driver

Automates a full interview session with a callback for each question:

```typescript
import { HireIntel, driveInterview } from '@hireintel/sdk';

const session = await client.interview.start({ resume_id, jd_id });
const report = await driveInterview(client, session, async (ctx) => ({
  answer_text: await getAnswerFromUser(ctx.question),
  signals: { responseTime: 30000, latencySeconds: 2, wordCount: 100, wordsPerMinute: 130, fillerCount: 1 },
}));

console.log(report.overallScore);
```

## Build

```bash
npm run build      # Compile to dist/ (ESM + CJS)
npm run typecheck   # Type verification only
```

## License

MIT
