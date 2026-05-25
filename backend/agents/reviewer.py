from backend.skills import SecurityAuditSkill


class ReviewerAgent:
    """Agent responsible for auditing generated Solidity code."""

    def __init__(self) -> None:
        self.skill = SecurityAuditSkill()

    async def review(self, solidity_code: str, contract_name: str = "") -> dict:
        result = await self.skill.execute(solidity_code=solidity_code, contract_name=contract_name)
        return {
            "agent": "reviewer",
            "action": "audit",
            "status": result["status"],
            "vulnerabilities": result["vulnerabilities"],
        }

    def format_feedback(self, audit_result: dict) -> str:
        """Format audit result as feedback string for the coder agent."""
        if audit_result["status"] == "PASS":
            return ""

        feedback_lines = ["The following security issues were found:"]
        for vuln in audit_result["vulnerabilities"]:
            feedback_lines.append(
                f"- [{vuln['severity'].upper()}] {vuln['vulnerability']}: "
                f"{vuln['description']} (Location: {vuln['location']})"
            )
        return "\n".join(feedback_lines)
