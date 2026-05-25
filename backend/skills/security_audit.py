import re
from dataclasses import dataclass, field

from .base import BaseSkill


@dataclass
class Vulnerability:
    severity: str  # "high", "medium", "low", "informational"
    vulnerability: str
    location: str
    description: str


@dataclass
class AuditResult:
    status: str  # "PASS" or "FAIL"
    vulnerabilities: list[Vulnerability] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "vulnerabilities": [
                {
                    "severity": v.severity,
                    "vulnerability": v.vulnerability,
                    "location": v.location,
                    "description": v.description,
                }
                for v in self.vulnerabilities
            ],
        }


REENTRANCY_PATTERN = re.compile(
    r"\.call\{.*value.*\}\(|\.call\.value\(|\.send\(|\.transfer\(", re.IGNORECASE
)
MISSING_ACCESS_CONTROL = re.compile(
    r"function\s+\w+\s*\([^)]*\)\s*(?:external|public)\s+(?!view|pure|onlyOwner|onlyRole)",
    re.IGNORECASE,
)
UNSAFE_DELEGATECALL = re.compile(r"\.delegatecall\(", re.IGNORECASE)
TX_ORIGIN = re.compile(r"tx\.origin", re.IGNORECASE)
UNSAFE_SELFDESTRUCT = re.compile(r"selfdestruct\(", re.IGNORECASE)
FLOATING_PRAGMA = re.compile(r"pragma\s+solidity\s*\^", re.IGNORECASE)
MISSING_ZERO_CHECK = re.compile(r"function\s+\w*\s*\([^)]*address\s+(\w+)", re.IGNORECASE)


class SecurityAuditSkill(BaseSkill):
    name = "security_audit"
    description = "Static analysis of Solidity code for common vulnerabilities"

    async def execute(self, *, solidity_code: str, contract_name: str = "") -> dict:
        vulnerabilities: list[Vulnerability] = []

        self._check_reentrancy(solidity_code, vulnerabilities)
        self._check_access_control(solidity_code, vulnerabilities)
        self._check_delegatecall(solidity_code, vulnerabilities)
        self._check_tx_origin(solidity_code, vulnerabilities)
        self._check_selfdestruct(solidity_code, vulnerabilities)
        self._check_pragma(solidity_code, vulnerabilities)
        self._check_arithmetic(solidity_code, vulnerabilities)
        self._check_event_emission(solidity_code, vulnerabilities)

        has_high = any(v.severity == "high" for v in vulnerabilities)
        status = "FAIL" if has_high else "PASS"

        result = AuditResult(status=status, vulnerabilities=vulnerabilities)
        return result.to_dict()

    def _check_reentrancy(self, code: str, vulns: list[Vulnerability]) -> None:
        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            if REENTRANCY_PATTERN.search(line):
                vulns.append(
                    Vulnerability(
                        severity="high",
                        vulnerability="Reentrancy Risk",
                        location=f"line {i}",
                        description="External call detected before state update. Follow checks-effects-interactions pattern.",
                    )
                )

    def _check_access_control(self, code: str, vulns: list[Vulnerability]) -> None:
        public_funcs = MISSING_ACCESS_CONTROL.finditer(code)
        for match in public_funcs:
            func_name = match.group()
            if "view" not in func_name and "pure" not in func_name:
                vulns.append(
                    Vulnerability(
                        severity="medium",
                        vulnerability="Missing Access Control",
                        location=func_name.strip()[:60],
                        description="Public/state-changing function without access control modifier.",
                    )
                )

    def _check_delegatecall(self, code: str, vulns: list[Vulnerability]) -> None:
        if UNSAFE_DELEGATECALL.search(code):
            vulns.append(
                Vulnerability(
                    severity="high",
                    vulnerability="Unsafe Delegatecall",
                    location="contract body",
                    description="delegatecall to user-controlled address can lead to storage collision attacks.",
                )
            )

    def _check_tx_origin(self, code: str, vulns: list[Vulnerability]) -> None:
        if TX_ORIGIN.search(code):
            vulns.append(
                Vulnerability(
                    severity="high",
                    vulnerability="tx.origin Authentication",
                    location="contract body",
                    description="Using tx.origin for authentication is vulnerable to phishing attacks. Use msg.sender instead.",
                )
            )

    def _check_selfdestruct(self, code: str, vulns: list[Vulnerability]) -> None:
        if UNSAFE_SELFDESTRUCT.search(code):
            vulns.append(
                Vulnerability(
                    severity="high",
                    vulnerability="Selfdestruct Usage",
                    location="contract body",
                    description="selfdestruct can forcibly destroy the contract. Ensure strict access control.",
                )
            )

    def _check_pragma(self, code: str, vulns: list[Vulnerability]) -> None:
        if FLOATING_PRAGMA.search(code):
            vulns.append(
                Vulnerability(
                    severity="low",
                    vulnerability="Floating Pragma",
                    location="pragma statement",
                    description="Lock pragma to a specific version to prevent unexpected behavior with compiler updates.",
                )
            )

    def _check_arithmetic(self, code: str, vulns: list[Vulnerability]) -> None:
        unchecked = re.search(r"unchecked\s*\{", code)
        if unchecked:
            vulns.append(
                Vulnerability(
                    severity="medium",
                    vulnerability="Unchecked Arithmetic",
                    location="unchecked block",
                    description="Ensure arithmetic in unchecked blocks cannot overflow/underflow.",
                )
            )

    def _check_event_emission(self, code: str, vulns: list[Vulnerability]) -> None:
        state_changes = re.findall(r"function\s+(\w+)", code)
        emit_count = len(re.findall(r"emit\s+\w+", code))
        if state_changes and emit_count == 0:
            vulns.append(
                Vulnerability(
                    severity="low",
                    vulnerability="Missing Events",
                    location="contract",
                    description="State-changing functions should emit events for off-chain tracking.",
                )
            )
