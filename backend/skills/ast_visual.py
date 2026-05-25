import re

from .base import BaseSkill

FUNC_PATTERN = re.compile(
    r"function\s+(\w+)\s*\(([^)]*)\)\s*"
    r"(external|public|internal|private)?\s*"
    r"(view|pure|payable)?\s*"
    r"(?:returns\s*\(([^)]*)\))?"
)
STATE_VAR_PATTERN = re.compile(
    r"(uint\d*|int\d*|bool|address|string|bytes\d*|mapping\([^)]+\))\s+"
    r"(public|private|internal)?\s*(\w+)\s*;"
)
INHERITANCE_PATTERN = re.compile(r"contract\s+\w+\s+is\s+([^{]+)")
CONTRACT_NAME_PATTERN = re.compile(r"contract\s+(\w+)")
MODIFIER_PATTERN = re.compile(r"modifier\s+(\w+)")
EVENT_PATTERN = re.compile(r"event\s+(\w+)")


class AstVisualSkill(BaseSkill):
    name = "ast_visual"
    description = "Parse Solidity code into React Flow graph structure"

    async def execute(self, *, solidity_code: str, contract_name: str = "") -> dict:
        nodes: list[dict] = []
        edges: list[dict] = []

        main_contract = CONTRACT_NAME_PATTERN.search(solidity_code)
        contract_id = main_contract.group(1) if main_contract else contract_name or "Contract"

        # Contract node as center
        nodes.append({
            "id": f"contract-{contract_id}",
            "type": "contractNode",
            "position": {"x": 400, "y": 200},
            "data": {
                "label": contract_id,
                "type": "contract",
            },
        })

        # Inheritance edges
        inheritance = INHERITANCE_PATTERN.search(solidity_code)
        if inheritance:
            parents = [p.strip() for p in inheritance.group(1).split(",")]
            for i, parent in enumerate(parents):
                parent_id = f"contract-{parent}"
                nodes.append({
                    "id": parent_id,
                    "type": "contractNode",
                    "position": {"x": 400, "y": 50 + i * 80},
                    "data": {"label": parent, "type": "inherited"},
                })
                edges.append({
                    "id": f"edge-{contract_id}-{parent}",
                    "source": f"contract-{contract_id}",
                    "target": parent_id,
                    "type": "smoothstep",
                    "label": "inherits",
                    "animated": True,
                })

        # Function nodes
        functions = list(FUNC_PATTERN.finditer(solidity_code))
        for i, func_match in enumerate(functions):
            func_name = func_match.group(1)
            visibility = func_match.group(3) or "internal"
            mutability = func_match.group(4) or ""
            params_raw = func_match.group(2)
            returns_raw = func_match.group(5)

            func_id = f"func-{func_name}-{i}"

            # Determine node color by visibility
            node_type = "functionRead" if visibility in ("view", "pure") or mutability in ("view", "pure") else "functionWrite"

            params = self._parse_params(params_raw)
            returns = self._parse_params(returns_raw) if returns_raw else []

            nodes.append({
                "id": func_id,
                "type": "functionNode",
                "position": {"x": 100 + (i % 3) * 250, "y": 400 + (i // 3) * 120},
                "data": {
                    "label": func_name,
                    "visibility": visibility,
                    "mutability": mutability,
                    "params": params,
                    "returns": returns,
                    "node_type": node_type,
                },
            })

            edges.append({
                "id": f"edge-{contract_id}-{func_id}",
                "source": f"contract-{contract_id}",
                "target": func_id,
                "type": "smoothstep",
                "label": visibility,
            })

        # State variable nodes
        state_vars = list(STATE_VAR_PATTERN.finditer(solidity_code))
        for i, var_match in enumerate(state_vars):
            var_type = var_match.group(1)
            var_visibility = var_match.group(2) or "internal"
            var_name = var_match.group(3)
            var_id = f"var-{var_name}"

            nodes.append({
                "id": var_id,
                "type": "stateVarNode",
                "position": {"x": 700, "y": 400 + i * 80},
                "data": {
                    "label": var_name,
                    "var_type": var_type,
                    "visibility": var_visibility,
                },
            })

            edges.append({
                "id": f"edge-{contract_id}-{var_id}",
                "source": f"contract-{contract_id}",
                "target": var_id,
                "type": "smoothstep",
                "label": "state",
                "style": {"strokeDasharray": "5,5"},
            })

        # Modifier nodes
        modifiers = list(MODIFIER_PATTERN.finditer(solidity_code))
        for i, mod_match in enumerate(modifiers):
            mod_name = mod_match.group(1)
            mod_id = f"mod-{mod_name}"

            nodes.append({
                "id": mod_id,
                "type": "modifierNode",
                "position": {"x": 100, "y": 200 + i * 80},
                "data": {"label": mod_name},
            })

            # Connect modifier to functions that use it
            for func_match in functions:
                func_line_start = func_match.start()
                func_line_end = min(func_match.end() + 200, len(solidity_code))
                func_context = solidity_code[func_line_start:func_line_end]
                if mod_name in func_context:
                    func_id = f"func-{func_match.group(1)}-{functions.index(func_match)}"
                    edges.append({
                        "id": f"edge-{mod_id}-{func_id}",
                        "source": mod_id,
                        "target": func_id,
                        "type": "smoothstep",
                        "label": "modifies",
                        "style": {"stroke": "#f59e0b"},
                    })

        return {"nodes": nodes, "edges": edges}

    def _parse_params(self, raw: str) -> list[dict]:
        if not raw or not raw.strip():
            return []
        params = []
        for param in raw.split(","):
            param = param.strip()
            if not param:
                continue
            parts = param.split()
            if len(parts) >= 2:
                params.append({"type": parts[0], "name": parts[1]})
            elif len(parts) == 1:
                params.append({"type": parts[0], "name": ""})
        return params
