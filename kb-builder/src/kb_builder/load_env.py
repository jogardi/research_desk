"""
Centralized dotenv loader for kb-builder.

Key goals:
- Always load the kb-builder project's `.env` regardless of current working directory.
- Override any already-set environment variables (important when re-running in the same shell).
"""

from __future__ import annotations

from pathlib import Path

import dotenv


def load_env(*, override: bool = True) -> None:
    """
    Load environment variables from the kb-builder `.env`.

    By default we set override=True so changes to `.env` take effect even if the
    variable was previously exported in the shell / inherited process env.
    """
    project_root = Path(__file__).resolve().parents[2]  # .../knowledgebase/kb-builder
    dotenv_path = project_root / ".env"
    dotenv.load_dotenv(dotenv_path=dotenv_path, override=override)



