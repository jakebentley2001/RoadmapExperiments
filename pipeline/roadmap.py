import re
import time
from openai import OpenAI
import threading
import queue

structure_prompt = """Please provide the content in the following format and structure exactly:

### Stage {stage_number}: {stage_title}
1. **Description**: {A concise description of this stage}
2. **Key Subtopics/Skills**:
   - {List each subtopic or skill as a new bullet item}
   - {Bullet 2}
   - {Bullet 3}
3. **Prerequisites**: {List or describe prerequisite knowledge}
4. **Estimated Time/Effort**: {e.g. "1 week", "2 weeks", etc.}
5. **Recommended Methods**:
   - {Bullet 1 for recommended method}
   - {Bullet 2}
   - {Bullet 3}

Please create 2 stages using the same structure. End your content after the final stage without any additional text outside of this structure.
"""

def extract_subtopics(stage_text):
    """Extracts the Key Subtopics/Skills from a completed stage text."""
    match = re.search(r"2\.\s\*\*Key Subtopics/Skills\*\*:\n((?:\s+- .+\n)+)", stage_text)
    if match:
        subtopics = [line.strip("- ").strip() for line in match.group(1).split("\n") if line.strip()]
        return subtopics
    return []

# --------------------------
# 1. Fetch resources per subtopic
# --------------------------
def fetch_resources_for_subtopic(subtopic, resources):
    """
    Fetch additional educational resources for a given subtopic.
    
    This function uses the OpenAI API to generate a markdown-formatted list of 
    resources (each as a bullet point with a brief description) for the subtopic.
    
    Args:
        subtopic (str): The subtopic for which resources are needed.
        
    Returns:
        str: Markdown-formatted resource information.
    """
    client = OpenAI()  # Replace with your actual OpenAI client initialization if needed
    
    prompt = (
        f"""Generate a list of additional resources for learning more about the subtopic: 
        '{subtopic}'. Your response should be in the exact format 
        - *Resource*
            *Short Description*
        - *Resource*
            *Short Description*
        - *Resource*
            *Short Description*
            
        only uses these resources {resources}
        """

    )

    
    response = client.chat.completions.create(
        model="gpt-4o",  # Use your desired model name
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=150  # Adjust as necessary
    )
    
    resource_content = response.choices[0].message.content.strip()

    return resource_content

# --------------------------
# 2. Update stage text in memory by inserting resources under each subtopic bullet
# --------------------------
def update_stage_with_resources(stage_text, subtopic_resources):
    """
    Given the original stage markdown and a dict mapping subtopics to resource markdown,
    insert each resource block immediately after the corresponding bullet item.
    
    Args:
        stage_text (str): The original markdown text for the stage.
        subtopic_resources (dict): Keys are subtopic strings; values are resource markdown.
    
    Returns:
        str: The updated stage markdown with resource info inserted.
    """
    lines = stage_text.splitlines()
    updated_lines = []
    
    # Process each line and insert resources right after a bullet that matches a subtopic.
    for line in lines:
        updated_lines.append(line)
        # Look for a bullet item; assume format: "- subtopic"
        bullet_match = re.match(r'\s*-\s*(.+)', line)
        if bullet_match:
            bullet_text = bullet_match.group(1).strip()
            # If the bullet exactly matches one of our subtopics...
            if bullet_text in subtopic_resources:
                # Split the resource markdown into lines and indent (e.g., 4 spaces)
                resource_lines = subtopic_resources[bullet_text].splitlines()
                indented_resource_lines = ["    " + res for res in resource_lines]
                updated_lines.extend(indented_resource_lines)
    return "\n".join(updated_lines)



def update_markdown_file_with_stage(roadmap_file, updated_stage_text, stage_header):
    """
    Reads the entire roadmap file, locates the stage block identified by stage_header,
    then replaces only the Key/Subtopics/Skills block within that stage with the corresponding
    block from updated_stage_text.
    
    Args:
        roadmap_file (str): Path to the markdown file.
        updated_stage_text (str): The new stage content that includes an updated 
                                  "2. **Key Subtopics/Skills**:" section.
        stage_header (str): The stage header line (e.g., "### Stage 1: Introduction ...").
    """
    # Read the whole file
    with open(roadmap_file, "r") as f:
        content = f.read()

    # Find the stage block using stage_header.
    stage_pattern = re.compile(
        re.escape(stage_header) + r'.*?(?=^### Stage|\Z)',
        re.DOTALL | re.MULTILINE
    )
    stage_match = stage_pattern.search(content)
    if stage_match:
        old_stage_block = stage_match.group(0)
        
        key_subtopics_pattern = re.compile(
            r'(2\.\s\*\*Key Subtopics/Skills\*\*:\n.*?)(?=\n\d+\.\s\*\*|$)',
            re.DOTALL
        )

        
        old_key_match = key_subtopics_pattern.search(old_stage_block)
        new_key_match = key_subtopics_pattern.search(updated_stage_text)
        
        if old_key_match and new_key_match:
            old_key_block = old_key_match.group(1)
            new_key_block = new_key_match.group(1)
            
            # Replace only the key subtopics block in the stage block.
            updated_stage_block = old_stage_block.replace(old_key_block, new_key_block)
            # print("******************************************************************************************************")
            # print("Jake")
            # print(updated_stage_block)
            # print("******************************************************************************************************")
            # Replace the entire stage block in the file content with the updated one.
            new_content = content.replace(old_stage_block, updated_stage_block)

            # print("******************************************************************************************************")
            # print("Sally")
            # print(new_content)
            # print("******************************************************************************************************")

            with open(roadmap_file, "w") as f:
                f.write(new_content)
        else:
            print("Key/Subtopics block not found in one of the texts.")
    else:
        # If the stage header wasn't found, append the updated stage at the end.
        with open(roadmap_file, "a") as f:
            f.write("\n" + updated_stage_text)



# --------------------------
# 4. Process a stage after it is streamed
# --------------------------
def process_stage(stage_text, roadmap_file, resources):
    """
    For a completed stage, fetch resources for each subtopic, update the stage text
    with these resources inserted under each bullet, and then update the markdown file.
    """
    subtopics = extract_subtopics(stage_text)
    if subtopics:
        print("\nFetching additional resources for subtopics...\n")
        subtopic_resources = {}
        for subtopic in subtopics:
            resource = fetch_resources_for_subtopic(subtopic, resources)
            subtopic_resources[subtopic] = resource
        
        # Update the stage text in memory
        updated_stage_text = update_stage_with_resources(stage_text, subtopic_resources)
        
        # Assume the stage header is the first line that starts with "### Stage"
        header_match = re.search(r'^(### Stage [^\n]+)', stage_text, re.MULTILINE)
        if header_match:
            stage_header = header_match.group(1)
        else:
            stage_header = "### Stage"  # Fallback
        
        # Update the roadmap markdown file with the new stage text
        update_markdown_file_with_stage(roadmap_file, updated_stage_text, stage_header)
        print("Updated stage with inserted resources:\n", updated_stage_text)


# --------------------------
# 5. Example streaming function that calls process_stage when a stage is complete.
# (Your existing create_roadmap function is modified to spawn process_stage in a thread.)
# --------------------------

def gather_open_resource(final_prompt):
    client = OpenAI()

    newline_index = final_prompt.find('\n')
    new_prompt = final_prompt[:newline_index]

    prompt = f"""
        This is the goal of the a roadmap builder: {new_prompt}
        I want you to find 10 educational websites that offer open source information that would help with the goal. 
        and the only output to be of the format: source source source ...

    """
    response = client.chat.completions.create(
            model="gpt-4o",  # Use your desired model name
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150  # Adjust as necessary
        )
    
    resource_content = response.choices[0].message.content.strip()
  
    resource_list = (
        [line.split(". ", 1)[1] for line in resource_content.split("\n") if ". " in line]
    )
    if resource_list == []:
        resource_list = [line for line in resource_content.split(" ")]

    return resource_content, resource_list


def create_roadmap(final_prompt):
    """
    Streams the roadmap. Once a stage is complete, spawns a thread to fetch resources
    and update the stage in the markdown file so that each subtopic's resources are inserted
    right under its bullet point.
    """
    resources, result_list = gather_open_resource(final_prompt)

    client = OpenAI()
    prompt = final_prompt + ": " + structure_prompt

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        stream=True
    )

    output = ""
    stage_text = ""  # Accumulate text for the current stage
    roadmap_file = "roadmap.md"
    counter = 2  # Assuming stage numbering starts at Stage 2

    for chunk in response:
        chunk_text = chunk.choices[0].delta.content
        if chunk_text:
            output += chunk_text
            stage_text += chunk_text

            # Append the chunk to the file
            with open(roadmap_file, "a") as md_file:
                md_file.write(chunk_text)
            print(chunk_text, end="", flush=True)

            # When a new stage header appears, process the previous stage.
            #if f"### Stage {counter}" in stage_text:
            if "**Prerequisites**" in stage_text:
                # (Optionally, you might trim stage_text so that it does not include the next stage.)
                print("Stage boundary detected; processing resources for the completed stage...")
                threading.Thread(
                    target=process_stage,
                    args=(stage_text, roadmap_file, resources)
                ).start()
                stage_text = ""  # Reset for the next stage
                counter += 1

    return output
