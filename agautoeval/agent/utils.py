"""Shared runtime utilities for agent implementations.

These functions operate on a DockerSandbox instance so agent code does not
need to duplicate common setup logic (e.g., nvm/npm installation).
"""

from typing import Any


def ensure_npm(sandbox: Any, min_version: str = "18") -> None:
    """Ensure npm (via nvm-managed Node.js) is available inside the container.

    Checks for npm; if missing, installs nvm then uses it to install
    Node.js >= *min_version*. The node/npm binaries are symlinked to
    /usr/local/bin so subsequent exec() calls find them on PATH.
    """
    _log = getattr(sandbox, "_log", print)
    name = getattr(sandbox, "_container_name", "container")

    # Check if npm already exists
    _, _, rc = sandbox.exec(["which", "npm"], cwd="/", timeout=30)
    if rc == 0:
        return

    _log(f"[{name}] npm not found, installing nvm + Node.js {min_version}...")

    NVM_DIR = "/root/.nvm"
    NVM_INSTALL_SCRIPT = "https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh"

    # Install curl if needed for nvm installer
    sandbox.exec(
        ["bash", "-c", "which curl || (apt-get update -qq && apt-get install -y -qq curl)"],
        cwd="/", timeout=120,
    )

    # Install nvm
    stdout, _, rc = sandbox.exec(
        ["bash", "-c", f"test -d {NVM_DIR} && echo '1' || echo '0'"],
        cwd="/", timeout=10,
    )
    if stdout.strip() != "1":
        _log(f"[{name}] Downloading nvm...")
        sandbox.exec(
            ["bash", "-c",
             f"(curl -fsSL {NVM_INSTALL_SCRIPT} || wget -qO- {NVM_INSTALL_SCRIPT}) | bash"],
            cwd="/", timeout=120,
        )

    # Install Node.js via nvm
    _log(f"[{name}] Installing Node.js {min_version} via nvm...")
    sandbox.exec(
        ["bash", "-c",
         f'export NVM_DIR="{NVM_DIR}" && '
         f'[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && '
         f'nvm install {min_version} && '
         f'nvm alias default {min_version}'],
        cwd="/", timeout=300,
    )
    symlink_nvm_bins(sandbox, NVM_DIR)

    # Verify
    stdout, _, rc = sandbox.exec(["node", "--version"], cwd="/", timeout=30)
    if rc == 0:
        npm_ver, _, _ = sandbox.exec(["npm", "--version"], cwd="/", timeout=30)
        _log(f"[{name}] Node.js {stdout.strip()}, npm {npm_ver.strip()}")
    else:
        raise RuntimeError("Node.js installation via nvm failed")


def symlink_nvm_bins(sandbox: Any, nvm_dir: str = "/root/.nvm") -> None:
    """Symlink all executables from the nvm default version bin dir to
    /usr/local/bin so non-interactive docker exec shells can find them.
    """
    sandbox.exec(
        ["bash", "-c",
         f'export NVM_DIR="{nvm_dir}" && '
         f'[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && '
         f'BIN_DIR=$(dirname "$(nvm which default)") && '
         f'for f in "$BIN_DIR"/*; do '
         f'  [ -f "$f" ] && [ -x "$f" ] && ln -sf "$f" /usr/local/bin/$(basename "$f"); '
         f'done'],
        cwd="/", timeout=30,
    )
