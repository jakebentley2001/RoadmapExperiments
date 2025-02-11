import re

def parse_stages(text):
    """
    Parses the LLM output text into a structured list of stages.
    Each stage is a dictionary with keys:
      stage_number, stage_title, description, key_subtopics, prerequisites,
      time_effort, recommended_methods
    """
    
    # Regex to find each stage header: "### Stage X: Title"
    stage_pattern = re.compile(r'^### Stage\s+(\d+):\s+(.*)$', re.MULTILINE)

    # Find all stages by their starting positions
    matches = list(stage_pattern.finditer(text))

    stages = []
    
    # We'll iterate over each match and slice the text from this stage to the next
    for i, match in enumerate(matches):
        stage_number = match.group(1).strip()
        stage_title = match.group(2).strip()

        # Start index for this stage's text
        start_pos = match.end()
        
        # End index -> next stage start OR end of text
        end_pos = matches[i+1].start() if i+1 < len(matches) else len(text)
        
        # Extract just this stage's block
        stage_block = text[start_pos:end_pos].strip()
        
        # Now we parse out the parts 1,2,3,4,5 within stage_block
        description = extract_section(stage_block, r'^1\.\s+\*\*Description\*\*:\s*(.*)', single_line=True)
        key_subtopics_block = extract_section(stage_block, r'^2\.\s+\*\*Key Subtopics/Skills\*\*:\s*(.*?)(?=^3\.|\Z)', single_line=False)
        prerequisites = extract_section(stage_block, r'^3\.\s+\*\*Prerequisites\*\*:\s*(.*)', single_line=True)
        time_effort = extract_section(stage_block, r'^4\.\s+\*\*Estimated Time/Effort\*\*:\s*(.*)', single_line=True)
        recommended_methods_block = extract_section(stage_block, r'^5\.\s+\*\*Recommended Methods\*\*:\s*(.*?)(?=^###|$)', single_line=False)

        # For Key Subtopics and Recommended Methods, we often have multiple lines
        # Parse them as bullet points
        key_subtopics = parse_bullet_points(key_subtopics_block)
        recommended_methods = parse_bullet_points(recommended_methods_block)
        
        # Build dictionary
        stage_data = {
            "stage_number": stage_number,
            "stage_title": stage_title,
            "description": description,
            "key_subtopics": key_subtopics,
            "prerequisites": prerequisites,
            "time_effort": time_effort,
            "recommended_methods": recommended_methods
        }

        stages.append(stage_data)
    
    return stages

def extract_section(text_block, pattern, single_line=True):
    """
    Extracts the content for a particular section using a regex.
      - If single_line=True, it extracts only the matching line.
      - If single_line=False, it extracts multiple lines until a stop pattern.
    """
    flags = re.MULTILINE | re.DOTALL
    match = re.search(pattern, text_block, flags)
    if match:
        # If single_line, we just return the first capturing group directly
        if single_line:
            return match.group(1).strip()
        else:
            return match.group(1).strip()
    return ""

def parse_bullet_points(text_block):
    """
    Splits a section (like Key Subtopics or Recommended Methods) by bullet lines.
    Assumes lines starting with '-' (or you can add other bullet chars).
    """
    lines = text_block.splitlines()
    bullets = []
    for line in lines:
        line = line.strip()
        # If the line starts with a dash, treat it as a bullet point
        if line.startswith('-'):
            # remove the dash and extra spaces
            bullet_text = line[1:].strip()
            if bullet_text:
                bullets.append(bullet_text)
    # Return list of bullet points
    return bullets

