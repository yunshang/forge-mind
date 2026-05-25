from litestar import post
from pydantic import BaseModel

from backend.skills.ast_visual import AstVisualSkill


class VisualizeRequest(BaseModel):
    solidity_code: str
    contract_name: str = ""


class VisualizeResponse(BaseModel):
    status: str
    graph_data: dict = {}
    error: str = ""


@post("/api/contracts/visualize")
async def visualize_contract(data: VisualizeRequest) -> VisualizeResponse:
    try:
        skill = AstVisualSkill()
        graph_data = await skill.execute(
            solidity_code=data.solidity_code,
            contract_name=data.contract_name,
        )
        return VisualizeResponse(
            status="success",
            graph_data=graph_data,
        )
    except Exception as e:
        return VisualizeResponse(
            status="error",
            error=str(e),
        )
