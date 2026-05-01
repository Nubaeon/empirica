"""Env-var name collector — names ONLY, never values.

The values of process environment variables are explicitly off-limits per
the proposal. This collector lists names that match conventional AI/secret
patterns so the scanner can flag *which credentials are reachable*, not
*what they are*.
"""

from __future__ import annotations

# Conservative pattern set — favors recall over precision so "interesting"
# env var names show up. Substring match (case-insensitive). The judgment
# layer (Phase 2) will refine.
_INTERESTING_FRAGMENTS: tuple[str, ...] = (
    'API_KEY', 'API-KEY', 'APIKEY',
    'TOKEN', 'SECRET', 'PASSWORD', 'PASSWD',
    'OPENAI', 'ANTHROPIC', 'GEMINI', 'GOOGLE_API',
    'CLAUDE', 'COHERE', 'MISTRAL', 'OLLAMA',
    'HUGGINGFACE', 'HF_', 'REPLICATE',
    'PINECONE', 'WEAVIATE', 'QDRANT',
    'AWS_', 'AZURE_', 'GCP_',
    'GITHUB_TOKEN', 'GH_TOKEN',
    'SLACK_TOKEN', 'NTFY_',
    'AI_',
)


def _is_interesting(name: str) -> bool:
    upper = name.upper()
    return any(fragment in upper for fragment in _INTERESTING_FRAGMENTS)


def collect_env_var_names(read_surface, env: dict[str, str] | None = None) -> dict[str, list[str]]:
    """Return ``{'var_names_only': [...]}`` when the read-surface permits.

    Note the awkward singleton key: it's the only legal emission for
    ``process_env`` and explicitly signals "no values were read."
    """
    if 'var_names_only' not in read_surface.process_env:
        return {'var_names_only': []}

    import os as _os
    source = env if env is not None else dict(_os.environ)
    names = sorted(name for name in source.keys() if _is_interesting(name))
    return {'var_names_only': names}
