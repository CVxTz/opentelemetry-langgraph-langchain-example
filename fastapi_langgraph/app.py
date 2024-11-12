import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from langchain_core.messages import HumanMessage
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel, Field

from fastapi_langgraph.agent import OverallState, build_agent

logging.basicConfig(level=logging.NOTSET)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Query(BaseModel):
    thread_id: str = Field(
        ..., description="Unique identifier for the conversation thread."
    )
    message: str = Field(..., description="User's message.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "thread_id": "conversation_123",
                    "message": "What is the capital of France?",
                }
            ]
        }
    }


class Response(BaseModel):
    message: str = Field(..., description="Agent's response.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run at startup. Initialise the agent and add it to request.state."""
    agent = build_agent(local_memory=True)
    yield {"agent": agent}


app = FastAPI(lifespan=lifespan)


@app.post("/chat", response_model=Response, response_model_exclude_none=True)
def chat_route(query: Query, request: Request) -> Response:
    """Handles chat requests."""
    try:
        thread_id = query.thread_id
        logger.info(f"Started processing {thread_id=}")
        message = query.message
        agent: CompiledGraph = request.state.agent

        config = {"configurable": {"thread_id": thread_id}}

        new_state = OverallState(messages=[HumanMessage(content=message)])

        final_state_dict = agent.invoke(new_state, config=config)

        final_state = OverallState(**final_state_dict)

        if not final_state.messages or not isinstance(final_state.messages, list):
            raise HTTPException(
                status_code=500, detail="Agent failed to generate a response."
            )

        response_message = final_state.messages[-1].content
        return Response(message=response_message)

    except Exception as e:
        logger.error("Processing failed")
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
