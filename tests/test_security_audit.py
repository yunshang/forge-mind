import pytest

from backend.skills.security_audit import SecurityAuditSkill
from tests.conftest import SAMPLE_ERC20, SAMPLE_MINIMAL, SAMPLE_VULNERABLE


@pytest.fixture
def skill():
    return SecurityAuditSkill()


class TestSecurityAudit:
    async def test_vulnerable_contract_fails_audit(self, skill: SecurityAuditSkill):
        result = await skill.execute(solidity_code=SAMPLE_VULNERABLE, contract_name="Vulnerable")

        assert result["status"] == "FAIL"
        severities = [v["severity"] for v in result["vulnerabilities"]]
        assert "high" in severities

    async def test_vulnerable_contract_detects_reentrancy(self, skill: SecurityAuditSkill):
        result = await skill.execute(solidity_code=SAMPLE_VULNERABLE, contract_name="Vulnerable")
        vuln_names = [v["vulnerability"] for v in result["vulnerabilities"]]

        assert "Reentrancy Risk" in vuln_names

    async def test_vulnerable_contract_detects_selfdestruct(self, skill: SecurityAuditSkill):
        result = await skill.execute(solidity_code=SAMPLE_VULNERABLE, contract_name="Vulnerable")
        vuln_names = [v["vulnerability"] for v in result["vulnerabilities"]]

        assert "Selfdestruct Usage" in vuln_names

    async def test_vulnerable_contract_detects_tx_origin(self, skill: SecurityAuditSkill):
        result = await skill.execute(solidity_code=SAMPLE_VULNERABLE, contract_name="Vulnerable")
        vuln_names = [v["vulnerability"] for v in result["vulnerabilities"]]

        assert "tx.origin Authentication" in vuln_names

    async def test_minimal_contract_passes_audit(self, skill: SecurityAuditSkill):
        result = await skill.execute(solidity_code=SAMPLE_MINIMAL, contract_name="SimpleStorage")

        assert result["status"] == "PASS"
        # Should have no high-severity issues
        high_vulns = [v for v in result["vulnerabilities"] if v["severity"] == "high"]
        assert len(high_vulns) == 0

    async def test_floating_pragma_detected(self, skill: SecurityAuditSkill):
        code = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Foo {
    function bar() external {}
}
"""
        result = await skill.execute(solidity_code=code, contract_name="Foo")
        vuln_names = [v["vulnerability"] for v in result["vulnerabilities"]]

        assert "Floating Pragma" in vuln_names

    async def test_missing_events_detected(self, skill: SecurityAuditSkill):
        code = """// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

contract NoEvents {
    uint256 public x;

    function setX(uint256 _x) external {
        x = _x;
    }
}
"""
        result = await skill.execute(solidity_code=code, contract_name="NoEvents")
        vuln_names = [v["vulnerability"] for v in result["vulnerabilities"]]

        assert "Missing Events" in vuln_names

    async def test_unchecked_arithmetic_detected(self, skill: SecurityAuditSkill):
        code = """// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

contract Unchecked {
    function add(uint256 a, uint256 b) external pure returns (uint256) {
        unchecked {
            return a + b;
        }
    }
}
"""
        result = await skill.execute(solidity_code=code, contract_name="Unchecked")
        vuln_names = [v["vulnerability"] for v in result["vulnerabilities"]]

        assert "Unchecked Arithmetic" in vuln_names

    async def test_result_structure(self, skill: SecurityAuditSkill):
        result = await skill.execute(solidity_code=SAMPLE_MINIMAL, contract_name="SimpleStorage")

        assert "status" in result
        assert "vulnerabilities" in result
        assert isinstance(result["vulnerabilities"], list)
        for vuln in result["vulnerabilities"]:
            assert "severity" in vuln
            assert "vulnerability" in vuln
            assert "location" in vuln
            assert "description" in vuln

    async def test_empty_code(self, skill: SecurityAuditSkill):
        result = await skill.execute(solidity_code="", contract_name="Empty")
        assert result["status"] == "PASS"
