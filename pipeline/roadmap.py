from openai import OpenAI


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

Please create multiple stages using the same structure. End your content after the final stage without any additional text outside of this structure.
"""


def create_roadmap(final_prompt):
    client = OpenAI()
    prompt = final_prompt + ": " + structure_prompt

    response = client.chat.completions.create(
            model="gpt-4o",
            messages= [{ "role": "user", "content": prompt}],
            temperature=0.7,
            stream=True,  # <--- The key to getting partial tokens
        )

    output = ""
    for chunk in response:
        chunk_text = chunk.choices[0].delta.content
        if chunk_text:
            output += chunk_text
        # Print the partial text without a newline, and flush for immediate display
        print(chunk_text, end="", flush=True)
       
    return output