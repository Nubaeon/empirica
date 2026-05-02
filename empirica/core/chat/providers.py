"""Multi-provider registry for empirica chat.

A Provider is a named OpenAI-compatible endpoint with optional default
model + auth. Chat keeps a registry of these so the user can switch
between them at runtime via /provider NAME (e.g. fast llama.cpp vs
smart Ollama-served qwopus).

Wire format per provider:
  - "chat_completions" (default): direct OpenAI-compat /v1/chat/completions
    Used for Ollama, LMStudio, vLLM, llama.cpp, Groq, OpenAI etc.
  - "responses": route through ecodex translator at base_url, which
    converts to chat-completions downstream. Used when the provider is
    the translator (for full-stack integration testing) or a future
    Responses-API-native endpoint.

CLI parsing: --provider NAME=URL[,model=M][,wire=W][,key_env=ENV]
  --provider ollama=http://192.168.1.68:11434/v1,model=qwen3.5:latest
  --provider llcpp=http://192.168.1.68:8080/v1,model=Qwen3-30B-A3B-Q4_K_M.gguf
  --provider deepseek=https://api.deepseek.com/v1,model=deepseek-chat,key_env=DEEPSEEK_API_KEY
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Provider:
    """One named OpenAI-compatible endpoint."""

    name: str
    base_url: str
    default_model: str | None = None
    wire: str = "chat_completions"  # "chat_completions" | "responses"
    api_key_env: str | None = None

    def display(self) -> str:
        suffix = f" · {self.default_model}" if self.default_model else ""
        return f"{self.name}  ({self.base_url}{suffix})"


@dataclass
class ProviderRegistry:
    """Registry of providers + tracking of active selection."""

    providers: dict[str, Provider] = field(default_factory=dict)
    active_provider_name: str | None = None
    active_model: str | None = None

    def add(self, provider: Provider) -> None:
        self.providers[provider.name] = provider
        if self.active_provider_name is None:
            self.active_provider_name = provider.name
            self.active_model = provider.default_model

    def names(self) -> list[str]:
        return list(self.providers.keys())

    def get(self, name: str) -> Provider | None:
        return self.providers.get(name)

    def active(self) -> Provider | None:
        if self.active_provider_name is None:
            return None
        return self.providers.get(self.active_provider_name)

    def set_active_provider(self, name: str) -> Provider | None:
        """Switch active provider; returns the new active provider or None."""
        p = self.providers.get(name)
        if p is None:
            return None
        self.active_provider_name = name
        # Reset model to provider default; user can /model NAME to switch
        self.active_model = p.default_model
        return p

    def set_active_model(self, model: str) -> bool:
        if self.active_provider_name is None:
            return False
        self.active_model = model
        return True

    def display_status(self) -> str:
        a = self.active()
        if a is None:
            return "no active provider"
        model = self.active_model or "(no default model)"
        return f"{a.name} · {model}"


def parse_provider_spec(spec: str) -> Provider:
    """Parse `NAME=URL[,key=val][,key=val]…` into a Provider."""
    if "=" not in spec:
        raise ValueError(
            f"--provider value must be NAME=URL[,…], got: {spec!r}"
        )
    name, _, rest = spec.partition("=")
    name = name.strip()
    if not name:
        raise ValueError(f"--provider missing NAME: {spec!r}")

    # Split URL from optional kv tail
    parts = rest.split(",")
    base_url = parts[0].strip()
    if not base_url:
        raise ValueError(f"--provider missing URL: {spec!r}")

    extras: dict[str, str] = {}
    for kv in parts[1:]:
        kv = kv.strip()
        if not kv:
            continue
        if "=" not in kv:
            raise ValueError(f"--provider extras must be key=val, got: {kv!r}")
        k, _, v = kv.partition("=")
        extras[k.strip()] = v.strip()

    return Provider(
        name=name,
        base_url=base_url,
        default_model=extras.get("model"),
        wire=extras.get("wire", "chat_completions"),
        api_key_env=extras.get("key_env"),
    )


def builtin_empirica_server_providers() -> list[Provider]:
    """Sensible defaults pre-loaded when no --provider flags are given.

    Targets the verified empirica-server LAN endpoint (T39 finding).
    Users can override entirely with --provider flags.
    """
    return [
        Provider(
            name="ollama",
            base_url="http://192.168.1.68:11434/v1",
            default_model="qwen3.5:latest",
        ),
        Provider(
            name="qwopus",
            base_url="http://192.168.1.68:11434/v1",
            default_model="qwopus:27b-q4",
        ),
        Provider(
            name="llcpp",
            base_url="http://192.168.1.68:8080/v1",
            default_model="Qwen3-30B-A3B-Q4_K_M.gguf",
        ),
        Provider(
            name="llcpp-alt",
            base_url="http://192.168.1.68:8081/v1",
            default_model="Qwen3-30B-A3B-Q4_K_M.gguf",
        ),
    ]
