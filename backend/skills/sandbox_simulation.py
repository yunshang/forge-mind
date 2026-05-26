import json
import subprocess
import tempfile
from pathlib import Path

from web3 import Web3

from backend.config import settings
from backend.utils.solc_detector import SolcDetector

from .base import BaseSkill


class SandboxSimulationSkill(BaseSkill):
    name = "sandbox_simulation"
    description = "Compile and deploy Solidity contracts to local Anvil sandbox"

    async def execute(
        self,
        *,
        solidity_code: str,
        contract_name: str,
        constructor_args: list | None = None,
    ) -> dict:
        constructor_args = constructor_args or []

        # Step 1: Compile
        compile_result = self._compile(solidity_code, contract_name)
        if "error" in compile_result:
            return {"status": "error", "error": compile_result["error"]}

        abi = compile_result["abi"]
        bytecode = compile_result["bytecode"]

        # Step 2: Deploy to Anvil
        w3 = Web3(Web3.HTTPProvider(settings.anvil_url))
        if not w3.is_connected():
            return {"status": "error", "error": f"Cannot connect to Anvil at {settings.anvil_url}"}

        deploy_result = self._deploy(w3, abi, bytecode, constructor_args)
        if "error" in deploy_result:
            return deploy_result

        # Step 3: Extract callable functions
        functions = self._extract_functions(abi)

        return {
            "status": "success",
            "contract_address": deploy_result["address"],
            "transaction_hash": deploy_result["tx_hash"],
            "abi": abi,
            "functions": functions,
            "chain_id": settings.anvil_chain_id,
        }

    def _compile(self, solidity_code: str, contract_name: str) -> dict:
        """Compile Solidity code using solc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / f"{contract_name}.sol"
            contract_path.write_text(solidity_code)

            solc_path = SolcDetector.find_solc()
            if not solc_path:
                return {"error": SolcDetector.get_install_instructions()}

            try:
                result = subprocess.run(
                    [
                        solc_path,
                        "--combined-json",
                        "abi,bin",
                        "--optimize",
                        str(contract_path),
                        "-o",
                        str(tmpdir),
                        "--overwrite",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            except subprocess.TimeoutExpired:
                return {"error": "Compilation timed out (30s)"}

            if result.returncode != 0:
                return {"error": f"Compilation failed:\n{result.stderr}"}

            # Parse combined-json output from stdout
            try:
                combined = json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"error": "Failed to parse solc output"}

            # Find the contract in output
            contract_key = None
            for key in combined.get("contracts", {}):
                if contract_name in key:
                    contract_key = key
                    break

            if not contract_key:
                available = list(combined.get("contracts", {}).keys())
                return {"error": f"Contract '{contract_name}' not found. Available: {available}"}

            contract_data = combined["contracts"][contract_key]
            raw_abi = contract_data["abi"]
            parsed_abi = json.loads(raw_abi) if isinstance(raw_abi, str) else raw_abi
            return {
                "abi": parsed_abi,
                "bytecode": contract_data["bin"],
            }

    def _deploy(self, w3: Web3, abi: list, bytecode: str, constructor_args: list) -> dict:
        """Deploy contract to Anvil using first pre-funded account."""
        account = w3.eth.accounts[0]
        contract = w3.eth.contract(abi=abi, bytecode=bytecode)

        try:
            if constructor_args:
                tx = contract.constructor(*constructor_args).build_transaction({
                    "from": account,
                    "nonce": w3.eth.get_transaction_count(account),
                    "gas": 3_000_000,
                    "gasPrice": w3.eth.gas_price,
                })
            else:
                tx = contract.constructor().build_transaction({
                    "from": account,
                    "nonce": w3.eth.get_transaction_count(account),
                    "gas": 3_000_000,
                    "gasPrice": w3.eth.gas_price,
                })

            tx_hash = w3.eth.send_transaction(tx)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

            return {
                "address": receipt["contractAddress"],
                "tx_hash": tx_hash.hex(),
            }
        except Exception as e:
            return {"error": f"Deployment failed: {e!s}"}

    def _extract_functions(self, abi: list) -> list[dict]:
        """Extract callable functions from ABI."""
        functions = []
        for item in abi:
            if item.get("type") == "function":
                func = {
                    "name": item["name"],
                    "inputs": [
                        {"name": inp.get("name", ""), "type": inp["type"]}
                        for inp in item.get("inputs", [])
                    ],
                    "outputs": [
                        {"name": out.get("name", ""), "type": out["type"]}
                        for out in item.get("outputs", [])
                    ],
                    "stateMutability": item.get("stateMutability", "nonpayable"),
                    "isRead": item.get("stateMutability") in ("view", "pure"),
                }
                functions.append(func)
        return functions
