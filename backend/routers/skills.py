from fastapi import APIRouter, HTTPException
from database import supabase

router = APIRouter(prefix="/skills", tags=["skills"])

@router.delete("/{skill_id}")
async def delete_skill(skill_id: str):
    """
    Delete a skill and all its related data (cascade deletion).
    
    Related data that will be automatically deleted:
    - Documents and document chunks
    - Chats and messages
    - Quizzes
    - Coding questions and test cases
    - Code submissions
    - Progress metrics
    """
    try:
        # Verify skill exists and delete it
        # RLS policy ensures user can only delete their own skills
        response = supabase.table("skills").delete().eq("id", skill_id).execute()
        
        # Check if any rows were deleted
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=404, 
                detail="Skill not found or you don't have permission to delete it"
            )
        
        return {
            "status": "success", 
            "message": "Skill and all related data deleted successfully",
            "deleted_skill_id": skill_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete skill error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete skill: {str(e)}")
