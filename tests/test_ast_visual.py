import pytest

from backend.skills.ast_visual import AstVisualSkill
from tests.conftest import SAMPLE_ERC20, SAMPLE_MINIMAL


@pytest.fixture
def skill():
    return AstVisualSkill()


class TestAstVisual:
    async def test_returns_nodes_and_edges(self, skill: AstVisualSkill):
        result = await skill.execute(solidity_code=SAMPLE_MINIMAL, contract_name="SimpleStorage")

        assert "nodes" in result
        assert "edges" in result
        assert isinstance(result["nodes"], list)
        assert isinstance(result["edges"], list)

    async def test_contract_node_exists(self, skill: AstVisualSkill):
        result = await skill.execute(solidity_code=SAMPLE_MINIMAL, contract_name="SimpleStorage")
        contract_nodes = [n for n in result["nodes"] if n["type"] == "contractNode"]

        assert len(contract_nodes) >= 1
        assert contract_nodes[0]["data"]["label"] == "SimpleStorage"

    async def test_detects_functions(self, skill: AstVisualSkill):
        result = await skill.execute(solidity_code=SAMPLE_MINIMAL, contract_name="SimpleStorage")
        func_nodes = [n for n in result["nodes"] if n["type"] == "functionNode"]
        func_names = [n["data"]["label"] for n in func_nodes]

        assert "set" in func_names
        assert "get" in func_names

    async def test_detects_state_variables(self, skill: AstVisualSkill):
        result = await skill.execute(solidity_code=SAMPLE_MINIMAL, contract_name="SimpleStorage")
        var_nodes = [n for n in result["nodes"] if n["type"] == "stateVarNode"]

        assert len(var_nodes) >= 1
        var_names = [n["data"]["label"] for n in var_nodes]
        assert "_value" in var_names

    async def test_detects_inheritance(self, skill: AstVisualSkill):
        result = await skill.execute(solidity_code=SAMPLE_ERC20, contract_name="MyToken")
        inherited_nodes = [n for n in result["nodes"] if n["type"] == "contractNode" and n["data"].get("type") == "inherited"]

        assert len(inherited_nodes) >= 2
        labels = [n["data"]["label"] for n in inherited_nodes]
        assert "ERC20" in labels
        assert "Ownable" in labels

    async def test_inheritance_edges_animated(self, skill: AstVisualSkill):
        result = await skill.execute(solidity_code=SAMPLE_ERC20, contract_name="MyToken")
        inherit_edges = [e for e in result["edges"] if e.get("label") == "inherits"]

        assert len(inherit_edges) >= 2
        for edge in inherit_edges:
            assert edge["animated"] is True

    async def test_function_visibility_classification(self, skill: AstVisualSkill):
        result = await skill.execute(solidity_code=SAMPLE_MINIMAL, contract_name="SimpleStorage")
        func_nodes = [n for n in result["nodes"] if n["type"] == "functionNode"]

        get_node = next(n for n in func_nodes if n["data"]["label"] == "get")
        assert get_node["data"]["node_type"] == "functionRead"

        set_node = next(n for n in func_nodes if n["data"]["label"] == "set")
        assert set_node["data"]["node_type"] == "functionWrite"

    async def test_edges_connect_to_contract(self, skill: AstVisualSkill):
        result = await skill.execute(solidity_code=SAMPLE_MINIMAL, contract_name="SimpleStorage")

        for edge in result["edges"]:
            source_is_contract = "contract-" in edge["source"]
            target_is_contract = "contract-" in edge["target"]
            # Every edge should connect to the contract (directly or via modifier)
            assert source_is_contract or target_is_contract

    async def test_empty_code(self, skill: AstVisualSkill):
        result = await skill.execute(solidity_code="", contract_name="Empty")

        # Should still have at least the contract node
        assert len(result["nodes"]) >= 1
        assert result["nodes"][0]["data"]["label"] == "Empty"

    async def test_erc20_has_many_functions(self, skill: AstVisualSkill):
        result = await skill.execute(solidity_code=SAMPLE_ERC20, contract_name="MyToken")
        func_nodes = [n for n in result["nodes"] if n["type"] == "functionNode"]

        func_names = [n["data"]["label"] for n in func_nodes]
        assert "mint" in func_names
        assert "burn" in func_names
        assert "addToBlacklist" in func_names
