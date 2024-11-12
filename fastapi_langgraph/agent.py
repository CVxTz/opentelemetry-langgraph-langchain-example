import logging
import os
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langchain_fireworks import ChatFireworks
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from opentelemetry import metrics, trace
from pydantic import BaseModel

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

meter = metrics.get_meter("opentelemetry.instrumentation.custom")

input_tokens_counter = meter.create_counter(
    "tokens.input", unit="tokens", description="Input tokens"
)
output_tokens_counter = meter.create_counter(
    "tokens.output", unit="tokens", description="Output tokens"
)

dot_env_path = Path(__file__).parents[1] / ".env"
if dot_env_path.is_file():
    load_dotenv(dotenv_path=dot_env_path)

LLM_API_KEY = os.environ.get("LLM_API_KEY")

client_large = ChatFireworks(
    api_key=LLM_API_KEY,
    model="accounts/fireworks/models/llama-v3p1-70b-instruct",
    temperature=0,
)

wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
tools = [wikipedia]
tools_node = ToolNode(tools=tools)

tools_node.invoke = trace.get_tracer(
    "opentelemetry.instrumentation.custom"
).start_as_current_span("tool_call")(tools_node.invoke)


class OverallState(BaseModel):
    messages: Annotated[list[AnyMessage], add_messages]


@trace.get_tracer("opentelemetry.instrumentation.custom").start_as_current_span(
    "query_llm"
)
def query_llm(state: OverallState) -> dict:
    local_client = client_large.bind_tools(tools)
    result = local_client.invoke(
        [
            SystemMessage(
                content="You are a helpful assistant. Use the wikipedia tool when necessary."
            )
        ]
        + state.messages
    )
    trace.get_current_span().set_attribute("query", state.messages[-1].content)
    trace.get_current_span().set_attribute("response", result.content)

    input_tokens_counter.add(
        result.usage_metadata["input_tokens"], {"model": client_large.model_name}
    )
    output_tokens_counter.add(
        result.usage_metadata["output_tokens"], {"model": client_large.model_name}
    )

    return {"messages": [result]}


@trace.get_tracer("opentelemetry.instrumentation.custom").start_as_current_span(
    "should_we_stop"
)
def should_we_stop(state: OverallState) -> str:
    logger.debug(
        f"Entering should_we_stop function. Current state: {state}"
    )  # Added log
    if state.messages[-1].tool_calls:
        logger.info(f"Calling tools: {state.messages[-1].tool_calls}")
        return "tools"
    else:
        logger.debug("Ending agent invocation")
        return END


def build_agent(local_memory=True):
    workflow = StateGraph(OverallState)

    # Add nodes
    workflow.add_node("llm", query_llm)
    workflow.add_node("tools", tools_node)

    # Add edges
    workflow.add_edge(START, "llm")
    workflow.add_conditional_edges("llm", should_we_stop)
    workflow.add_edge("tools", "llm")

    agent = workflow.compile(
        checkpointer=MemorySaver() if local_memory else None
    )  # Change to Db memory for prod

    agent.invoke = trace.get_tracer(
        "opentelemetry.instrumentation.custom"
    ).start_as_current_span("agent_invoke")(agent.invoke)

    return agent


if __name__ == "__main__":
    _agent = build_agent(local_memory=True)

    _agent.invoke = trace.get_tracer(
        "opentelemetry.instrumentation.custom"
    ).start_as_current_span("agent_invoke")(_agent.invoke)

    initial_state = OverallState(
        messages=[HumanMessage(content="Explain latent diffusion")]
    )

    config = {"configurable": {"thread_id": "1"}}

    state_dict = _agent.invoke(initial_state, config=config)

    state = OverallState(**state_dict)

    for message in state.messages:
        print(message)

    new_state = OverallState(messages=[HumanMessage(content="Explain game theory")])

    final_state_dict = _agent.invoke(new_state, config=config)

    final_state = OverallState(**final_state_dict)

    for message in final_state.messages:
        print(message.type, message)
