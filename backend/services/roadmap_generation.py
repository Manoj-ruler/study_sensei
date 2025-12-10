"""
Roadmap Generation Service
Uses Gemini AI to generate personalized learning roadmaps
"""

import google.generativeai as genai
import os
from typing import Optional, List
from services.roadmap_visualization import generate_roadmap_svg, extract_phases_from_roadmap


# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)


def generate_roadmap(
    skill_title: str,
    description: str,
    category: str,
    is_technical: bool,
    document_context: Optional[str] = None
) -> tuple[str, str]:
    """
    Generate a personalized learning roadmap using Gemini AI
    
    Args:
        skill_title: Title of the skill
        description: User's description/objective
        category: Skill category (technical, creative, business, etc.)
        is_technical: Whether coding challenges are available
        document_context: Optional context from uploaded documents
        
    Returns:
        Tuple of (roadmap_markdown, roadmap_svg_data_uri)
    """
    
    # Build the prompt
    prompt = f"""You are an expert learning advisor for StudySensei, an AI-powered learning platform.

SKILL DETAILS:
- Title: {skill_title}
- Description: {description}
- Category: {category}
- Technical Skill: {'Yes' if is_technical else 'No'}

{f'''UPLOADED DOCUMENTS CONTEXT:
{document_context}

Use this context to make the roadmap more specific and relevant.
''' if document_context else ''}

STUDYSENSEI FEATURES:
1. **EXPLAIN Mode**: Get detailed explanations on any topic. AI breaks down complex concepts into digestible pieces.
2. **PLAN Mode**: Create structured learning plans with milestones, timelines, and checkpoints.
3. **COACH Mode**: Get personalized guidance, motivation, study strategies, and accountability.
4. **QUIZ Mode**: Test your knowledge with AI-generated quizzes at any point in your learning journey.
5. **Document Library**: Upload PDFs, notes, textbooks - AI will reference them in answers and create custom content.
{f'6. **Coding Challenges**: Practice with auto-graded coding problems and real-world exercises.' if is_technical else ''}

TASK: Create a comprehensive, actionable learning roadmap with these sections:

## 1. OVERVIEW (2-3 sentences)
Brief introduction to what they'll learn and why it matters.

## 2. LEARNING OBJECTIVES (4-6 specific goals)
Clear, measurable outcomes they'll achieve. Use bullet points.

## 3. STEP-BY-STEP ROADMAP (5-7 phases)
For EACH phase, include:
- **Phase name** and estimated duration
- Key topics to master
- **How to use StudySensei for this phase:**
  - When to use EXPLAIN mode
  - When to use PLAN mode
  - When to use COACH mode
  - When to take QUIZ mode tests
  - How to leverage uploaded documents
  {f'- When to practice coding challenges' if is_technical else ''}

Format each phase like this:
### Phase X: [Name] (Duration)
**Topics:** ...
**StudySensei Strategy:**
- EXPLAIN: ...
- PLAN: ...
- COACH: ...
- QUIZ: ...
- DOCUMENTS: ...
{f'- CODING: ...' if is_technical else ''}

## 4. TIPS FOR SUCCESS
- Best practices for using StudySensei effectively
- How to track progress
- When to upload additional resources
- How to stay motivated

Format in clean Markdown with headers and bullet points. Be specific and actionable. Make it inspiring and motivating!
"""
    
    try:
        # Generate roadmap with Gemini
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        roadmap_text = response.text
        
        # Extract phases for SVG generation
        phases = extract_phases_from_roadmap(roadmap_text)
        
        # Generate SVG visualization
        roadmap_svg = generate_roadmap_svg(skill_title, phases)
        
        # Insert SVG into roadmap (after title, before overview)
        lines = roadmap_text.split('\n')
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith('## ') and ('overview' in line.lower() or '1.' in line):
                insert_index = i
                break
        
        if insert_index > 0:
            lines.insert(insert_index, f'\n![Learning Roadmap Visualization]({roadmap_svg})\n')
            roadmap_text = '\n'.join(lines)
        
        return roadmap_text, roadmap_svg
        
    except Exception as e:
        print(f"Error generating roadmap: {e}")
        # Return a basic roadmap if generation fails
        fallback_roadmap = f"""# {skill_title} Learning Roadmap

## Overview
Welcome to your learning journey for {skill_title}! This roadmap will guide you through mastering this skill using StudySensei's AI-powered features.

## Learning Objectives
- Understand the fundamentals of {skill_title}
- Build practical skills through hands-on practice
- Apply knowledge to real-world scenarios
- Achieve proficiency in {skill_title}

## Your Learning Path

### Phase 1: Foundation (1-2 weeks)
**Topics:** Core concepts and basics
**StudySensei Strategy:**
- EXPLAIN: Use to understand fundamental concepts
- PLAN: Create your learning schedule
- QUIZ: Test basic knowledge

### Phase 2: Deep Dive (2-3 weeks)
**Topics:** Advanced concepts and techniques
**StudySensei Strategy:**
- EXPLAIN: Explore complex topics
- COACH: Get guidance on challenging areas
- DOCUMENTS: Upload relevant materials

### Phase 3: Practice (2-3 weeks)
**Topics:** Hands-on application
**StudySensei Strategy:**
- COACH: Get feedback on your work
- QUIZ: Regular knowledge checks
{f'- CODING: Practice with challenges' if is_technical else ''}

### Phase 4: Mastery (Ongoing)
**Topics:** Real-world application
**StudySensei Strategy:**
- COACH: Refine your skills
- DOCUMENTS: Add advanced resources

## Tips for Success
- Use EXPLAIN mode whenever you're confused
- Take quizzes regularly to track progress
- Upload your study materials to get personalized help
- Ask COACH mode for motivation when needed
"""
        phases = extract_phases_from_roadmap(fallback_roadmap)
        roadmap_svg = generate_roadmap_svg(skill_title, phases)
        
        return fallback_roadmap, roadmap_svg


async def get_document_context(document_ids: List[str]) -> Optional[str]:
    """
    Retrieve and summarize context from uploaded documents
    
    Args:
        document_ids: List of document IDs
        
    Returns:
        Summarized context from documents
    """
    if not document_ids:
        return None
    
    try:
        from supabase import create_client
        import os
        
        # Initialize Supabase client
        SUPABASE_URL = os.getenv('SUPABASE_URL')
        SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Retrieve chunks for the provided document IDs
        all_chunks = []
        for doc_id in document_ids:
            response = supabase.table('document_chunks')\
                .select('content, chunk_index')\
                .eq('document_id', doc_id)\
                .order('chunk_index')\
                .limit(20)\
                .execute()  # Limit to first 20 chunks per document to avoid token overflow
            
            if response.data:
                all_chunks.extend([chunk['content'] for chunk in response.data])
        
        if not all_chunks:
            return None
        
        # Combine chunks into context
        context = "\n\n".join(all_chunks)
        
        # If context is too long, truncate it
        max_context_length = 8000  # characters
        if len(context) > max_context_length:
            context = context[:max_context_length] + "\n\n[... content truncated for brevity ...]"
        
        return context
        
    except Exception as e:
        print(f"Error retrieving document context: {e}")
        return None

