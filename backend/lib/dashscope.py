import os
import re
import json
from openai import OpenAI

BASE_URL = os.getenv(
    "DASHSCOPE_BASE_URL",
    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)
API_KEY = os.getenv("DASHSCOPE_API_KEY", "")


def _get_client() -> OpenAI:
    return OpenAI(api_key=API_KEY, base_url=BASE_URL)


def extract_fields(text: str, system_prompt: str) -> dict:
    """Call Qwen-Max via DashScope International to extract invoice fields."""
    if not API_KEY:
        raise ValueError("DASHSCOPE_API_KEY not set")

    client = _get_client()
    completion = client.chat.completions.create(
        model="qwen-max",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Thông tin khách hàng đọc: '{text}'"},
        ],
        temperature=0.1,
    )
    raw = completion.choices[0].message.content.strip()
    return _parse_json_response(raw)


def _parse_json_response(raw: str) -> dict:
    """Extract JSON from LLM response, tolerant of markdown wrappers."""
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return json.loads(raw)
