from agautoeval.agent.base import BaseAgent, AgentResult
from agautoeval.agent.opencode import OpenCodeAgent
from agautoeval.agent.claude import ClaudeCodeAgent
from agautoeval.agent.swe_agent import SWEAgentAgent
from agautoeval.agent.mock import MockAgent
from agautoeval.config import AgentConfig

_AGENT_REGISTRY: dict[str, type[BaseAgent]] = {
    "opencode": OpenCodeAgent,
    "claude": ClaudeCodeAgent,
    "swe_agent": SWEAgentAgent,
    "mock": MockAgent,
}

# Per-agent type keyword mapping: maps agent types to the subset of
# AgentConfig fields their constructor accepts.
_AGENT_CONFIG_FIELDS: dict[str, set[str]] = {
    "opencode": {"command", "env", "timeout", "install_cmd", "version_cmd", "model", "provider"},
    "claude": {"command", "env", "timeout", "install_cmd", "version_cmd", "model", "provider"},
    "swe_agent": {"command", "env", "timeout", "install_cmd", "version_cmd", "model", "provider"},
    "mock": {"command", "env", "timeout"},
}


def create_agent(config: AgentConfig) -> BaseAgent:
    if config.type not in _AGENT_REGISTRY:
        raise ValueError(
            f"Unknown agent type: {config.type}. "
            f"Available: {list(_AGENT_REGISTRY.keys())}"
        )
    cls = _AGENT_REGISTRY[config.type]
    fields = _AGENT_CONFIG_FIELDS.get(config.type, {"command", "env", "timeout"})
    kwargs = {f: getattr(config, f) for f in fields}
    return cls(**kwargs)
