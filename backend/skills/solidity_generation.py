import asyncio
import json
import re
import time

import anthropic

from backend.config import settings

from .base import BaseSkill

MAX_RETRIES = 8
BASE_DELAY = 5

SYSTEM_PROMPT = """You are an expert Solidity smart contract developer. Given a natural language description, generate a complete, production-quality Solidity smart contract.

You MUST respond with valid JSON (no markdown fences) in this exact format:
{
  "contract_name": "ContractName",
  "solidity_code": "// SPDX-License-Identifier: MIT\\npragma solidity ^0.8.20;\\n\\ncontract ContractName { ... }",
  "constructor_args": ["arg1_description", "arg2_description"],
  "description": "Brief description of what the contract does"
}

Rules:
- Use Solidity ^0.8.20 with appropriate imports from OpenZeppelin if needed
- Include NatSpec comments for public functions
- Include proper access control (Ownable or custom)
- Include events for state changes
- The solidity_code must be a single string with \\n for newlines
- constructor_args should describe each parameter (name, type, purpose)
- Do NOT include markdown code fences in the response"""


class SolidityGenerationSkill(BaseSkill):
    name = "solidity_generation"
    description = "Generate Solidity smart contracts from natural language descriptions"

    async def execute(self, *, prompt: str, feedback: str | None = None) -> dict:
        user_message = f"Generate a Solidity smart contract for: {prompt}"
        if feedback:
            user_message += f"\n\nPlease fix the following issues found in the previous version:\n{feedback}"

        client = anthropic.Anthropic(
            api_key=settings.anthropic_api_key,
            base_url=settings.anthropic_base_url,
            default_headers={"api-key": settings.anthropic_api_key},
        )

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = client.messages.create(
                    model=settings.anthropic_model,
                    max_tokens=4096,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_message}],
                )
                raw_text = response.content[0].text
                return self._parse_response(raw_text)
            except (anthropic.RateLimitError, anthropic.APIStatusError) as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = BASE_DELAY * (2 ** attempt)
                    await asyncio.sleep(delay)
            except anthropic.APIError as e:
                # Check if it's a rate-limit-like error from MiMo
                if "429" in str(e) or "rate limit" in str(e).lower():
                    last_error = e
                    if attempt < MAX_RETRIES - 1:
                        delay = BASE_DELAY * (2 ** attempt)
                        await asyncio.sleep(delay)
                else:
                    raise

        raise last_error

    def _parse_response(self, raw: str) -> dict:
        """Parse LLM response, handling potential formatting issues."""
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

        # Try direct parse first
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Try extracting JSON block
            json_match = re.search(r"\{.*\}", raw, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                except json.JSONDecodeError:
                    # Fix unescaped newlines/tabs inside JSON string values
                    fixed = self._fix_json_strings(json_match.group())
                    try:
                        data = json.loads(fixed)
                    except json.JSONDecodeError:
                        # Last resort: extract fields manually via regex
                        data = self._extract_fields_manually(raw)
            else:
                data = self._extract_fields_manually(raw)

        code = data.get("solidity_code", "")
        code = code.replace("\\n", "\n").replace("\\t", "\t")
        data["solidity_code"] = code

        return {
            "contract_name": data.get("contract_name", "Unknown"),
            "solidity_code": data["solidity_code"],
            "constructor_args": data.get("constructor_args", []),
            "description": data.get("description", ""),
        }

    def _fix_json_strings(self, raw: str) -> str:
        """Fix unescaped newlines/tabs inside JSON string values.

        Scans character-by-character, tracking whether we're inside a JSON string
        (respecting backslash escapes). Replaces literal newlines/tabs inside
        strings with their escaped equivalents so json.loads can parse them.
        """
        result = []
        in_string = False
        i = 0
        while i < len(raw):
            c = raw[i]

            if in_string:
                if c == "\\":
                    # Escaped char — copy both backslash and next char verbatim
                    result.append(c)
                    if i + 1 < len(raw):
                        result.append(raw[i + 1])
                        i += 2
                    else:
                        i += 1
                elif c == '"':
                    # End of string
                    in_string = False
                    result.append(c)
                    i += 1
                elif c == "\n":
                    result.append("\\n")
                    i += 1
                elif c == "\r":
                    result.append("\\r")
                    i += 1
                elif c == "\t":
                    result.append("\\t")
                    i += 1
                else:
                    result.append(c)
                    i += 1
            else:
                if c == '"':
                    in_string = True
                result.append(c)
                i += 1

        return "".join(result)

    def _extract_fields_manually(self, raw: str) -> dict:
        """Extract fields from malformed JSON using direct string scanning.

        Handles literal newlines inside solidity_code by scanning for the
        boundary between the end of solidity_code and the start of
        constructor_args (or end of object).
        """
        name = self._extract_simple_string(raw, "contract_name")
        desc = self._extract_simple_string(raw, "description")
        code = self._extract_code_field(raw)
        args = self._extract_array(raw, "constructor_args")

        return {
            "contract_name": name or "Unknown",
            "solidity_code": code,
            "constructor_args": args,
            "description": desc or "",
        }

    def _extract_simple_string(self, raw: str, field: str) -> str | None:
        """Extract a simple single-line string field value."""
        m = re.search(rf'"{field}"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
        return m.group(1) if m else None

    def _extract_code_field(self, raw: str) -> str:
        """Extract solidity_code which may contain literal newlines.

        Strategy: find the opening quote of solidity_code's value, then scan
        forward character-by-character (handling escapes) until we hit the
        closing quote. Since the code may have literal newlines that break
        regex, we fall back to finding the boundary with constructor_args.
        """
        # Find the start of the solidity_code value
        key_match = re.search(r'"solidity_code"\s*:\s*"', raw)
        if not key_match:
            return ""

        start = key_match.end()
        i = start
        result = []
        while i < len(raw):
            c = raw[i]
            if c == "\\":
                result.append(c)
                if i + 1 < len(raw):
                    result.append(raw[i + 1])
                    i += 2
                else:
                    i += 1
            elif c == '"':
                # Potential end quote. Check if this looks like the real end
                # by seeing if ",\n follows with a known field name or }
                rest = raw[i + 1:i + 30].lstrip()
                if rest.startswith(",") or rest.startswith("}") or rest.startswith("\n") or rest.startswith("\r"):
                    # Likely the real end — check if next content is a field
                    field_check = re.match(r',\s*"(?:constructor_args|description|contract_name)"', rest)
                    if field_check or rest.startswith("}"):
                        break
                # Not the real end — it's an escaped or embedded quote
                result.append(c)
                i += 1
            else:
                result.append(c)
                i += 1

        code = "".join(result)
        # Unescape JSON string escapes
        code = code.replace('\\"', '"').replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")
        return code

    def _extract_array(self, raw: str, field: str) -> list:
        """Extract a JSON array field value."""
        m = re.search(rf'"{field}"\s*:\s*(\[.*?\])', raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
        return []
