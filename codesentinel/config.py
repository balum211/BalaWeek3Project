"""Runtime configuration for CodeSentinel.

Everything is read from environment variables (or a local .env file) so the
same code runs in Streamlit, the MCP server, the eval harness and the tests.

Provider order (first match wins):
    1. NEBIUS_API_KEY     -> Nebius Token Factory (OpenAI compatible)
    2. FIREWORKS_API_KEY  -> Fireworks AI (OpenAI compatible)
    3. OPENAI_API_KEY     -> OpenAI
    4. none               -> "static" mode: deterministic analyzers only

A second provider, when present, is wired in as an automatic fallback model.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env", override=False)

DATA_DIR = Path(os.getenv("CS_DATA_DIR", ROOT_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

PROVIDERS = {
    "nebius": {
        "key_env": "NEBIUS_API_KEY",
        "base_url": os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/"),
        "model": os.getenv("NEBIUS_MODEL", "meta-llama/Llama-3.3-70B-Instruct"),
    },
    "fireworks": {
        "key_env": "FIREWORKS_API_KEY",
        "base_url": os.getenv("FIREWORKS_BASE_URL", "https://api.fireworks.ai/inference/v1"),
        "model": os.getenv("FIREWORKS_MODEL", "accounts/fireworks/models/llama-v3p3-70b-instruct"),
    },
    "openai": {
        "key_env": "OPENAI_API_KEY",
        "base_url": os.getenv("OPENAI_BASE_URL") or None,
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    },
}


@dataclass
class Settings:
    provider: str | None = None
    fallback_provider: str | None = None
    temperature: float = float(os.getenv("CS_TEMPERATURE", "0.1"))
    request_timeout: int = int(os.getenv("CS_LLM_TIMEOUT", "60"))
    max_retries: int = int(os.getenv("CS_LLM_RETRIES", "2"))
    agent_step_limit: int = int(os.getenv("CS_AGENT_STEP_LIMIT", "12"))
    max_files: int = int(os.getenv("CS_MAX_FILES", "15"))
    max_file_bytes: int = int(os.getenv("CS_MAX_FILE_BYTES", "120000"))
    llm_cache_ttl: int = int(os.getenv("CS_LLM_CACHE_TTL", str(24 * 3600)))
    github_cache_ttl: int = int(os.getenv("CS_GITHUB_CACHE_TTL", "300"))
    github_token: str | None = os.getenv("GITHUB_TOKEN") or None
    mem0_api_key: str | None = os.getenv("MEM0_API_KEY") or None
    slow_agent_seconds: float = float(os.getenv("CS_SLOW_AGENT_SECONDS", "45"))
    extra: dict = field(default_factory=dict)

    @property
    def llm_enabled(self) -> bool:
        return self.provider is not None


def _available_providers() -> list[str]:
    forced = os.getenv("CS_PROVIDER", "").strip().lower()
    found = [name for name, p in PROVIDERS.items() if os.getenv(p["key_env"])]
    if forced == "static":
        return []
    if forced in found:
        found.remove(forced)
        found.insert(0, forced)
    return found


def get_settings() -> Settings:
    available = _available_providers()
    return Settings(
        provider=available[0] if available else None,
        fallback_provider=available[1] if len(available) > 1 else None,
    )


def provider_label(name: str | None) -> str:
    if not name:
        return "Static analysis only (no LLM key found)"
    return f"{name.title()} · {PROVIDERS[name]['model']}"
