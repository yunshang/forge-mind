from dataclasses import asdict

from litestar import delete, get, post
from litestar.exceptions import NotFoundException
from pydantic import BaseModel

from backend.agents import Orchestrator
from backend.store import session_store


class CreateSessionRequest(BaseModel):
    name: str = ""


class GenerateInSessionRequest(BaseModel):
    prompt: str


@post("/api/sessions")
async def create_session(data: CreateSessionRequest) -> dict:
    session = session_store.create_session(name=data.name)
    return session.to_dict()


@get("/api/sessions")
async def list_sessions() -> list[dict]:
    sessions = session_store.list_sessions()
    return [s.to_summary() for s in sessions]


@get("/api/sessions/{session_id:str}")
async def get_session(session_id: str) -> dict:
    session = session_store.get_session(session_id)
    if not session:
        raise NotFoundException(f"Session {session_id} not found")
    return session.to_dict()


@delete("/api/sessions/{session_id:str}", status_code=200)
async def delete_session(session_id: str) -> dict:
    if not session_store.delete_session(session_id):
        raise NotFoundException(f"Session {session_id} not found")
    return {"status": "deleted"}


@post("/api/sessions/{session_id:str}/generate")
async def generate_in_session(session_id: str, data: GenerateInSessionRequest) -> dict:
    session = session_store.get_session(session_id)
    if not session:
        raise NotFoundException(f"Session {session_id} not found")

    # Add user message to history
    session_store.add_message(session_id, "user", data.prompt)

    # Build conversation history for orchestrator
    history = [m.to_dict() for m in session.messages]

    # Run orchestrator with history context
    orchestrator = Orchestrator()
    result = await orchestrator.run(
        prompt=data.prompt,
        conversation_history=history,
    )

    # Build result dict
    result_dict = {
        "status": result.status,
        "contract_name": result.contract_name,
        "solidity_code": result.solidity_code,
        "constructor_args": result.constructor_args,
        "description": result.description,
        "audit_result": result.audit_result,
        "graph_data": result.graph_data,
        "sandbox_result": result.sandbox_result,
        "logs": result.logs,
        "iterations": result.iterations,
        "error": result.error,
        "session_id": session_id,
    }

    # Add assistant summary to history
    if result.status == "success":
        summary = (
            f"Generated contract: {result.contract_name}\n"
            f"Audit: {result.audit_result.get('status', 'N/A')}\n"
            f"Sandbox: {result.sandbox_result.get('status', 'N/A')}"
        )
    else:
        summary = f"Error: {result.error}"
    session_store.add_message(session_id, "assistant", summary)

    # Update session's current result
    session_store.update_result(session_id, result_dict)

    return result_dict
