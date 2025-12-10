# StudySensei - Project Documentation

## 1. Project Overview
**StudySensei** is an AI-powered study companion designed to help users learn new skills by uploading study materials (PDFs), asking questions via a chat interface, and testing their knowledge through generated quizzes.

## 2. Technology Stack

### Frontend
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **State Management**: React Hooks (`useState`, `useEffect`, `useRef`)

### Backend
- **Framework**: FastAPI (Python)
- **AI/LLM**: Google Gemini API (`gemini-1.5-flash`)
- **RAG**: `sentence-transformers` (Embeddings), Supabase `pgvector`
- **PDF Processing**: `pypdf`, `langchain`

### Database & Storage
- **Database**: Supabase (PostgreSQL)
- **Storage**: Supabase Storage (for PDF files)
- **Vector Store**: `pgvector` extension for semantic search
- **Auth**: Supabase Auth

## 3. Architecture
The application follows a standard client-server architecture:
1.  **Frontend**: Handles user interaction, file uploads, and displays chat/quiz interfaces.
2.  **Backend**: Exposes REST API endpoints for processing documents, managing chat sessions, and generating quizzes.
3.  **Database**: Stores user data, skills, documents, chat history, and quiz results.
4.  **RAG Pipeline**:
    *   User uploads PDF -> Backend extracts text -> Chunks text -> Generates Embeddings -> Stores in DB.
    *   User asks question -> Backend embeds query -> Searches similar chunks -> Sends context + query to LLM -> Returns answer.

## 4. Key Features Implemented

### A. Authentication & User Management
- **Login/Signup**: Implemented using Supabase Auth.
- **Dashboard**: Displays user-specific "Skills" (topics they are studying).

### B. Document Management
- **Upload**: Users can upload PDF documents to a specific Skill.
- **Processing**:
    - Files are stored in Supabase Storage bucket `documents`.
    - Text is extracted and split into chunks.
    - Embeddings are generated using `sentence-transformers/all-MiniLM-L6-v2`.
    - Chunks are stored in the `document_chunks` table with vector embeddings.
- **Management**: Users can view status (Processing/Ready) and delete documents.

### C. Intelligent Chat (RAG)
- **Contextual Q&A**: Answers are generated based *only* on the uploaded documents.
- **Chat History**:
    - Conversation history is saved to `messages` table.
    - Last 10 messages are injected into the LLM context for continuity.
- **Slash Commands**:
    - `/new`: Clears the current session to start fresh.
    - `/delete`: Deletes the current chat history from the database.
- **Sources**: Responses include citations (filenames) of the documents used.

### D. Quiz System
- **Generation**: AI generates a 5-question multiple-choice quiz based on the documents.
- **Deduplication**: The system tracks previously asked questions to ensure new quizzes offer fresh content.
- **Persistence**:
    - Quiz results are saved to `quizzes` table.
    - Individual questions and user answers are saved to `quiz_questions` table.
- **Scoring**: Immediate feedback and score calculation.

## 5. Database Schema

### Tables
1.  **`profiles`**: User details (linked to `auth.users`).
2.  **`skills`**: Study topics (Title, Description, User ID).
3.  **`documents`**: Uploaded file metadata (Filename, Storage Path, Processed Status).
4.  **`document_chunks`**: Text chunks and vector embeddings for RAG.
5.  **`chats`**: Chat session metadata.
6.  **`messages`**: Individual chat messages (Role, Content, Chat ID).
7.  **`quizzes`**: Quiz summary (Score, Total Questions).
8.  **`quiz_questions`**: Detailed question data (Question, Options, Correct Answer, User Answer).

### RLS Policies
- Row-Level Security is enabled on all tables to ensure users can only access their own data.

## 6. API Endpoints

### Documents
- `POST /documents/upload`: Upload and process a PDF.
- `DELETE /documents/{id}`: Delete a document and its chunks.

### Chat
- `POST /chat/message`: Send a message (performs RAG search and LLM generation).
- `DELETE /chat/{chat_id}`: Delete a chat session.

### Quiz
- `POST /quiz/generate`: Generate a new quiz.
- `POST /quiz/save`: Save quiz results and questions.

## 7. Setup & Run

### Prerequisites
- Node.js & npm
- Python 3.10+
- Supabase Account
- Google Gemini API Key

### Environment Variables
**Frontend ([.env.local](file:///c:/Users/manoj/OneDrive/Desktop/bluconn/frontend/.env.local))**:
```
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

**Backend ([.env](file:///c:/Users/manoj/OneDrive/Desktop/bluconn/backend/.env))**:
```
SUPABASE_URL=...
SUPABASE_KEY=...
GOOGLE_API_KEY=...
```

### Running the App
1.  **Backend**:
    ```bash
    cd backend
    venv\Scripts\activate
    uvicorn main:app --reload --port 8000
    ```
2.  **Frontend**:
    ```bash
    cd frontend
    npm run dev
    ```
