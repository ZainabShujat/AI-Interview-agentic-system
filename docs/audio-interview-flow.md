# Audio Interview Agent Architecture & Flow

This document details the newly integrated Audio Interview workflow, explaining how the core orchestrator, the speech services, and the Interview Agent evaluate a candidate's spoken responses in real-time.

---

## The Workflow Architecture

The Audio Interview loop acts as an infinite state machine that continues asking questions and evaluating spoken responses until the candidate completes all categories in their targeted roadmap.

### 1. The Client-Side Trigger
When the candidate finishes speaking into their microphone, the frontend application packages the raw audio recording (e.g., as a `.wav` file) and compiles metadata into a `multipart/form-data` payload. 

This payload is sent to the new endpoint:
`POST /api/interview/audio-answer`

It includes:
*   `audio_file`: The raw bytes of the user's spoken answer.
*   `interview_id`: The database UUID tracking this specific session.
*   `question_text`: The question the agent just asked.
*   `category`: The current roadmap category (e.g., Technical, Behavioral).
*   `signals`: Frontend telemetry (like face visibility, latency).

---

## 2. Speech-to-Text Transcription & Telemetry

Before the AI Judge can evaluate the response, the system must transform the acoustic payload into actionable text.

*   **Deepgram API (Speech Service):** The `audio_file` bytes are routed immediately to the `speech_service.transcribe_audio()` function. Using the Deepgram Nova-2 model, it transcribes the speech into text with incredibly low latency.
*   **Acoustic Telemetry:** Simultaneously, the `speech_service.analyze_voice_features()` module inspects the raw audio bytes to extract acoustic metadata—such as `speakingRate`, `jitter`, `energy`, and `pitchVariance`.
*   **Signal Merging:** These acoustic metrics are combined with the frontend telemetry to create a comprehensive `signals_dict` that paints a complete picture of the candidate's confidence and delivery.

---

## 3. The Judge Agent Evaluation

With the text transcript and the rich telemetry signals in hand, the orchestrator invokes the generative AI model via `gemini_service.judge_answer()`.

The Judge Agent evaluates the transcript against three strict rubrics:
1.  **Accuracy:** Was the answer technically correct?
2.  **Depth:** Did the candidate provide sufficient detail, or was the answer superficial?
3.  **Communication:** Measured partially by the transcript structure and augmented heavily by the acoustic telemetry (speaking rate, jitter).

The Judge Agent returns a structured JSON evaluation scoring the candidate out of 100 for each rubric.

---

## 4. Adaptive Difficulty & State Machine Logic

Once the Judge Agent evaluates the answer, the orchestrator updates the database and determines what happens next.

*   **Memory Update:** The `Memory Agent` reads the new evaluation and updates the candidate's active profile (e.g., noting newly discovered weak skills or strong competencies).
*   **Follow-Up Logic:** If the Judge Agent scored the candidate's `depth` below 60 or `communication` below 50, the orchestrator triggers a follow-up loop. Instead of advancing to the next category, it instructs the AI to probe deeper into the exact same topic.
*   **Adaptive Difficulty:** The orchestrator averages the scores of the candidate's last two answers. 
    *   If the average > 85, the difficulty escalates to `Hard`.
    *   If the average < 70, the difficulty reduces to `Easy`.

---

## 5. Generating the Next Response

Finally, the orchestrator looks at the candidate's roadmap queue to see what category comes next. 

It invokes `gemini_service.generate_question()` passing in the candidate's historical context, the newly calculated difficulty level, and the specific memory context. The AI generates the next conversational question to ask the candidate.

This question is returned to the frontend as JSON, ready to be synthesized into voice by the frontend's Text-to-Speech client, completely restarting the loop.
