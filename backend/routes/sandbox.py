import json

from litestar import post
from pydantic import BaseModel
from web3 import Web3

from backend.config import settings


class CallRequest(BaseModel):
    contract_address: str
    abi: list
    function_name: str
    args: list = []
    is_read: bool = False
    value: int = 0


class CallResponse(BaseModel):
    status: str
    result: str = ""
    transaction_hash: str = ""
    error: str = ""


@post("/api/sandbox/call")
async def call_contract(data: CallRequest) -> CallResponse:
    w3 = Web3(Web3.HTTPProvider(settings.anvil_url))
    if not w3.is_connected():
        return CallResponse(status="error", error=f"Cannot connect to Anvil at {settings.anvil_url}")

    try:
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(data.contract_address),
            abi=data.abi,
        )

        func = getattr(contract.functions, data.function_name)

        if data.is_read:
            result = func(*data.args).call()
            return CallResponse(
                status="success",
                result=json.dumps(result, default=str),
            )
        else:
            account = w3.eth.accounts[0]
            tx_params = {
                "from": account,
                "nonce": w3.eth.get_transaction_count(account),
                "gas": 500_000,
                "gasPrice": w3.eth.gas_price,
            }
            if data.value > 0:
                tx_params["value"] = data.value

            tx = func(*data.args).build_transaction(tx_params)
            tx_hash = w3.eth.send_transaction(tx)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

            return CallResponse(
                status="success",
                result=json.dumps({
                    "transactionHash": tx_hash.hex(),
                    "blockNumber": receipt["blockNumber"],
                    "gasUsed": receipt["gasUsed"],
                    "status": receipt["status"],
                }, default=str),
                transaction_hash=tx_hash.hex(),
            )
    except Exception as e:
        return CallResponse(status="error", error=str(e))
