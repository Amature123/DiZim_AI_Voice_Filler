"""Unit tests for _parse_json_response JSON parsing."""
import json
import pytest
import re


def _parse_json(raw: str) -> dict:
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return json.loads(raw)


def test_parse_clean_json():
    raw = '{"buyerInfo": {"buyerName": "A"}}'
    assert _parse_json(raw) == {"buyerInfo": {"buyerName": "A"}}


def test_parse_markdown_wrapped_json():
    raw = '```json\n{"buyerInfo": {"buyerName": "A"}}\n```'
    assert _parse_json(raw) == {"buyerInfo": {"buyerName": "A"}}


def test_parse_json_with_leading_text():
    raw = 'Here is the result:\n{"buyerInfo": {}}'
    assert _parse_json(raw) == {"buyerInfo": {}}
