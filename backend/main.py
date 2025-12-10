from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="StudySensei API", version="1.0.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers import documents
from routers import chat
from routers import quiz

app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(quiz.router)
from routers import solver
app.include_router(solver.router)
from routers import mentor
app.include_router(mentor.router)
from routers import analytics
app.include_router(analytics.router)
from routers import roadmap
app.include_router(roadmap.router)
from routers import skills
app.include_router(skills.router)

@app.get("/")
async def root():
    return {"message": "Welcome to StudySensei API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
