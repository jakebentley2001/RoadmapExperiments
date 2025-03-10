from parse_text import parse_stages
from roadmap import create_roadmap
from refine_prompt import start_graph, build_graph, main_interaction
import os
from langchain_community.llms import OpenAI
from langchain.chains import LLMChain
from dotenv import load_dotenv
# Initialize the LLM (here we use OpenAI’s model)

load_dotenv()

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")
        
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

start_graph()
graph = build_graph()
final_prompt = main_interaction(graph)

road_map = create_roadmap(final_prompt)


parsed_text = parse_stages(road_map)




