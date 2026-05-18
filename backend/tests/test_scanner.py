"""Scanner agent tests."""

from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.agents.scanner import ScannerAgent
from app.core.gemini_client import GeminiClientError
from app.db.session import get_db
from app.main import app
from app.services.repo_cloner import ClonedRepo


class FakeAsyncSession:
    """Minimal async-session double for router and agent tests."""

    def __init__(self) -> None:
        self.records: dict[str, list[object]] = {
            "audits": [],
            "ai_systems": [],
            "agent_runs": [],
            "artifacts": [],
            "gaps": [],
        }
        self.commits = 0
        self.rollbacks = 0

    def add(self, instance: object) -> None:
        table_name = getattr(instance.__class__, "__tablename__", None)
        if hasattr(instance, "id") and getattr(instance, "id", None) is None:
            setattr(instance, "id", uuid4())
        if table_name in self.records and instance not in self.records[table_name]:
            self.records[table_name].append(instance)

    def add_all(self, instances: list[object]) -> None:
        for instance in instances:
            self.add(instance)

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, instance: object) -> None:
        return None

    async def rollback(self) -> None:
        self.rollbacks += 1


def _build_demo_repo(repo_root: Path) -> Path:
    repo_path = repo_root / "repo"
    (repo_path / "models").mkdir(parents=True)
    (repo_path / "nlu").mkdir(parents=True)
    (repo_path / "actions").mkdir(parents=True)
    (repo_path / "README.md").write_text(
        (
            "# Rasa style assistant\n\n"
            "This project contains a chatbot with NLU, dialogue policies, and response models.\n"
        ),
        encoding="utf-8",
    )
    (repo_path / "requirements.txt").write_text(
        "tensorflow\ntransformers\nscikit-learn\n", encoding="utf-8"
    )
    (repo_path / "models" / "policy_model.py").write_text(
        "import tensorflow as tf\nclass PolicyModel:\n    pass\n",
        encoding="utf-8",
    )
    (repo_path / "nlu" / "train_model.py").write_text(
        "from sklearn.pipeline import Pipeline\n# train conversational intent model\n",
        encoding="utf-8",
    )
    (repo_path / "actions" / "response_generator.py").write_text(
        "# retrieval-based response action\n",
        encoding="utf-8",
    )
    return repo_path


def _build_resume_screening_repo(repo_root: Path) -> Path:
    repo_path = repo_root / "Resume-Screening"
    (repo_path / "src" / "resume_screening").mkdir(parents=True)
    (repo_path / "README.md").write_text(
        (
            "# Resume Screening\n\n"
            "Machine learning project for resume screening in recruitment workflows.\n"
            "The notebook evaluates applicant resumes, candidate suitability, and hiring-related skills.\n"
        ),
        encoding="utf-8",
    )
    (repo_path / "requirements.txt").write_text(
        "scikit-learn\npandas\nnumpy\n", encoding="utf-8"
    )
    (repo_path / "Resume_Screening.ipynb").write_text(
        (
            '{"cells":[{"cell_type":"markdown","source":["Resume screening for recruitment and candidate ranking."]},'
            '{"cell_type":"code","source":["# applicant screening workflow\\n"]}],"metadata":{},"nbformat":4,"nbformat_minor":5}'
        ),
        encoding="utf-8",
    )
    (repo_path / "src" / "resume_screening" / "model.py").write_text(
        "from sklearn.ensemble import RandomForestClassifier\n# score applicant resumes for hiring teams\n",
        encoding="utf-8",
    )
    return repo_path


def _build_llm_resume_training_repo(repo_root: Path) -> Path:
    repo_path = repo_root / "llm.c"
    (repo_path / "scripts").mkdir(parents=True)
    (repo_path / "train_gpt2.py").write_text(
        "import torch\n# train gpt style transformer\n",
        encoding="utf-8",
    )
    (repo_path / "README.md").write_text(
        (
            "# llm.c\n\n"
            "Minimal language model training and inference project.\n"
            "Supports checkpoint resume training, transformer inference, and GPT experiments.\n"
        ),
        encoding="utf-8",
    )
    (repo_path / "scripts" / "README.md").write_text(
        "Use this script to resume training from a checkpoint.\n",
        encoding="utf-8",
    )
    return repo_path


@pytest.mark.asyncio
async def test_scanner_agent_uses_gemini_output_when_available(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """ScannerAgent should persist AI systems and mark the run as Gemini-backed."""

    fake_db = FakeAsyncSession()
    repo_root = tmp_path / "clone"
    repo_path = _build_demo_repo(repo_root)
    cleanup_calls: list[Path] = []

    async def fake_shallow_clone(repo_url: str) -> ClonedRepo:
        return ClonedRepo(temp_dir=repo_root, repo_path=repo_path)

    async def fake_cleanup_clone(cloned_repo: ClonedRepo | Path | str | None) -> None:
        if cloned_repo is None:
            return
        target = cloned_repo.temp_dir if isinstance(cloned_repo, ClonedRepo) else Path(cloned_repo)
        cleanup_calls.append(target)
        shutil.rmtree(target, ignore_errors=True)

    async def fake_call_flash_json(prompt: str, temperature: float = 0.0) -> dict[str, object]:
        return {
            "ai_systems_found": [
                {
                    "name": "assistant_dialogue_policy",
                    "description": (
                        "This repository contains a dialogue policy model used to choose the next "
                        "assistant action in a conversational workflow."
                    ),
                    "source_files": ["models/policy_model.py", "nlu/train_model.py"],
                    "detection_signals": [
                        "dependency signal: requirements.txt references tensorflow",
                        "README signal: README.md mentions chatbot behavior",
                    ],
                }
            ],
            "summary": "One chatbot-oriented AI system was identified from policy and NLU evidence.",
        }

    monkeypatch.setattr("app.agents.scanner.shallow_clone", fake_shallow_clone)
    monkeypatch.setattr("app.agents.scanner.cleanup_clone", fake_cleanup_clone)
    monkeypatch.setattr("app.agents.scanner.call_flash_json", fake_call_flash_json)

    agent = ScannerAgent(fake_db)
    result = await agent.run(
        {"repo_url": "https://github.com/rasahq/rasa", "max_files_to_inspect": 50},
        audit_id=uuid4(),
    )

    assert result["mode"] == "gemini"
    assert result["files_inspected"] >= 3
    assert len(result["ai_systems_found"]) == 1
    assert len(fake_db.records["ai_systems"]) == 1
    assert len(fake_db.records["agent_runs"]) == 1
    assert cleanup_calls
    assert not repo_root.exists()


def test_scanner_endpoint_fallback_persists_inventory_and_cleans_up(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The scanner endpoint should fall back deterministically and persist audit artifacts."""

    fake_db = FakeAsyncSession()
    repo_root = tmp_path / "clone"
    repo_path = _build_demo_repo(repo_root)
    cleanup_calls: list[Path] = []

    async def override_get_db():
        yield fake_db

    async def fake_shallow_clone(repo_url: str) -> ClonedRepo:
        return ClonedRepo(temp_dir=repo_root, repo_path=repo_path)

    async def fake_cleanup_clone(cloned_repo: ClonedRepo | Path | str | None) -> None:
        if cloned_repo is None:
            return
        target = cloned_repo.temp_dir if isinstance(cloned_repo, ClonedRepo) else Path(cloned_repo)
        cleanup_calls.append(target)
        shutil.rmtree(target, ignore_errors=True)

    async def failing_call_flash_json(prompt: str, temperature: float = 0.0) -> dict[str, object]:
        raise GeminiClientError("forced fallback")

    monkeypatch.setattr("app.agents.scanner.shallow_clone", fake_shallow_clone)
    monkeypatch.setattr("app.agents.scanner.cleanup_clone", fake_cleanup_clone)
    monkeypatch.setattr("app.agents.scanner.call_flash_json", failing_call_flash_json)
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/agents/scanner",
                json={"repo_url": "https://github.com/rasahq/rasa", "max_files_to_inspect": 50},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "fallback"
    assert payload["repo_url"] == "https://github.com/rasahq/rasa"
    assert payload["files_inspected"] >= 3
    assert payload["ai_systems_found"]
    for candidate in payload["ai_systems_found"]:
        assert candidate["id"]
        assert candidate["name"]
        assert candidate["description"]
        assert candidate["source_files"]
        assert candidate["detection_signals"]

    assert len(fake_db.records["audits"]) == 1
    assert len(fake_db.records["ai_systems"]) == len(payload["ai_systems_found"])
    assert len(fake_db.records["agent_runs"]) == 1
    assert cleanup_calls
    assert not repo_root.exists()


@pytest.mark.asyncio
async def test_scanner_fallback_avoids_generic_candidate_for_resume_screening_repo(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Recruitment-heavy repository evidence should produce a specific resume-screening candidate."""

    fake_db = FakeAsyncSession()
    repo_root = tmp_path / "clone"
    repo_path = _build_resume_screening_repo(repo_root)
    cleanup_calls: list[Path] = []

    async def fake_shallow_clone(repo_url: str) -> ClonedRepo:
        return ClonedRepo(temp_dir=repo_root, repo_path=repo_path)

    async def fake_cleanup_clone(cloned_repo: ClonedRepo | Path | str | None) -> None:
        if cloned_repo is None:
            return
        target = cloned_repo.temp_dir if isinstance(cloned_repo, ClonedRepo) else Path(cloned_repo)
        cleanup_calls.append(target)
        shutil.rmtree(target, ignore_errors=True)

    async def failing_call_flash_json(prompt: str, temperature: float = 0.0) -> dict[str, object]:
        raise GeminiClientError("forced fallback")

    monkeypatch.setattr("app.agents.scanner.shallow_clone", fake_shallow_clone)
    monkeypatch.setattr("app.agents.scanner.cleanup_clone", fake_cleanup_clone)
    monkeypatch.setattr("app.agents.scanner.call_flash_json", failing_call_flash_json)

    agent = ScannerAgent(fake_db)
    result = await agent.run(
        {
            "repo_url": "https://github.com/anukalp-mishra/Resume-Screening",
            "max_files_to_inspect": 80,
        },
        audit_id=uuid4(),
    )

    assert result["mode"] == "fallback"
    assert result["ai_systems_found"]
    candidate = result["ai_systems_found"][0]
    assert candidate["name"] == "resume_screening_model"
    assert candidate["name"] != "repository_ai_feature"
    assert "recruit" in candidate["description"].lower()
    assert any("repository name contains Resume-Screening" in signal for signal in candidate["detection_signals"])
    assert any("machine learning" in signal.lower() for signal in candidate["detection_signals"])
    assert any(
        "resume screening workflow" in signal.lower() or "resume or cv workflows" in signal.lower()
        for signal in candidate["detection_signals"]
    )
    assert cleanup_calls
    assert not repo_root.exists()


@pytest.mark.asyncio
async def test_scanner_fallback_does_not_misread_resume_training_as_recruitment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """LLM repos that mention resume training should stay generative, not recruitment-related."""

    fake_db = FakeAsyncSession()
    repo_root = tmp_path / "clone"
    repo_path = _build_llm_resume_training_repo(repo_root)
    cleanup_calls: list[Path] = []

    async def fake_shallow_clone(repo_url: str) -> ClonedRepo:
        return ClonedRepo(temp_dir=repo_root, repo_path=repo_path)

    async def fake_cleanup_clone(cloned_repo: ClonedRepo | Path | str | None) -> None:
        if cloned_repo is None:
            return
        target = cloned_repo.temp_dir if isinstance(cloned_repo, ClonedRepo) else Path(cloned_repo)
        cleanup_calls.append(target)
        shutil.rmtree(target, ignore_errors=True)

    async def failing_call_flash_json(prompt: str, temperature: float = 0.0) -> dict[str, object]:
        raise GeminiClientError("forced fallback")

    monkeypatch.setattr("app.agents.scanner.shallow_clone", fake_shallow_clone)
    monkeypatch.setattr("app.agents.scanner.cleanup_clone", fake_cleanup_clone)
    monkeypatch.setattr("app.agents.scanner.call_flash_json", failing_call_flash_json)

    agent = ScannerAgent(fake_db)
    result = await agent.run(
        {
            "repo_url": "https://github.com/karpathy/llm.c",
            "max_files_to_inspect": 50,
        },
        audit_id=uuid4(),
    )

    assert result["mode"] == "fallback"
    assert result["ai_systems_found"]
    candidate = result["ai_systems_found"][0]
    assert candidate["name"] == "language_model_training_and_inference"
    assert candidate["name"] != "resume_screening_model"
    assert "language model" in candidate["description"].lower()
    assert cleanup_calls
    assert not repo_root.exists()


def test_scanner_endpoint_returns_422_for_invalid_agent_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The scanner route should not leak a 500 when the final payload is malformed."""

    fake_db = FakeAsyncSession()

    async def override_get_db():
        yield fake_db

    async def fake_scanner_run(self, input_data, audit_id):
        return {
            "audit_id": audit_id,
            "repo_url": input_data["repo_url"],
            "files_inspected": 4,
            "ai_systems_found": [
                {
                    "id": str(uuid4()),
                    "name": "resume_screening_model",
                    # Missing description on purpose to trigger response validation.
                    "source_files": ["src/model.py"],
                    "detection_signals": ["README signal: README mentions recruitment screening"],
                }
            ],
            "summary": "Malformed payload for regression coverage.",
            "mode": "gemini",
        }

    monkeypatch.setattr("app.routers.agents.ScannerAgent.run", fake_scanner_run)
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/agents/scanner",
                json={
                    "repo_url": "https://github.com/anukalp-mishra/Resume-Screening",
                    "max_files_to_inspect": 80,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert "description" in response.json()["detail"]
    assert len(fake_db.records["audits"]) == 1
    assert fake_db.records["audits"][0].status == "failed"
