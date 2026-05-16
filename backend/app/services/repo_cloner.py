"""Repository cloning helpers for the scanner agent."""

from __future__ import annotations

import asyncio
import os
import shutil
import stat
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from app.core.exceptions import RepositoryCloneError


@dataclass(slots=True)
class ClonedRepo:
    """Filesystem handle for a shallow-cloned repository."""

    temp_dir: Path
    repo_path: Path


def _clone_sync(repo_url: str) -> ClonedRepo:
    temp_dir = Path(tempfile.mkdtemp(prefix="conforma-scan-"))
    repo_path = temp_dir / "repo"
    command = [
        "git",
        "clone",
        "--depth",
        "1",
        "--filter=blob:none",
        "--no-tags",
        repo_url,
        str(repo_path),
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RepositoryCloneError("git is not installed or not available on PATH.") from exc
    except subprocess.CalledProcessError as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        stderr = (exc.stderr or exc.stdout or "").strip()
        raise RepositoryCloneError(f"Failed to clone repository: {stderr or repo_url}") from exc

    return ClonedRepo(temp_dir=temp_dir, repo_path=repo_path)


async def shallow_clone(repo_url: str) -> ClonedRepo:
    """Shallow-clone a public repository into a temporary directory."""

    return await asyncio.to_thread(_clone_sync, repo_url)


def _handle_remove_readonly(func, path: str, _exc_info) -> None:
    """Retry directory cleanup after clearing Windows read-only flags."""

    os.chmod(path, stat.S_IWRITE)
    func(path)


def _cleanup_sync(temp_dir: Path) -> None:
    for _ in range(3):
        try:
            shutil.rmtree(temp_dir, onerror=_handle_remove_readonly)
            return
        except FileNotFoundError:
            return
        except OSError:
            time.sleep(0.2)

    shutil.rmtree(temp_dir, ignore_errors=True)


async def cleanup_clone(cloned_repo: ClonedRepo | Path | str | None) -> None:
    """Remove a cloned repository temp directory if it exists."""

    if cloned_repo is None:
        return

    if isinstance(cloned_repo, ClonedRepo):
        temp_dir = cloned_repo.temp_dir
    else:
        temp_dir = Path(cloned_repo)

    if not temp_dir.exists():
        return

    await asyncio.to_thread(_cleanup_sync, temp_dir)
