from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
import json
import re
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage



def start_graph():
    Model = ChatOpenAI(model="gpt-4o",temperature=0.5)

    class State(MessagesState):
        summary: str

    #############################################
    # System Message Setup
    #############################################
    content = """ChatGPT, I would like to request your assistance in creating an AI-powered prompt rewriter, which can help me rewrite and refine prompts that I intend to use with you, ChatGPT, for the purpose of obtaining improved responses. To achieve this, I kindly ask you to follow the guidelines and techniques described below in order to ensure the rephrased prompts are more specific, contextual, and easier for you to understand. Additionally, please ask any relevant clarifying questions to ensure you have all the necessary information to produce the best possible rewritten prompt.

    Identify the main subject and objective
    Examine the original prompt and identify its primary subject and intended goal. Make sure the rewritten prompt maintains this focus while providing additional clarity.

    Ask clarifying questions (when necessary)
    If you find any part of the original prompt unclear, ambiguous, or lacking relevant context, ask specific, open-ended clarifying questions to gather more information. Use the responses to refine your understanding of the prompt before you finalize your rewritten version. The questions should have 4 possible answer choices.

    Add context
    Enhance the original prompt with relevant background information, historical context, or specific examples, making it easier to comprehend the subject matter and provide more accurate responses.

    Ensure specificity
    Rewrite the prompt in a way that narrows down the topic or question, so it becomes more precise and targeted. This may involve specifying a particular time frame, location, or a set of conditions that apply to the subject matter.

    Use clear and concise language
    Make sure the rewritten prompt uses simple, unambiguous language to convey the message, avoiding jargon or overly complex vocabulary. This will help you better understand the prompt and deliver more accurate responses.

    Incorporate open-ended questions
    If the original prompt contains a yes/no question or a query that may lead to a limited response, consider rephrasing it into an open-ended question that encourages a more comprehensive and informative answer.

    Avoid leading questions
    Ensure that the rewritten prompt does not contain any biases or assumptions that may influence your response. Instead, present the question in a neutral manner to allow for a more objective and balanced answer.

    Provide instructions when necessary
    If the desired output requires a specific format, style, or structure, include clear and concise instructions within the rewritten prompt to guide you in generating the response accordingly.

    Ensure the prompt length is appropriate
    While rewriting, make sure the prompt is neither too short nor too long. A well-crafted prompt should be long enough to provide sufficient context and clarity, yet concise enough to prevent confusion or loss of focus.

    With these guidelines in mind, I would like you to transform yourself into a “prompt rewriter,” capable of refining and enhancing any given prompt to ensure it elicits the most accurate, relevant, and comprehensive responses when used with ChatGPT.

    Please begin by examining the original prompt.
    If you need more information, ask clarifying questions.
    Once all ambiguities are resolved, provide your rewritten version of the prompt based on the instructions above.
    """
    global sys_msg
    sys_msg = SystemMessage(
        content=content
    )
    global model
    model = Model

#############################################
# Node Functions
#############################################

def generate_questions(state: MessagesState):
    """
    Generates exactly three questions about the user's topic.
    Expects the last user message to contain the topic.
    """
    # The user topic is the last message content from the user:
    topic = state["messages"][-1].content  # e.g., "the user wants to learn about X"

    prompt = f"""Ask the clarifying questions on the following topic: {topic}
    Please return exactly three clarifying questions about this topic 
    in the following JSON format (and no additional text):
    {{
        "question1": "Your first question here",
        "question2": "Your second question here",
        "question3": "Your third question here"
    }}
    Ensure your output is valid JSON and do not include any extra keys or text.
    """
    # Ask the model to generate 3 questions
    generated_questions = model.invoke([
        sys_msg, 
        AIMessage(content=prompt)
    ])

    pattern1 = r'"question1":\s*"([^"]+)"'
    pattern2 = r'"question2":\s*"([^"]+)"'
    pattern3 = r'"question3":\s*"([^"]+)"'
    match = re.search(pattern1, generated_questions.content)
    match2 = re.search(pattern2, generated_questions.content)
    match3 = re.search(pattern3, generated_questions.content)
    if match:
        question = match.group(1)
        q1 = question

    if match2:
        question = match2.group(1)
        q2 = question

    if match3:
        question = match3.group(1)
        q3 = question

    
    return {
        "messages": [
            AIMessage(content=f"Question 1 related to {topic}: {q1}"),
            AIMessage(content=f"Question 2 related to {topic}: {q2}"),
            AIMessage(content=f"Question 3 related to {topic}: {q3}")
        ]
    }


def human_feedback_answers(state: MessagesState):
    """
    This node is triggered once the user has provided their answers.
    In this example, the logic is minimal because we handle collecting
    answers in the main Python loop. We simply pass through here.
    """
    # Optionally, you can do more logic or store data in state["meta"], etc.
    return {}  # No new messages—just a placeholder.


def create_prompt(state: MessagesState):
    """
    Create a final prompt or summary using the user’s two answers.
    """
    # Collect the last two HumanMessages (the user answers).
    # In many cases, you might find them by indexing or using a filter.
    user_messages = [m for m in state["messages"] if isinstance(m, HumanMessage)]
    
    # If you only store two answers, they should be the last two
    answer1 = user_messages[-3].content
    answer2 = user_messages[-2].content
    answer3 = user_messages[-1].content
    original_prompt = f"""  
    I want to create a structured curriculum for learning {state["messages"][0].content} from the ground up. Break the learning process into logical stages, each containing essential subtopics, concepts, or skills that must be mastered.

    For each stage, provide:

    A brief description of what is covered.
    The key subtopics or skills within that stage.
    Any prerequisites (if applicable).
    The estimated time or effort needed for completion.
    Recommended learning methods (e.g., hands-on projects, reading, exercises).
    Ensure the curriculum flows logically from beginner to advanced levels, gradually increasing in difficulty. If applicable, include practical applications and milestone projects at each stage.

    Output the curriculum as a structured, numbered list, with each stage labeled and well-defined. Format it clearly for easy reference.
    """

    prompt = (f"""I want to build a curriculum builder that takes in a task or skill and outputs the subtopics and skills necessary to achieve the input. build me a prompt that does this
            Here is the original prompt: {original_prompt}
            Here are the two clarifying questions with their answers:
            1: {answer1}
            2: {answer2}
            3: {answer3}
            Now return only the refined prompt
            """)

    generated_prompt= model.invoke([sys_msg, AIMessage(content=prompt)])

    return {"messages": [AIMessage(content=generated_prompt.content)]}

    

def build_graph():
    
    #############################################
    # Build the StateGraph
    #############################################
    builder = StateGraph(MessagesState)

    # Add nodes
    builder.add_node("generate_questions", generate_questions)
    builder.add_node("human_feedback_answers", human_feedback_answers)
    builder.add_node("create_prompt", create_prompt)

    # Define edges
    builder.add_edge(START, "generate_questions")
    builder.add_edge("generate_questions", "human_feedback_answers")
    builder.add_edge("human_feedback_answers", "create_prompt")
    builder.add_edge("create_prompt", END)

    # Create a memory saver/checkpointer if needed
    memory = MemorySaver()

    # Compile the graph
    graph = builder.compile(
        interrupt_before=["human_feedback_answers"], 
        checkpointer=memory
    )

    return graph
    

def main_interaction(graph):
    #############################################
    # MAIN INTERACTION LOGIC
    #############################################

    # 1. Ask for the topic
    user_input = input("What topic do you want to learn about: ")
    initial_input = {
        "messages": [HumanMessage(content=f"the user wants to learn about {user_input}")]
    }

    # 2. Stream and get TWO AI questions, collecting the answers
    answers = []
    question_count = 0

    # First streaming pass: generate_questions node will run
    for event in graph.stream(initial_input, {"configurable": {"thread_id": "15"}}, stream_mode="values"):
        for new_event in event["messages"]:
            if "Question" in new_event.content:
                new_event.pretty_print()  # Display the question
                user_answer = input("Your answer: ")
                answers.append(new_event.content + ":\n" + user_answer)
                question_count += 1

                # If we've already answered 2 questions, break out
                if question_count >= 3:
                    break
            else:
                # Print any other messages from the AI
                new_event.pretty_print()

        if question_count >= 3:
            break

    # 3. Update the graph with both answers at once, pointing to "human_feedback_answers"
    graph.update_state(
        {"configurable": {"thread_id": "15"}},
        {
            "messages": [HumanMessage(content=a) for a in answers]
        },
        as_node="human_feedback_answers"
    )

    # 4. Stream again to move from human_feedback_answers → create_prompt → END
    count = 0
    for event in graph.stream(None, {"configurable": {"thread_id": "15"}}, stream_mode="values"):
        #This helps us not return the human feedback
        if count == 0 or count == 1:
            count +=1
            if count == 1:
                continue

        #for msg in event["messages"]:
        event["messages"][-1].pretty_print()
        final_prompt = event["messages"][-1].content

    print("\n=== Done! ===")

    return final_prompt


