"""
SVG Roadmap Visualization Service
Generates beautiful roadmap diagrams as SVG
"""

import svgwrite
from typing import List, Dict
import base64


def generate_roadmap_svg(skill_title: str, phases: List[Dict[str, str]]) -> str:
    """
    Generate a visual roadmap diagram as SVG
    
    Args:
        skill_title: Title of the skill
        phases: List of phase dictionaries with 'name' and 'duration' keys
        
    Returns:
        Base64 encoded SVG data URI
    """
    # Calculate dimensions
    phase_count = len(phases)
    width = min(800, 150 * phase_count + 100)
    height = 250
    
    dwg = svgwrite.Drawing(size=(f'{width}px', f'{height}px'))
    
    # Add gradient definition
    gradient = dwg.defs.add(dwg.linearGradient(id='purple_gradient', x1='0%', y1='0%', x2='100%', y2='0%'))
    gradient.add_stop_color(offset='0%', color='#9333ea')
    gradient.add_stop_color(offset='100%', color='#ec4899')
    
    # Add title
    dwg.add(dwg.text(
        skill_title,
        insert=(width/2, 30),
        text_anchor='middle',
        font_size='20px',
        font_weight='bold',
        font_family='Arial, sans-serif',
        fill='url(#purple_gradient)'
    ))
    
    # Draw roadmap path
    y_pos = 80
    x_start = 50
    phase_width = min(140, (width - 100) / phase_count - 20)
    spacing = 20
    
    for i, phase in enumerate(phases):
        x = x_start + (i * (phase_width + spacing))
        
        # Draw phase box with gradient border
        dwg.add(dwg.rect(
            insert=(x, y_pos),
            size=(phase_width, 100),
            fill='#faf5ff',
            stroke='url(#purple_gradient)',
            stroke_width=2,
            rx=12
        ))
        
        # Add phase number circle
        dwg.add(dwg.circle(
            center=(x + 20, y_pos + 20),
            r=16,
            fill='url(#purple_gradient)'
        ))
        dwg.add(dwg.text(
            str(i + 1),
            insert=(x + 20, y_pos + 26),
            text_anchor='middle',
            fill='white',
            font_weight='bold',
            font_size='14px',
            font_family='Arial, sans-serif'
        ))
        
        # Add phase name (wrap text if too long)
        phase_name = phase.get('name', f'Phase {i+1}')
        if len(phase_name) > 15:
            # Split into two lines
            words = phase_name.split()
            mid = len(words) // 2
            line1 = ' '.join(words[:mid])
            line2 = ' '.join(words[mid:])
            
            dwg.add(dwg.text(
                line1,
                insert=(x + phase_width/2, y_pos + 55),
                text_anchor='middle',
                font_size='11px',
                font_weight='600',
                font_family='Arial, sans-serif',
                fill='#581c87'
            ))
            dwg.add(dwg.text(
                line2,
                insert=(x + phase_width/2, y_pos + 70),
                text_anchor='middle',
                font_size='11px',
                font_weight='600',
                font_family='Arial, sans-serif',
                fill='#581c87'
            ))
        else:
            dwg.add(dwg.text(
                phase_name,
                insert=(x + phase_width/2, y_pos + 60),
                text_anchor='middle',
                font_size='12px',
                font_weight='600',
                font_family='Arial, sans-serif',
                fill='#581c87'
            ))
        
        # Add duration
        duration = phase.get('duration', '')
        if duration:
            dwg.add(dwg.text(
                duration,
                insert=(x + phase_width/2, y_pos + 90),
                text_anchor='middle',
                font_size='10px',
                font_family='Arial, sans-serif',
                fill='#9333ea'
            ))
        
        # Draw arrow to next phase
        if i < len(phases) - 1:
            arrow_start_x = x + phase_width
            arrow_end_x = arrow_start_x + spacing
            arrow_y = y_pos + 50
            
            # Arrow line
            dwg.add(dwg.line(
                start=(arrow_start_x, arrow_y),
                end=(arrow_end_x, arrow_y),
                stroke='#9333ea',
                stroke_width=2
            ))
            
            # Arrow head
            dwg.add(dwg.polygon(
                points=[
                    (arrow_end_x, arrow_y),
                    (arrow_end_x - 6, arrow_y - 4),
                    (arrow_end_x - 6, arrow_y + 4)
                ],
                fill='#9333ea'
            ))
    
    # Add footer text
    dwg.add(dwg.text(
        'Your Learning Journey',
        insert=(width/2, height - 20),
        text_anchor='middle',
        font_size='11px',
        font_style='italic',
        font_family='Arial, sans-serif',
        fill='#9ca3af'
    ))
    
    # Convert to base64 data URI
    svg_string = dwg.tostring()
    svg_bytes = svg_string.encode('utf-8')
    svg_base64 = base64.b64encode(svg_bytes).decode('utf-8')
    
    return f"data:image/svg+xml;base64,{svg_base64}"


def extract_phases_from_roadmap(roadmap_text: str) -> List[Dict[str, str]]:
    """
    Extract phase information from generated roadmap text
    
    Args:
        roadmap_text: The markdown roadmap text
        
    Returns:
        List of phase dictionaries
    """
    phases = []
    lines = roadmap_text.split('\n')
    
    current_phase = None
    for line in lines:
        # Look for phase headers (e.g., "### Phase 1:" or "## Week 1:")
        if line.startswith('###') or line.startswith('##'):
            if 'phase' in line.lower() or 'week' in line.lower() or 'step' in line.lower():
                # Extract phase name
                phase_name = line.replace('#', '').strip()
                # Remove numbering if present
                phase_name = phase_name.split(':', 1)[-1].strip() if ':' in phase_name else phase_name
                
                if current_phase:
                    phases.append(current_phase)
                
                current_phase = {
                    'name': phase_name[:30],  # Limit length
                    'duration': ''
                }
        
        # Look for duration mentions
        elif current_phase and ('week' in line.lower() or 'day' in line.lower() or 'month' in line.lower()):
            if not current_phase['duration']:
                # Extract duration
                for word in line.split():
                    if any(unit in word.lower() for unit in ['week', 'day', 'month']):
                        # Get the number before it
                        words = line.split()
                        idx = words.index(word)
                        if idx > 0 and words[idx-1].isdigit():
                            current_phase['duration'] = f"{words[idx-1]} {word}"
                            break
    
    if current_phase:
        phases.append(current_phase)
    
    # If no phases found, create default ones
    if not phases:
        phases = [
            {'name': 'Foundation', 'duration': '1-2 weeks'},
            {'name': 'Core Learning', 'duration': '2-3 weeks'},
            {'name': 'Practice', 'duration': '1-2 weeks'},
            {'name': 'Mastery', 'duration': '2-3 weeks'},
        ]
    
    return phases[:6]  # Limit to 6 phases for visual clarity
