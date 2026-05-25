import json
from unittest.mock import MagicMock, patch

import pytest

from backend.skills.sandbox_simulation import SandboxSimulationSkill


@pytest.fixture
def skill():
    return SandboxSimulationSkill()


MOCK_ABI = [
    {
        "type": "function",
        "name": "balanceOf",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
    },
    {
        "type": "function",
        "name": "transfer",
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
    },
    {
        "type": "constructor",
        "inputs": [{"name": "name", "type": "string"}],
    },
    {
        "type": "event",
        "name": "Transfer",
        "inputs": [],
    },
]


class TestExtractFunctions:
    def test_extracts_only_functions(self, skill: SandboxSimulationSkill):
        result = skill._extract_functions(MOCK_ABI)

        assert len(result) == 2
        names = [f["name"] for f in result]
        assert "balanceOf" in names
        assert "transfer" in names

    def test_view_function_marked_as_read(self, skill: SandboxSimulationSkill):
        result = skill._extract_functions(MOCK_ABI)
        balance_of = next(f for f in result if f["name"] == "balanceOf")

        assert balance_of["isRead"] is True
        assert balance_of["stateMutability"] == "view"

    def test_write_function_not_marked_as_read(self, skill: SandboxSimulationSkill):
        result = skill._extract_functions(MOCK_ABI)
        transfer = next(f for f in result if f["name"] == "transfer")

        assert transfer["isRead"] is False
        assert transfer["stateMutability"] == "nonpayable"

    def test_inputs_parsed(self, skill: SandboxSimulationSkill):
        result = skill._extract_functions(MOCK_ABI)
        transfer = next(f for f in result if f["name"] == "transfer")

        assert len(transfer["inputs"]) == 2
        assert transfer["inputs"][0]["name"] == "to"
        assert transfer["inputs"][0]["type"] == "address"

    def test_empty_abi(self, skill: SandboxSimulationSkill):
        result = skill._extract_functions([])
        assert result == []


class TestCompile:
    @patch("backend.skills.sandbox_simulation.subprocess.run")
    def test_compile_success(self, mock_run: MagicMock, skill: SandboxSimulationSkill):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "contracts": {
                    "test.sol:TestContract": {
                        "abi": json.dumps(MOCK_ABI),
                        "bin": "0x6080604052",
                    }
                }
            }),
            stderr="",
        )

        result = skill._compile("pragma solidity 0.8.20; contract TestContract {}", "TestContract")

        assert "abi" in result
        assert "bytecode" in result
        assert len(result["abi"]) == 4

    @patch("backend.skills.sandbox_simulation.subprocess.run")
    def test_compile_failure(self, mock_run: MagicMock, skill: SandboxSimulationSkill):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error: Expected identifier")

        result = skill._compile("invalid code", "Bad")

        assert "error" in result
        assert "Compilation failed" in result["error"]

    @patch("backend.skills.sandbox_simulation.subprocess.run", side_effect=FileNotFoundError)
    def test_compile_solc_not_found(self, mock_run: MagicMock, skill: SandboxSimulationSkill):
        result = skill._compile("code", "C")

        assert "error" in result
        assert "solc not found" in result["error"]


class TestDeploy:
    def test_deploy_success(self, skill: SandboxSimulationSkill):
        mock_w3 = MagicMock()
        mock_w3.eth.accounts = ["0xabc"]
        mock_w3.eth.get_transaction_count.return_value = 0
        mock_w3.eth.gas_price = 1000000000

        mock_receipt = {"contractAddress": "0x1234"}
        mock_w3.eth.wait_for_transaction_receipt.return_value = mock_receipt
        mock_w3.eth.send_transaction.return_value = MagicMock(hex=lambda: "0xdeadbeef")

        mock_contract = MagicMock()
        mock_contract.constructor.return_value.build_transaction.return_value = {"data": "0x"}
        mock_w3.eth.contract.return_value = mock_contract

        result = skill._deploy(mock_w3, MOCK_ABI, "0x6080", [])

        assert result["address"] == "0x1234"
        assert result["tx_hash"] == "0xdeadbeef"

    def test_deploy_with_constructor_args(self, skill: SandboxSimulationSkill):
        mock_w3 = MagicMock()
        mock_w3.eth.accounts = ["0xabc"]
        mock_w3.eth.get_transaction_count.return_value = 0
        mock_w3.eth.gas_price = 1000000000

        mock_receipt = {"contractAddress": "0x1234"}
        mock_w3.eth.wait_for_transaction_receipt.return_value = mock_receipt
        mock_w3.eth.send_transaction.return_value = MagicMock(hex=lambda: "0xdeadbeef")

        mock_contract = MagicMock()
        mock_contract.constructor.return_value.build_transaction.return_value = {"data": "0x"}
        mock_w3.eth.contract.return_value = mock_contract

        result = skill._deploy(mock_w3, MOCK_ABI, "0x6080", ["TestToken"])

        assert result["address"] == "0x1234"
        mock_contract.constructor.assert_called_once_with("TestToken")
