import json
import os
from pathlib import Path

from dotenv import load_dotenv
from strands import Agent
from strands_tools import calculator
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


def generate_html(posts: list[Post]):
    current_html = Path("pages/feed.html").read_text()
    system_prompt = get_instructions("html_generator_prompt", current_html=current_html)
    agent = Agent(model=model, tools=[calculator], system_prompt=system_prompt)
    spec = Path("spec/spec.md").read_text()

    response = agent(spec)
    Path("pages/feed.html").write_text(response.message["content"][0]["text"])


def add_new_posts(posts: list[Post]):
    page_path = Path("breba_social/agents/pages/feed.html")
    current_html = page_path.read_text()
    system_prompt = get_instructions("html_generator_add_posts_prompt", current_html=current_html)
    agent = Agent(model=model, tools=[calculator], system_prompt=system_prompt)
    json_string = json.dumps([p.model_dump() for p in posts], default=str)

    response = agent(json_string)
    page_path.write_text(response.message["content"][0]["text"])