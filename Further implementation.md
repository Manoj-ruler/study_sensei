StudySensei 2.0 – Full Implementation Guide

From “Good RAG App” → “Serious AI Learning Platform”

Tech stack (same as yours):

Frontend: Next.js 14 (App Router), TypeScript, Tailwind, Lucide

Backend: FastAPI, Python

Database: Supabase Postgres (+ pgvector)

Auth: Supabase Auth

Storage: Supabase Storage

AI: Gemini 1.5 Flash, sentence-transformers/all-MiniLM-L6-v2

Infra: Docker + Docker Compose

New Extras: Background worker, code execution engine, multi-agent mentor, analytics

0. Where You Are Right Now (Baseline)

You already have: 

project_document

Auth (Supabase)

Skills (topics)

PDF upload to Supabase Storage

Back-end text extraction + chunking

Embeddings using MiniLM → stored in document_chunks with pgvector

Chat using RAG (/chat/message)

Quiz generation + storage (quizzes, quiz_questions)

API endpoints:

POST /documents/upload

DELETE /documents/{id}

POST /chat/message

DELETE /chat/{chat_id}

POST /quiz/generate

POST /quiz/save

We keep all of this and add layers on top.

1. Project Structure (High-Level)

Suggested folder structure:

study-sensei/
  frontend/        # Next.js
  backend/         # FastAPI main app
  worker/          # Background tasks (doc processing, reminders)
  code_runner/     # (optional) Dockerized code execution environment
  docker-compose.yml
  README.md


Inside backend/:

backend/
  app/
    __init__.py
    main.py
    api/
      __init__.py
      documents.py
      chat.py
      quiz.py
      mentor.py        # multi-agent endpoints
      solver.py        # code execution endpoints
      analytics.py     # progress dashboards
    core/
      config.py        # env loading
      db.py            # DB connection
      auth.py          # Supabase JWT validation
      ai.py            # Gemini + embeddings + routing logic
      rag.py           # RAG pipeline helpers
    models/
      # SQLAlchemy models if you use ORM (optional)
    schemas/
      # Pydantic schemas for request/response


Inside worker/:

worker/
  worker_main.py  # background tasks
  requirements.txt

2. Dockerize the Whole System

Goal: run frontend, backend, and db with one command:

docker-compose up --build

2.1 Backend Dockerfile

Create backend/Dockerfile:

FROM python:3.11-slim

WORKDIR /app

# System dependencies (for pypdf, sentence-transformers, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


Make sure backend/requirements.txt includes at least:

fastapi
uvicorn[standard]
python-dotenv
requests
pydantic
sentence-transformers
pypdf
supabase-py
psycopg2-binary
sqlalchemy
langchain

2.2 Frontend Dockerfile

Create frontend/Dockerfile:

FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]


Make sure package.json has "start": "next start" script.

2.3 docker-compose.yml

At project root:

version: "3.9"

services:
  db:
    image: postgres:15
    container_name: study_db
    restart: always
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: studysensei
    ports:
      - "5432:5432"
    volumes:
      - db_data:/var/lib/postgresql/data
    command: ["postgres", "-c", "shared_preload_libraries=vector"]

  backend:
    build: ./backend
    container_name: study_backend
    restart: always
    depends_on:
      - db
    environment:
      DB_HOST: db
      DB_PORT: 5432
      DB_NAME: studysensei
      DB_USER: postgres
      DB_PASSWORD: postgres
      SUPABASE_URL: your_supabase_url
      SUPABASE_KEY: your_supabase_service_role_key
      GOOGLE_API_KEY: your_gemini_key
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    container_name: study_frontend
    restart: always
    depends_on:
      - backend
    environment:
      NEXT_PUBLIC_BACKEND_URL: "http://localhost:8000"
      NEXT_PUBLIC_SUPABASE_URL: your_supabase_url
      NEXT_PUBLIC_SUPABASE_ANON_KEY: your_supabase_anon_key
    ports:
      - "3000:3000"

  worker:
    build: ./worker
    container_name: study_worker
    restart: always
    depends_on:
      - backend
      - db
    environment:
      DB_HOST: db
      DB_PORT: 5432
      DB_NAME: studysensei
      DB_USER: postgres
      DB_PASSWORD: postgres
      SUPABASE_URL: your_supabase_url
      SUPABASE_KEY: your_supabase_service_role_key

volumes:
  db_data:


🔹 You are still using Supabase’s managed Postgres for prod; this db is optional for local dev.
If using Supabase DB only, you can remove db and just point backend & worker to Supabase.

3. Background Worker – Document Processing

Right now, your upload endpoint probably:

Receives file

Uploads to Supabase Storage

Extracts text

Chunks

Embeds

Inserts chunks

This is heavy and blocks the request.

We change to:

Upload endpoint:

Only:

Save metadata in documents

Mark status = 'pending'

Worker:

Periodically scans DB for status = 'pending'

Processes them

Marks status = 'ready'

3.1 DB: Add Fields

In documents table, add:

status (text): 'pending' | 'processing' | 'ready' | 'failed'

error_message (text, nullable)

Example migration (Supabase SQL):

ALTER TABLE documents
ADD COLUMN status text NOT NULL DEFAULT 'pending',
ADD COLUMN error_message text;

3.2 Modify Upload Endpoint (/documents/upload)

Pseudocode (FastAPI):

# app/api/documents.py

@router.post("/documents/upload")
async def upload_document(
    skill_id: str,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    # 1. Upload file to Supabase Storage
    storage_path = f"{user.id}/{skill_id}/{file.filename}"

    supabase.storage.from_("documents").upload(
        storage_path, file.file
    )

    # 2. Insert into documents table with status 'pending'
    doc = {
        "user_id": user.id,
        "skill_id": skill_id,
        "filename": file.filename,
        "storage_path": storage_path,
        "status": "pending",
    }

    # Insert with supabase client OR sqlalchemy

    return {"message": "Uploaded successfully. Processing will start soon."}


Don’t call embedding code here anymore.

3.3 Worker Service

In worker/worker_main.py:

import time
import os
from supabase import create_client
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
import psycopg2

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

conn = psycopg2.connect(
    host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
)
conn.autocommit = True

def fetch_pending_documents():
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, storage_path FROM documents WHERE status = 'pending' LIMIT 5"
        )
        return cur.fetchall()

def update_document_status(doc_id, status, error=None):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE documents SET status = %s, error_message = %s WHERE id = %s",
            (status, error, doc_id),
        )

def process_document(doc_id, storage_path):
    try:
        update_document_status(doc_id, "processing")

        # 1. download file from Supabase
        bucket = supabase.storage.from_("documents")
        res = bucket.download(storage_path)
        pdf_bytes = res  # depends on SDK; may need res.content

        with open("/tmp/tmp.pdf", "wb") as f:
            f.write(pdf_bytes)

        # 2. extract text
        reader = PdfReader("/tmp/tmp.pdf")
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"

        # 3. chunk text (simple split by N chars)
        chunks = []
        chunk_size = 1000
        for i in range(0, len(full_text), chunk_size):
            chunks.append(full_text[i : i + chunk_size])

        # 4. embed each chunk
        embeddings = model.encode(chunks).tolist()

        # 5. insert into document_chunks
        with conn.cursor() as cur:
            for idx, (text, emb) in enumerate(zip(chunks, embeddings)):
                cur.execute(
                    """
                    INSERT INTO document_chunks (document_id, chunk_index, content, embedding)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (doc_id, idx, text, emb),
                )

        update_document_status(doc_id, "ready")
    except Exception as e:
        update_document_status(doc_id, "failed", str(e))

def main_loop():
    while True:
        docs = fetch_pending_documents()
        if not docs:
            time.sleep(5)
            continue

        for doc_id, storage_path in docs:
            process_document(doc_id, storage_path)

if __name__ == "__main__":
    main_loop()


This is not “beautiful scalable worker” but is totally fine and shows you understand async offline processing.

3.4 Frontend UI for Status

In your document list page, poll /documents endpoint every few seconds and show:

Pending – yellow

Processing – orange

Ready – green

Failed – red (with tooltip of error_message)

This gives a very “cloud product” feel.

4. Problem-Solving Engine (Code Execution)

Goal: Let users:

Get coding questions generated from their documents.

Write code (e.g., in Python).

Run code safely.

Get result: Passed/Failed + explanation.

4.1 New Tables

Add:

CREATE TABLE coding_questions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  skill_id uuid REFERENCES skills(id),
  user_id uuid REFERENCES profiles(id),
  question_text text NOT NULL,
  input_format text,
  output_format text,
  difficulty text,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE test_cases (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  question_id uuid REFERENCES coding_questions(id) ON DELETE CASCADE,
  input text NOT NULL,
  expected_output text NOT NULL
);

CREATE TABLE code_submissions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  question_id uuid REFERENCES coding_questions(id),
  user_id uuid REFERENCES profiles(id),
  language text NOT NULL,
  code text NOT NULL,
  passed boolean,
  result_message text,
  created_at timestamptz DEFAULT now()
);

4.2 Generate Coding Question (Backend)

Endpoint: POST /solver/generate-question

Pseudocode:

# app/api/solver.py

@router.post("/solver/generate-question")
async def generate_question(skill_id: str, user=Depends(get_current_user)):
    """
    1. Fetch top chunks for this skill.
    2. Ask LLM: create 1 coding problem from these concepts.
    3. Also ask it to suggest 2-3 sample test cases.
    4. Save in coding_questions + test_cases.
    """
    # 1. query chunks related to skill
    chunks = get_chunks_for_skill(skill_id)  # your own helper

    context = "\n\n".join([c.content for c in chunks[:5]])

    prompt = f"""
You are a coding problem generator.

Context (topics, explanation):
{context}

Create ONE programming problem in Python for students. Output JSON ONLY in this format:
{{
  "question": "...",
  "input_format": "...",
  "output_format": "...",
  "test_cases": [
    {{ "input": "...", "expected_output": "..." }},
    {{ "input": "...", "expected_output": "..." }}
  ]
}}
"""

    llm_response = call_gemini(prompt)  # implement in app/core/ai.py

    data = json.loads(llm_response)

    # Insert into coding_questions + test_cases tables
    # ...

    return {"question_id": q_id, "question": data["question"], "test_cases": data["test_cases"]}

4.3 Code Execution (Safely)

You must not run user code directly in backend process.

Simplest safe demo approach (for project-level, not for real prod):

In code_runner/, you create a tiny Python image that:

Reads code + input from files/env

Runs it inside container

Captures stdout

code_runner/Dockerfile:

FROM python:3.11-slim
WORKDIR /runner
COPY run_code.py .
CMD ["python", "run_code.py"]


code_runner/run_code.py (simplified):

import subprocess
import os
from textwrap import dedent

code = os.environ.get("USER_CODE", "")
test_input = os.environ.get("TEST_INPUT", "")

with open("user_code.py", "w") as f:
    f.write(code)

try:
    result = subprocess.run(
        ["python", "user_code.py"],
        input=test_input.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=2
    )
    print("STDOUT::" + result.stdout.decode())
    print("STDERR::" + result.stderr.decode())
except Exception as e:
    print("ERROR::" + str(e))


In backend, to execute:

import docker  # pip install docker

client = docker.from_env()

def run_code_in_docker(code: str, test_input: str):
    container = client.containers.run(
        "study_sensei_code_runner",  # image name you build
        environment={
            "USER_CODE": code,
            "TEST_INPUT": test_input,
        },
        detach=True,
    )
    logs = container.logs(timeout=5).decode()
    container.remove()
    return logs

4.4 Endpoint: Submit Code

POST /solver/submit

@router.post("/solver/submit")
async def submit_code(body: SubmitCodeSchema, user=Depends(get_current_user)):
    """
    body:
      question_id
      language (we'll support 'python')
      code
    """
    # 1. Fetch test cases from DB
    test_cases = get_test_cases(body.question_id)

    all_passed = True
    result_message = ""

    for tc in test_cases:
        logs = run_code_in_docker(body.code, tc.input)
        stdout_line = extract_stdout(logs)
        if stdout_line.strip() != tc.expected_output.strip():
            all_passed = False
            result_message += f"Failed for input {tc.input}. Expected {tc.expected_output}, got {stdout_line}\n"

    # Store submission
    save_submission(...)

    return {
        "passed": all_passed,
        "details": result_message if not all_passed else "All test cases passed!"
    }


Frontend side: simple code editor (textarea) + run button.

5. Multi-Agent Mentor System

Currently, you have /chat/message that does RAG and returns an answer.

We want to upgrade to a more “mentor-style” system with modes / agents:

Explain Mode – Teacher agent

Quiz Me Mode – Examiner agent

Plan Mode – Planner agent (study schedule)

Coach Mode – Motivator agent

You can implement this without any extra library by:

Accepting a mode parameter in the API.

Using different prompts for each mode.

5.1 New Endpoint: /mentor/message

POST /mentor/message

{
  "skill_id": "uuid",
  "mode": "explain" | "quiz" | "plan" | "coach",
  "message": "I want to master joins in SQL"
}

5.2 Orchestrator in Backend
# app/api/mentor.py

@router.post("/mentor/message")
async def mentor_message(body: MentorMessageSchema, user=Depends(get_current_user)):
    if body.mode == "explain":
        return await handle_explain_mode(body, user)
    elif body.mode == "quiz":
        return await handle_quiz_mode(body, user)
    elif body.mode == "plan":
        return await handle_plan_mode(body, user)
    elif body.mode == "coach":
        return await handle_coach_mode(body, user)
    else:
        raise HTTPException(status_code=400, detail="Invalid mode")

5.3 Teacher Agent (Explain Mode + RAG)
async def handle_explain_mode(body, user):
    # 1. Use RAG to get relevant chunks for this skill + question
    chunks = retrieve_relevant_chunks(body.skill_id, body.message)

    context = "\n\n".join([c.content for c in chunks])

    prompt = f"""
You are a friendly TEACHER.

Use ONLY the context below to explain clearly.

Context:
{context}

User's question:
{body.message}

Explain step by step.
At the end, list 3 practice questions about this topic.
"""

    answer = call_gemini(prompt)
    return {"role": "assistant", "content": answer}

5.4 Examiner Agent (Quiz Mode)
async def handle_quiz_mode(body, user):
    # Same as your quiz generation but more conversational:
    chunks = retrieve_relevant_chunks(body.skill_id, body.message)
    context = "\n\n".join([c.content for c in chunks])

    prompt = f"""
You are an EXAMINER.

From the following context, generate 5 multiple-choice questions.

Context:
{context}

Output JSON ONLY:
[
  {{
    "question": "...",
    "options": ["A", "B", "C", "D"],
    "correct_index": 1,
    "explanation": "..."
  }},
  ...
]
"""

    response = call_gemini(prompt)
    questions = json.loads(response)

    # Optionally save them in quiz tables

    return {"mode": "quiz", "questions": questions}

5.5 Planner Agent (Study Plan)
async def handle_plan_mode(body, user):
    """
    Input message: "I have 10 days to learn SQL from these docs"
    """

    chunks = get_overview_chunks_for_skill(body.skill_id)
    context = "\n\n".join([c.content for c in chunks])

    prompt = f"""
You are a STUDY PLANNER.

User: {body.message}

Context about what they need to learn:
{context}

Create a day-by-day study plan in simple bullet points with tasks for each day.
"""

    answer = call_gemini(prompt)
    return {"mode": "plan", "plan": answer}

5.6 Coach Agent (Motivator)
async def handle_coach_mode(body, user):
    """
    No need for RAG here. Just motivational guidance.
    """
    prompt = f"""
You are a MOTIVATION COACH.

User says:
{body.message}

Reply with short, practical, encouraging advice in 5-8 lines.
"""

    answer = call_gemini(prompt)
    return {"mode": "coach", "message": answer}

5.7 Frontend

On the chat page:

Add a mode selector (tabs or dropdown):

Explain | Quiz | Plan | Coach

Send the selected mode in the request.

Render UI differently based on mode:

For quiz: show MCQ UI.

For plan: show nicely formatted schedule.

This gives a clear “multi-agent” UX without complex libs.

6. Analytics & Progress Tracking

We now want to show a dashboard:

Your accuracy by topic.

How many quizzes you completed.

Your improvement over time.

6.1 New Table: progress_metrics
CREATE TABLE progress_metrics (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id),
  skill_id uuid REFERENCES skills(id),
  topic text NOT NULL,
  total_questions int DEFAULT 0,
  correct_questions int DEFAULT 0,
  last_updated timestamptz DEFAULT now()
);

6.2 Updating Progress After Quiz

When you save quiz results (/quiz/save):

Each question should have a topic field (you can:

Add a dropdown in UI, or

Let AI tag each question with topic using LLM).

Then, after each question:

def update_progress(user_id, skill_id, topic, correct: bool):
    # check if row exists
    row = fetch_progress(user_id, skill_id, topic)
    if row:
        row.total_questions += 1
        if correct:
            row.correct_questions += 1
    else:
        # insert new row
        ...


Call this for each question.

6.3 API: Get Analytics for Skill

GET /analytics/skill/{skill_id}

Returns:

{
  "skill_id": "uuid",
  "topics": [
    {
      "topic": "Joins",
      "total": 10,
      "correct": 7,
      "accuracy": 70
    },
    ...
  ],
  "overall_accuracy": 65,
  "quizzes_taken": 5
}


Backend pseudocode:

@router.get("/analytics/skill/{skill_id}")
async def get_skill_analytics(skill_id: str, user=Depends(get_current_user)):
    rows = fetch_progress_rows(user.id, skill_id)

    topics_data = []
    total_correct = 0
    total_questions = 0

    for r in rows:
        acc = (r.correct_questions / r.total_questions) * 100 if r.total_questions else 0
        topics_data.append({
            "topic": r.topic,
            "total": r.total_questions,
            "correct": r.correct_questions,
            "accuracy": acc
        })
        total_questions += r.total_questions
        total_correct += r.correct_questions

    overall_accuracy = (total_correct / total_questions) * 100 if total_questions else 0

    # Maybe count quizzes from quizzes table
    quizzes_taken = count_quizzes(user.id, skill_id)

    return {
        "skill_id": skill_id,
        "topics": topics_data,
        "overall_accuracy": overall_accuracy,
        "quizzes_taken": quizzes_taken
    }

6.4 Frontend: Dashboard Graphs

Use recharts:

npm install recharts


Example bar chart for topic accuracy:

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const TopicAccuracyChart = ({ data }) => (
  <ResponsiveContainer width="100%" height={300}>
    <BarChart data={data}>
      <XAxis dataKey="topic" />
      <YAxis />
      <Tooltip />
      <Bar dataKey="accuracy" />
    </BarChart>
  </ResponsiveContainer>
);


Call /analytics/skill/{id}, pass response topics into this component.

Show in /skills/[id]/analytics page.

7. Optional: Knowledge Graph (Lightweight Version)

If you have time and energy, do this. If not, skip.

7.1 Minimal Approach (Inside Postgres)

Instead of Neo4j, you can:

CREATE TABLE concepts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  skill_id uuid REFERENCES skills(id),
  name text NOT NULL
);

CREATE TABLE concept_relations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  from_concept uuid REFERENCES concepts(id),
  to_concept uuid REFERENCES concepts(id),
  relation_type text  -- e.g., 'prerequisite', 'related'
);

7.2 Extracting Concepts Using AI

When processing documents (in worker), after embeddings:

Call LLM with text and ask:

“Extract main concepts as a JSON list of strings.”

Insert each into concepts table (if not exists).

For relationships, you can manually define a few, or ask LLM:

“For this list of concepts, define prerequisites: output pairs (A → B).”

This is optional but looks super advanced.

7.3 Frontend: Visual Graph

Use a simple force-graph component (like react-force-graph) to display nodes and edges.

You don’t need fancy logic. Even a static graph view is enough for “wow factor”.

8. Security & Config – Make It Clean

Validate Supabase JWT in all protected routes.

Strictly filter DB rows by user_id.

Ensure code execution never touches host filesystem.

Keep all secrets in .env or environment, never in git.

9. Development & Execution Flow
Running Locally (without Docker)

Backend:

cd backend
uvicorn app.main:app --reload --port 8000


Worker:

cd worker
python worker_main.py


Frontend:

cd frontend
npm run dev

Running With Docker (Recommended for Demo)
docker-compose up --build


Then open:

http://localhost:3000 → frontend

http://localhost:8000/docs → backend Swagger

10. What You End Up With

After implementing everything above, your project will be:

Not “just a chatbot with PDFs”.

But a full platform that:

Handles heavy processing asynchronously.

Lets users:

Learn any skill.

Upload study material.

Chat with an AI teacher.

Take quizzes.

Solve coding questions with execution.

Get progress analytics.

Runs as multiple services (frontend, backend, worker, optional code runner).

Uses:

RAG

Multi-agent pattern

Vector search

Background jobs

Modern frontend

And you will honestly be in the “advanced project” category, not just “nice side project”.