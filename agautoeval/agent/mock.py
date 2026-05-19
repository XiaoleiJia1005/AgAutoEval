"""Mock agent for testing the harness pipeline."""

import time

from agautoeval.agent.base import AgentResult, BaseAgent


class MockAgent(BaseAgent):
    """A mock agent that returns a hardcoded patch for testing."""

    def run(self, repo_path: str, problem_statement: str) -> AgentResult:
        start = time.monotonic()
        time.sleep(0.1)

        patch = "diff --git a/calc.py b/calc.py\nindex d12ffba..4b65a37 100644\n--- a/calc.py\n+++ b/calc.py\n@@ -1,2 +1,2 @@\n def add(a, b):\n-    return a - b  # bug: should be a + b\n+    return a + b  # bug: should be a + b\n"

        return AgentResult(
            patch=patch,
            stdout=patch,
            stderr="",
            duration=time.monotonic() - start,
            success=True,
        )
