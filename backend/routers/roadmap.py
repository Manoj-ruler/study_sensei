"""
Roadmap Router
API endpoints for generating and managing learning roadmaps
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from services.roadmap_generation import generate_roadmap, get_document_context
from supabase import create_client
import os

router = APIRouter(prefix="/roadmap", tags=["roadmap"])

# Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


class GenerateRoadmapRequest(BaseModel):
    skill_id: str
    document_ids: Optional[List[str]] = []


@router.post("/generate")
async def generate_skill_roadmap(request: GenerateRoadmapRequest):
    """
    Generate a personalized learning roadmap for a skill
    
    Args:
        skill_id: ID of the skill
        document_ids: Optional list of document IDs for context
        
    Returns:
        Generated roadmap markdown and SVG
    """
    try:
        # Fetch skill details
        skill_response = supabase.table('skills').select('*').eq('id', request.skill_id).single().execute()
        
        if not skill_response.data:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        skill = skill_response.data
        
        # Get document context if documents provided
        document_context = None
        if request.document_ids:
            document_context = await get_document_context(request.document_ids)
        
        # Generate roadmap
        roadmap_text, roadmap_svg = generate_roadmap(
            skill_title=skill['title'],
            description=skill.get('description', ''),
            category=skill.get('category', 'general'),
            is_technical=skill.get('is_technical', False) or skill.get('category') == 'technical',
            document_context=document_context
        )
        
        # Update skill with roadmap
        update_response = supabase.table('skills').update({
            'roadmap': roadmap_text,
            'roadmap_svg': roadmap_svg
        }).eq('id', request.skill_id).execute()
        
        return {
            "success": True,
            "roadmap": roadmap_text,
            "roadmap_svg": roadmap_svg,
            "skill_id": request.skill_id
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generating roadmap: {e}")
        print(f"Full traceback: {error_details}")
        raise HTTPException(status_code=500, detail=f"Failed to generate roadmap: {str(e)}")


@router.get("/{skill_id}")
async def get_skill_roadmap(skill_id: str):
    """
    Get the roadmap for a skill
    
    Args:
        skill_id: ID of the skill
        
    Returns:
        Roadmap data
    """
    try:
        response = supabase.table('skills').select('roadmap, roadmap_svg').eq('id', skill_id).single().execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        return {
            "roadmap": response.data.get('roadmap'),
            "roadmap_svg": response.data.get('roadmap_svg')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
