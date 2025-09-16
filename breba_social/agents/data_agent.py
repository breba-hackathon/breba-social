import os
from pathlib import Path

from dotenv import load_dotenv
from strands import Agent
from strands.models.openai import OpenAIModel

from breba_social.agents.instruction_reader import get_instructions
from breba_social.models import Post

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_KEY")
model = OpenAIModel(
    client_args={
        "api_key": OPENAI_KEY,
    },
    model_id="gpt-4.1",
    params={
        "temperature": 0,
    }
)

def filter_post(post: Post):
    system_prompt = get_instructions("filter_posts_prompt")
    agent = Agent(model=model, tools=[], system_prompt=system_prompt)

    json_str = post.model_dump_json()
    response = agent(json_str)

    return response.message["content"][0]["text"] == "true"
