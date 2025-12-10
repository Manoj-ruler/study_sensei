from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Any
from database import supabase
import datetime

router = APIRouter(prefix="/analytics", tags=["analytics"])

class MetricLog(BaseModel):
    user_id: str
    skill_id: str
    activity_type: str # 'quiz', 'code', 'chat'
    score: Optional[int] = 0
    max_score: Optional[int] = 0
    metadata: Optional[dict] = {}

@router.post("/log")
async def log_metric(payload: MetricLog):
    try:
        data = {
            "user_id": payload.user_id,
            "skill_id": payload.skill_id,
            "activity_type": payload.activity_type,
            "score": payload.score,
            "max_score": payload.max_score,
            "metadata": payload.metadata
        }
        res = supabase.table("progress_metrics").insert(data).execute()
        return {"status": "success", "id": res.data[0]['id']}
    except Exception as e:
        print(f"Log Metric Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/skill/{skill_id}")
async def get_skill_analytics(skill_id: str, user_id: str):
    try:
        # Fetch metrics for this user and skill
        response = supabase.table("progress_metrics") \
            .select("*") \
            .eq("skill_id", skill_id) \
            .eq("user_id", user_id) \
            .order("created_at", desc=False) \
            .execute()
        
        metrics = response.data
        
        # Process data for charts
        # 1. Total Activity Count
        # 2. Quiz Performance over time
        # 3. Code Challenges solved
        
        quiz_scores = [m for m in metrics if m['activity_type'] == 'quiz']
        code_submissions = [m for m in metrics if m['activity_type'] == 'code']
        
        # Simple aggregated stats
        total_quizzes = len(quiz_scores)
        total_code_challenges = len(code_submissions)
        
        # Calculate quiz average (normalize to 0-1)
        if total_quizzes > 0:
            quiz_scores_normalized = [q['score'] / q['max_score'] if q.get('max_score', 0) > 0 else 0 for q in quiz_scores]
            avg_quiz_score = sum(quiz_scores_normalized) / total_quizzes
        else:
            avg_quiz_score = 0
        
        # Calculate code average (normalize to 0-1)
        if total_code_challenges > 0:
            code_scores_normalized = [c['score'] / c['max_score'] if c.get('max_score', 0) > 0 else 0 for c in code_submissions]
            avg_code_score = sum(code_scores_normalized) / total_code_challenges
        else:
            avg_code_score = 0
        
        # Combined average score (weighted by count)
        total_activities = total_quizzes + total_code_challenges
        if total_activities > 0:
            combined_avg_score = ((avg_quiz_score * total_quizzes) + (avg_code_score * total_code_challenges)) / total_activities
        else:
            combined_avg_score = 0

        return {
            "summary": {
                "total_quizzes": total_quizzes,
                "avg_quiz_score": round(avg_quiz_score, 2),
                "code_challenges_solved": total_code_challenges,
                "avg_code_score": round(avg_code_score, 2),
                "combined_avg_score": round(combined_avg_score, 2)
            },
            "history": metrics
        }

    except Exception as e:
        print(f"Get Analytics Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
