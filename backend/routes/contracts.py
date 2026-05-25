from dataclasses import asdict

from litestar import post
from pydantic import BaseModel

from backend.agents import Orchestrator


class GenerateRequest(BaseModel):
    prompt: str


class GenerateResponse(BaseModel):
    status: str
    contract_name: str = ""
    solidity_code: str = ""
    constructor_args: list = []
    description: str = ""
    audit_result: dict = {}
    graph_data: dict = {}
    sandbox_result: dict = {}
    logs: list = []
    iterations: int = 0
    error: str = ""


@post("/api/contracts/generate")
async def generate_contract(data: GenerateRequest) -> GenerateResponse:
    orchestrator = Orchestrator()
    result = await orchestrator.run(prompt=data.prompt)

    return GenerateResponse(
        status=result.status,
        contract_name=result.contract_name,
        solidity_code=result.solidity_code,
        constructor_args=result.constructor_args,
        description=result.description,
        audit_result=result.audit_result,
        graph_data=result.graph_data,
        sandbox_result=result.sandbox_result,
        logs=[asdict(log) for log in result.logs] if hasattr(result.logs[0], "__dataclass_fields__") else result.logs,
        iterations=result.iterations,
        error=result.error,
    )
