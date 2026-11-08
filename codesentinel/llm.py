"""Model factory and robust structured output helpers.

Error handling strategy for every LLM call in the system:
  1. Client level retries with timeout (max_retries / request_timeout).
  2. Model fallback: primary provider, then the secondary provider if configured.
  3. Output repair: if the reply is not valid JSON for the schema, one repair
     call is made that shows the model its own output and the validation error.
  4. Graceful degradation: callers fall back to deterministic results when all
     of the above fail, and the run is marked "degraded" in the monitor.
"""

from __future__ import annotations

import json
import re
from typing import TypeVar

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

from codesentinel.config import PROVIDERS, Settings

T = TypeVar("T", bound=BaseModel)

_OVERRIDE: list[BaseChatModel] | None = None  # tests inject fake models here


def set_model_override(models: list[BaseChatModel] | None) -> None:
    global _OVERRIDE
    _OVERRIDE = models


def _make(provider: str, settings: Settings) -> BaseChatModel:
    import os

    from langchain_openai import ChatOpenAI

    p = PROVIDERS[provider]
    kwargs = dict(model=p["model"], api_key=os.getenv(p["key_env"]), temperature=settings.temperature,
                  timeout=settings.request_timeout, max_retries=settings.max_retries)
    if p["base_url"]:
        kwargs["base_url"] = p["base_url"]
    return ChatOpenAI(**kwargs)


def get_models(settings: Settings) -> list[BaseChatModel]:
    """Primary model first, then fallbacks. Empty list means static mode."""
    if _OVERRIDE is not None:
        return list(_OVERRIDE)
    models = []
    for name in (settings.provider, settings.fallback_provider):
        if name:
            models.append(_make(name, settings))
    return models


def model_name(model: BaseChatModel) -> str:
    return getattr(model, "model_name", None) or getattr(model, "model", None) or type(model).__name__


def extract_json(text: str) -> dict:
    """Pull the first JSON object out of a reply that may include prose or code fences."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if fence:
        text = fence.group(1)
    start = text.find("{")
    if start < 0:
        raise ValueError("No JSON object found in the model reply.")
    depth, in_str, esc = 0, False, False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise ValueError("The JSON object in the model reply is not closed.")


def message_text(msg) -> str:
    content = getattr(msg, "content", msg)
    if isinstance(content, list):
        return "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)
    return str(content)


def parse_or_repair(model: BaseChatModel, text: str, schema: type[T]) -> T:
    try:
        return schema.model_validate(extract_json(text))
    except (ValueError, ValidationError, json.JSONDecodeError) as exc:
        repair = model.invoke([
            SystemMessage(content="You fix malformed JSON. Reply with one JSON object only, no prose."),
            HumanMessage(content=f"Schema:\n{json.dumps(schema.model_json_schema())[:4000]}\n\n"
                                 f"Validation error:\n{str(exc)[:800]}\n\nOriginal reply:\n{text[:6000]}"),
        ])
        return schema.model_validate(extract_json(message_text(repair)))


def structured_call(models: list[BaseChatModel], system: str, user: str, schema: type[T]) -> tuple[T, str]:
    """Single shot structured call with model fallback. Returns (result, model_name)."""
    errors = []
    for model in models:
        try:
            reply = model.invoke([SystemMessage(content=system), HumanMessage(content=user)])
            return parse_or_repair(model, message_text(reply), schema), model_name(model)
        except Exception as exc:  # noqa: BLE001  try the next provider
            errors.append(f"{model_name(model)}: {type(exc).__name__}: {str(exc)[:200]}")
    raise RuntimeError("All models failed. " + " | ".join(errors))
