"""Agent definition storage in ~/.agautoeval/agents.json.

Each agent has:
  - type: unique key used in YAML config agent.type
  - label: display name
  - description: one-line summary
  - capabilities: list of tag strings (tool-use, shell, sandboxed, etc.)
  - defaults: dict of AgentConfig overrides (command, install_cmd, env, etc.)
"""

import json
import os
from pathlib import Path

AGENTS_PATH = Path("~/.agautoeval/agents.json").expanduser().resolve()

PREBUILT_AGENTS = [
    {
        "type": "opencode",
        "label": "OpenCode",
        "description": "Tool-use agent with shell access",
        "capabilities": ["tool-use", "shell", "sandboxed"],
        "defaults": {
            "command": "opencode run --dangerously-skip-permissions -m {provider}/{model} {problem_statement}",
            "install_cmd": "npm install -g opencode-ai",
            "version_cmd": "opencode --version",
            "env": {},
            "timeout": 1800,
            "persist": [],
            "model": "",
            "provider": "",
        },
    },
    {
        "type": "claude",
        "label": "Claude Agent",
        "description": "Native AI agent with tool calling",
        "capabilities": ["tool-use", "native-agent"],
        "defaults": {
            "command": "claude --dangerously-skip-permissions -p {problem_statement} --output-format stream-json",
            "install_cmd": "npm install -g @anthropic-ai/claude-code",
            "version_cmd": "claude --version",
            "env": {},
            "timeout": 1800,
            "persist": [],
            "model": "",
            "provider": "",
        },
    },
    {
        "type": "swe_agent",
        "label": "SWE Agent",
        "description": "Research-grade software engineering agent",
        "capabilities": ["tool-use", "shell", "multi-agent"],
        "defaults": {
            "command": "mini -m {provider}/{model} -t {problem_statement} -y",
            "install_cmd": "pip install mini-swe-agent",
            "version_cmd": "pip show mini-swe-agent | grep Version",
            "env": {},
            "timeout": 1800,
            "persist": [],
            "model": "",
            "provider": "",
        },
    },
]


def ensure_agents_file() -> Path:
    """Create agents.json with prebuilt defaults if it doesn't exist."""
    agents_dir = AGENTS_PATH.parent
    agents_dir.mkdir(parents=True, exist_ok=True)

    if not AGENTS_PATH.exists():
        _write_agents(PREBUILT_AGENTS)
    return AGENTS_PATH


def _read_agents() -> list[dict]:
    """Read all agent definitions from agents.json."""
    ensure_agents_file()
    try:
        with open(AGENTS_PATH) as f:
            data = json.load(f)
        agents = data.get("agents", [])
        if not isinstance(agents, list):
            return []
        return agents
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _write_agents(agents: list[dict]) -> None:
    """Atomically write agent definitions to agents.json."""
    agents_dir = AGENTS_PATH.parent
    agents_dir.mkdir(parents=True, exist_ok=True)

    tmp = AGENTS_PATH.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump({"agents": agents}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, AGENTS_PATH)


def get_agent(agent_type: str) -> dict | None:
    """Look up a single agent by type. Returns None if not found."""
    agents = _read_agents()
    for a in agents:
        if a.get("type") == agent_type:
            return a
    return None


def get_agent_defaults(agent_type: str) -> dict:
    """Return the defaults dict for an agent, or empty dict if not found."""
    agent = get_agent(agent_type)
    if agent is None:
        return {}
    return agent.get("defaults", {})


def list_agents() -> list[dict]:
    """Return all agent definitions."""
    return _read_agents()


def upsert_agent(agent_def: dict) -> dict:
    """Insert or update an agent definition by type. Returns the stored record."""
    agent_type = agent_def.get("type")
    if not agent_type:
        raise ValueError("Agent definition must have a 'type' field")

    agents = _read_agents()
    for i, a in enumerate(agents):
        if a.get("type") == agent_type:
            agents[i] = agent_def
            _write_agents(agents)
            return agent_def

    agents.append(agent_def)
    _write_agents(agents)
    return agent_def


def delete_agent(agent_type: str) -> bool:
    """Remove an agent by type. Returns True if deleted, False if not found."""
    agents = _read_agents()
    for i, a in enumerate(agents):
        if a.get("type") == agent_type:
            agents.pop(i)
            _write_agents(agents)
            return True
    return False
