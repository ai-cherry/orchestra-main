from __future__ import annotations

import subprocess
from os import getenv
from pathlib import Path
from typing import Any, Dict

from . import BaseIntegration, ActionFn

__all__ = ["PulumiIntegration"]


class PulumiIntegration(BaseIntegration):
    """Interact with Pulumi via CLI – useful inside CI runners.

    *Requires* `pulumi` CLI to be installed in the runner. GitHub Actions images
    already include it via the `pulumi/action` setup step.
    """

    name = "pulumi"

    required_env_vars = ("PULUMI_ACCESS_TOKEN",)

    # ---------------------------------------------------------------------
    # Credential handling
    # ---------------------------------------------------------------------
    @property
    def credentials(self) -> Dict[str, str]:
        return {"PULUMI_ACCESS_TOKEN": getenv("PULUMI_ACCESS_TOKEN", "")}

    # ------------------------------------------------------------------
    # Public actions
    # ------------------------------------------------------------------
    def get_action(self, action_name: str) -> ActionFn:
        match action_name:
            case "preview":
                return self.preview
            case "up":
                return self.up
            case _:
                raise KeyError(f"Unknown Pulumi action: {action_name}")

    # ------------------------------------------------------------------
    # Implementation helpers
    # ------------------------------------------------------------------
    def _run_pulumi(self, cmd: list[str], work_dir: str | Path) -> str:
        env = {**self.credentials, **{"PULUMI_SKIP_UPDATE_CHECK": "true"}}
        result = subprocess.run(
            ["pulumi", *cmd],
            cwd=work_dir,
            env={**env, **{key: getenv(key, "") for key in env}},
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        return result.stdout.strip()

    # ---------------------------- actions ---------------------------------
    def preview(self, stack: str, work_dir: str = "infrastructure/pulumi") -> str:
        """Return the diff for *stack* without applying changes."""
        return self._run_pulumi(["preview", "--stack", stack, "--non-interactive", "--color", "always"], work_dir)

    def up(self, stack: str, work_dir: str = "infrastructure/pulumi", yes: bool = True) -> str:
        """Apply changes to *stack*."""
        cmd = ["up", "--stack", stack, "--non-interactive"]
        if yes:
            cmd.append("--yes")
        return self._run_pulumi(cmd, work_dir) 