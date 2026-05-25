import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

from backend.config import settings
from backend.skills import AstVisualSkill, SandboxSimulationSkill

from .coder import CoderAgent
from .reviewer import ReviewerAgent


@dataclass
class AgentLog:
    agent: str
    message: str
    level: str = "info"  # info, warn, error, success


@dataclass
class OrchestrationResult:
    status: str  # "success" or "error"
    contract_name: str = ""
    solidity_code: str = ""
    constructor_args: list = field(default_factory=list)
    description: str = ""
    audit_result: dict = field(default_factory=dict)
    graph_data: dict = field(default_factory=dict)
    sandbox_result: dict = field(default_factory=dict)
    logs: list[dict] = field(default_factory=list)
    iterations: int = 0
    error: str = ""


class Orchestrator:
    """Orchestrates coder and reviewer agents with self-healing loop."""

    def __init__(self) -> None:
        self.coder = CoderAgent()
        self.reviewer = ReviewerAgent()
        self.ast_skill = AstVisualSkill()
        self.sandbox_skill = SandboxSimulationSkill()

    async def run(
        self,
        prompt: str,
        on_log: Callable[[AgentLog], Awaitable[None]] | None = None,
        conversation_history: list[dict] | None = None,
    ) -> OrchestrationResult:
        logs: list[dict] = []

        async def log(agent: str, message: str, level: str = "info") -> None:
            entry = {"agent": agent, "message": message, "level": level}
            logs.append(entry)
            if on_log:
                await on_log(AgentLog(agent=agent, message=message, level=level))

        await log("orchestrator", f"Starting contract generation for: {prompt[:80]}...")

        # Build context from conversation history
        context_prefix = ""
        if conversation_history:
            context_lines = ["Previous conversation context:"]
            for msg in conversation_history[-6:]:  # Last 6 messages for context
                context_lines.append(f"{msg['role']}: {msg['content'][:200]}")
            context_prefix = "\n".join(context_lines) + "\n\n"

        feedback = None
        code_result = None

        for iteration in range(1, settings.max_healing_iterations + 1):
            await log("coder", f"Iteration {iteration}: Generating Solidity code...", "info")

            try:
                full_prompt = context_prefix + prompt if context_prefix else prompt
                code_result = await self.coder.generate(full_prompt, feedback)
            except Exception as e:
                await log("coder", f"Generation failed: {e}", "error")
                return OrchestrationResult(status="error", error=str(e), logs=logs, iterations=iteration)

            await log("coder", f"Generated contract: {code_result['contract_name']}", "success")

            # Audit
            await log("reviewer", "Running security audit...", "info")
            try:
                audit_result = await self.reviewer.review(
                    code_result["solidity_code"], code_result["contract_name"]
                )
            except Exception as e:
                await log("reviewer", f"Audit failed: {e}", "error")
                return OrchestrationResult(status="error", error=str(e), logs=logs, iterations=iteration)

            if audit_result["status"] == "PASS":
                await log("reviewer", "Audit PASSED - no high-severity issues found", "success")
                break
            else:
                high_count = sum(
                    1 for v in audit_result["vulnerabilities"] if v["severity"] == "high"
                )
                total = len(audit_result["vulnerabilities"])
                await log(
                    "reviewer",
                    f"Audit found {total} issues ({high_count} high severity). Requesting fix...",
                    "warn",
                )
                feedback = self.reviewer.format_feedback(audit_result)

                if iteration == settings.max_healing_iterations:
                    await log("orchestrator", "Max iterations reached. Returning last version.", "warn")
                    break
        else:
            audit_result = {"status": "UNKNOWN", "vulnerabilities": []}

        # Visualize
        await log("orchestrator", "Generating contract topology graph...", "info")
        try:
            graph_data = await self.ast_skill.execute(
                solidity_code=code_result["solidity_code"],
                contract_name=code_result["contract_name"],
            )
            await log("orchestrator", f"Graph generated: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges", "success")
        except Exception as e:
            await log("orchestrator", f"Graph generation failed: {e}", "warn")
            graph_data = {"nodes": [], "edges": []}

        # Deploy to sandbox
        await log("orchestrator", "Deploying to Anvil sandbox...", "info")
        try:
            sandbox_result = await self.sandbox_skill.execute(
                solidity_code=code_result["solidity_code"],
                contract_name=code_result["contract_name"],
                constructor_args=code_result.get("constructor_args"),
            )
            if sandbox_result.get("status") == "success":
                await log("orchestrator", f"Deployed at {sandbox_result['contract_address']}", "success")
            else:
                await log("orchestrator", f"Deployment issue: {sandbox_result.get('error', 'unknown')}", "warn")
        except Exception as e:
            await log("orchestrator", f"Sandbox deployment failed: {e}", "warn")
            sandbox_result = {"status": "error", "error": str(e)}

        return OrchestrationResult(
            status="success",
            contract_name=code_result["contract_name"],
            solidity_code=code_result["solidity_code"],
            constructor_args=code_result.get("constructor_args", []),
            description=code_result.get("description", ""),
            audit_result=audit_result,
            graph_data=graph_data,
            sandbox_result=sandbox_result,
            logs=logs,
            iterations=iteration,
        )
