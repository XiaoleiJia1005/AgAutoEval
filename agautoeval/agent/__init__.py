from agautoeval.agent.base import BaseAgent, AgentResult
from agautoeval.agent.opencode import OpenCodeAgent
from agautoeval.agent.mock import MockAgent

_AGENT_REGISTRY: dict[str, type[BaseAgent]] = {
    "opencode": OpenCodeAgent,
    "mock": MockAgent,
}


def create_agent(agent_type: str, **kwargs) -> BaseAgent:
    if agent_type not in _AGENT_REGISTRY:
        raise ValueError(
            f"Unknown agent type: {agent_type}. "
            f"Available: {list(_AGENT_REGISTRY.keys())}"
        )
    return _AGENT_REGISTRY[agent_type](**kwargs)
