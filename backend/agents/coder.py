from backend.skills import SolidityGenerationSkill


class CoderAgent:
    """Agent responsible for generating Solidity code from natural language."""

    def __init__(self) -> None:
        self.skill = SolidityGenerationSkill()

    async def generate(self, prompt: str, feedback: str | None = None) -> dict:
        result = await self.skill.execute(prompt=prompt, feedback=feedback)
        return {
            "agent": "coder",
            "action": "generate",
            "contract_name": result["contract_name"],
            "solidity_code": result["solidity_code"],
            "constructor_args": result["constructor_args"],
            "description": result["description"],
        }
