# chat_agent.py
from llama_index.core.tools.query_engine import QueryEngineTool
from llama_index.core.tools.types import ToolMetadata
from llama_index.core.agent.react.base import ReActAgent
from llama_index.core.chat_engine.types import AgentChatResponse
from llama_index.llms.openai import OpenAI

import chainlit as cl
from chainlit.input_widget import Select, TextInput
import openai

from index_wikipages import create_index
from utils import get_apikey

index = None
agent = None

@cl.on_chat_start
async def on_chat_start():
    await cl.Message(
        content="# 👋 Meet Elobot\n\nYour in-house AI assistant powered by GPT + Wikipedia + Chainlit."
    ).send()
    await cl.ChatSettings(
        [
            Select(
                id="MODEL",
                label="OpenAI - Model",
                values=["gpt-3.5-turbo"],
                initial_index=0,
            ),
            TextInput(id="WikiPageRequest", label="Request Wikipage"),
        ]
    ).send()

def wikisearch_engine(index):
    return index.as_query_engine(
        response_mode="compact", verbose=True, similarity_top_k=10
    )

def create_react_agent(model_name: str):
    global index
    if index is None:
        raise ValueError("Index is not initialized.")

    query_engine_tools = [
        QueryEngineTool(
            query_engine=wikisearch_engine(index),
            metadata=ToolMetadata(
                name="Wikipedia",
                description="Useful for performing searches on the Wikipedia knowledgebase",
            ),
        )
    ]

    openai.api_key = get_apikey()
    llm = OpenAI(model=model_name)
    agent = ReActAgent.from_tools(
        tools=query_engine_tools,
        llm=llm,
        verbose=True,
    )
    return agent

@cl.on_settings_update
async def setup_agent(settings):
    global agent, index

    query = settings.get("WikiPageRequest", "")
    model_name = settings.get("MODEL", "gpt-3.5-turbo")

    if not query:
        await cl.Message(content="\u26a0\ufe0f Please enter a Wikipedia page to index.").send()
        return

    index = create_index(query)
    print(f"\u2705 Index created for page: {query}")

    agent = create_react_agent(model_name)
    await cl.Message(
        author="Agent", content=f"\u2705 Wikipage(s) **\"{query}\"** successfully indexed and ready!"
    ).send()

@cl.on_message
async def main(message: cl.Message):
    global agent
    if not agent:
        await cl.Message(content="Agent is not available yet. Try updating settings first.").send()
        return

    print("Received message:", message.content)
    try:
        response = await cl.make_async(agent.chat)(message.content)
        final_content = (
            response.response
            if isinstance(response, AgentChatResponse)
            else str(response)
        )
        await cl.Message(author="Agent", content=final_content).send()
    except Exception as e:
        print("\u274c Error while querying agent:", e)
        await cl.Message(content=f"\u274c Error: {e}").send()