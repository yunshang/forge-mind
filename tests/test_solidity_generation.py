import json
from unittest.mock import MagicMock, patch

import pytest

from backend.skills.solidity_generation import SolidityGenerationSkill


@pytest.fixture
def skill():
    return SolidityGenerationSkill()


MOCK_LLM_RESPONSE = {
    "contract_name": "TestToken",
    "solidity_code": "// SPDX-License-Identifier: MIT\\npragma solidity ^0.8.20;\\n\\ncontract TestToken {\\n    uint256 public totalSupply;\\n}",
    "constructor_args": ["Initial supply as uint256"],
    "description": "A simple ERC20 test token",
}


class TestSolidityGenerationParse:
    def test_parse_valid_json(self, skill: SolidityGenerationSkill):
        raw = json.dumps(MOCK_LLM_RESPONSE)
        result = skill._parse_response(raw)

        assert result["contract_name"] == "TestToken"
        assert "pragma solidity" in result["solidity_code"]
        assert "\n" in result["solidity_code"]  # newlines should be unescaped
        assert len(result["constructor_args"]) == 1

    def test_parse_json_with_markdown_fences(self, skill: SolidityGenerationSkill):
        raw = f"```json\n{json.dumps(MOCK_LLM_RESPONSE)}\n```"
        result = skill._parse_response(raw)

        assert result["contract_name"] == "TestToken"

    def test_parse_json_with_surrounding_text(self, skill: SolidityGenerationSkill):
        raw = f"Here is the contract:\n{json.dumps(MOCK_LLM_RESPONSE)}\nDone."
        result = skill._parse_response(raw)

        assert result["contract_name"] == "TestToken"

    def test_parse_invalid_json_returns_empty(self, skill: SolidityGenerationSkill):
        """Parser gracefully handles completely invalid input."""
        result = skill._parse_response("this is not json at all")
        assert result["contract_name"] == "Unknown"
        assert result["solidity_code"] == ""

    def test_parse_preserves_code_formatting(self, skill: SolidityGenerationSkill):
        response = {
            "contract_name": "Foo",
            "solidity_code": "line1\\nline2\\n\\tindented",
            "constructor_args": [],
            "description": "test",
        }
        result = skill._parse_response(json.dumps(response))

        assert result["solidity_code"] == "line1\nline2\n\tindented"

    def test_parse_missing_fields_use_defaults(self, skill: SolidityGenerationSkill):
        raw = '{"contract_name": "Bar", "solidity_code": "code"}'
        result = skill._parse_response(raw)

        assert result["contract_name"] == "Bar"
        assert result["constructor_args"] == []
        assert result["description"] == ""

    def test_parse_literal_newlines_in_code(self, skill: SolidityGenerationSkill):
        """MiMo responses often have literal newlines inside JSON string values."""
        raw = (
            '{\n'
            '  "contract_name": "NFTAuction",\n'
            '  "solidity_code": "// SPDX-License-Identifier: MIT\n'
            'pragma solidity ^0.8.20;\n'
            '\n'
            'contract NFTAuction {\n'
            '    uint256 public highestBid;\n'
            '}",\n'
            '  "constructor_args": ["NFT address"],\n'
            '  "description": "An NFT auction contract"\n'
            '}'
        )
        result = skill._parse_response(raw)

        assert result["contract_name"] == "NFTAuction"
        assert "pragma solidity" in result["solidity_code"]
        assert "contract NFTAuction" in result["solidity_code"]
        assert "highestBid" in result["solidity_code"]
        assert result["constructor_args"] == ["NFT address"]
        assert result["description"] == "An NFT auction contract"

    def test_parse_literal_newlines_with_escaped_quotes(self, skill: SolidityGenerationSkill):
        """Code containing escaped quotes (e.g. import paths) with literal newlines."""
        raw = (
            '{\n'
            '  "contract_name": "Foo",\n'
            '  "solidity_code": "// SPDX-License-Identifier: MIT\\npragma solidity ^0.8.20;\\n\\nimport \\"@openzeppelin/contracts/token/ERC721/IERC721.sol\\";\\n\\ncontract Foo {\\n    uint256 x;\\n}",\n'
            '  "constructor_args": [],\n'
            '  "description": "test"\n'
            '}'
        )
        result = skill._parse_response(raw)

        assert result["contract_name"] == "Foo"
        assert "pragma solidity" in result["solidity_code"]
        assert "IERC721" in result["solidity_code"]


class TestSolidityGenerationExecute:
    @patch("backend.skills.solidity_generation.anthropic.Anthropic")
    async def test_execute_calls_llm(self, mock_anthropic_cls: MagicMock, skill: SolidityGenerationSkill):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(MOCK_LLM_RESPONSE))]
        mock_client.messages.create.return_value = mock_response

        result = await skill.execute(prompt="Create a test token")

        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs["model"] is not None
        assert "Create a test token" in call_kwargs.kwargs["messages"][0]["content"]

        assert result["contract_name"] == "TestToken"

    @patch("backend.skills.solidity_generation.anthropic.Anthropic")
    async def test_execute_with_feedback(self, mock_anthropic_cls: MagicMock, skill: SolidityGenerationSkill):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(MOCK_LLM_RESPONSE))]
        mock_client.messages.create.return_value = mock_response

        await skill.execute(prompt="Create a token", feedback="Fix reentrancy")

        call_kwargs = mock_client.messages.create.call_args
        user_msg = call_kwargs.kwargs["messages"][0]["content"]
        assert "Fix reentrancy" in user_msg
