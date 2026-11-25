# Narrated Sprints walkthrough

The video replays terminal output captured from the Groq CLI. Windows text-to-speech provides English narration. The walkthrough uses the supplied learner CSV, the synthetic curriculum file, and fictional job openings. The learner's name is redacted in the video.

## 1. Setup

This is the Sprints multi-agent career and assessment orchestrator. One LangGraph workflow handles curriculum questions, Python submissions, learner records, and career matching. The setup imports twenty-five learner records, indexes one synthetic curriculum document in Chroma, and loads three fictional openings. Groq hosts the chat model, G P T O S S one hundred twenty B. Gemini creates the embeddings for curriculum search.

## 2. Curriculum Advisor

The learner asks how StateGraph routes Advisor and Assessor questions. The Advisor searches Chroma, checks the evidence, and cites the filename in its answer. Here the source explains that a conditional edge selects the Advisor for curriculum questions and the Assessor for code grading. The printed retrieval time covers both a Gemini query embedding and the vector search. This recorded call exceeds the one-second target.

## 3. Python Assessor

In the same learner session, the code command submits the sum-two exercise. Python REPL executes the submission and the rubric tests inside the Docker sandbox. All three tests pass and determine the score of one hundred. The model writes typed feedback, and a separate judge reviews it against the test evidence. The graph allows up to three feedback attempts. Starting the grading turn clears the Advisor retrieval timing.

## 4. Tier-one partner review

The learner now asks for a job match. SQLite checks progress, assessment score, employer preferences, and salary target against the seeded openings. The fixture returns a Fawry match. Because it is a tier-one opening in this demo, LangGraph pauses and presents the structured approval request. The shell asks for an explicit decision and reviewer ID before it resumes.

## 5. Resuming the recommendation

The reviewer enters yes and a simulated reviewer ID. LangGraph resumes from the checkpoint for the same learner. The recommendation includes the salary range stored in SQLite and labels the opening as a demo. Together, the pause and resume demonstrate the human approval gate. A placement pilot needs verified openings and authenticated staff reviewers.

## 6. Learner records

The learner asks for completed modules, target salary, and preferred employers. The ReAct message trace shows that Groq invoked the authorized learner-record tool. A parameterized, read-only SQLite query returns twelve completed modules and a salary target of thirty thousand Egyptian pounds. The Python grade here comes from the stored learner record. The earlier grade came from the exercise submitted during this session.

## 7. Grading with Docker unavailable

A separate shell runs the same submission with Docker removed from that process's search path. The Assessor reports unable to verify and names the Docker Python REPL tool in the structured failure. The application withholds the grade. Learner code has no host execution fallback.

## 8. Verification and rollout

Twelve automated tests pass, including a curriculum request followed by assessment on the same learner thread. A separate test covers the timing reset after a failed route. The verification notes record the full retrieval latency and an earlier warm Chroma lookup benchmark. A pilot needs official course material, verified openings, durable checkpoints, staff authentication, and a larger latency benchmark.
