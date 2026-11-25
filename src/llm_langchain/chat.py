from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import InMemorySaver
from langsmith import uuid7

from src.llm_langchain.changelog import Changelog
from src.llm_langchain.llm_config import SYSTEM_PROMPT, SUMMARIZE_PROMPT
from src.llm_langchain.llm_config import create_model
from src.llm_langchain.tools import find_product, substitute, answer_source

prompt_conv = ChatPromptTemplate.from_messages([
    ("human", "{message}")
])
model = create_model()
sum_model = SummarizationMiddleware(model=model, trigger=("messages", 10), keep=("messages", 2),
                                    summary_prompt=SUMMARIZE_PROMPT)

agent = create_agent(model=model, tools=[find_product, substitute, answer_source], system_prompt=SYSTEM_PROMPT,
                     middleware=[sum_model], checkpointer=InMemorySaver())


def call_llm(message, config):
    messages = prompt_conv.invoke({"message": message}).to_messages()
    try:
        yield f"\n{model.model} > "
        for token, metadata in agent.stream({"messages": messages}, config=config, stream_mode="messages"):
            if token.content and metadata.get("langgraph_node") == "model":
                yield token.content
    except NotImplementedError as e:
        yield f"Une erreur est survenue : {e}"


def talk_to_llm() -> str:
    changelog = Changelog()
    config = {
        "configurable": {
            "thread_id": str(uuid7()),
        },
        "callbacks": [changelog]
    }
    message = "Bonjour, dis moi ce que tu peux faire."
    print("".join(call_llm(message, config)))
    while True:
        message = input(f"\nVous > ").strip()
        for msg in call_llm(message, config) :
            print(msg, end="", flush=True)
        print(changelog.rows)


if __name__ == '__main__':
    print()
    talk_to_llm()
