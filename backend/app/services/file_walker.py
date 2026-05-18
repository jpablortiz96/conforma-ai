"""Candidate file discovery for the scanner agent."""

from __future__ import annotations

import json
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
import re

CANDIDATE_PATTERNS = (
    "*.ipynb",
    "*model*.py",
    "*train*.py",
    "*inference*.py",
    "*ml*.py",
    "*ai*.py",
)
MODEL_EXTENSIONS = {".onnx", ".pt", ".h5", ".pkl"}
AI_DIRECTORY_NAMES = {"models", "weights", "checkpoints"}
MANIFEST_NAMES = {"requirements.txt", "pyproject.toml", "package.json"}
README_PREFIXES = ("readme",)
DEPENDENCY_KEYWORDS = {
    "torch",
    "tensorflow",
    "transformers",
    "scikit-learn",
    "sklearn",
    "keras",
    "xgboost",
    "langchain",
    "openai",
    "anthropic",
    "google-generativeai",
    "google-genai",
    "huggingface",
    "sentence-transformers",
    "onnxruntime",
}
README_SIGNAL_MAP = {
    "ai": "README mentions AI capabilities",
    "machine learning": "README mentions machine learning",
    "ml": "README mentions ML capabilities",
    "neural": "README mentions neural networks",
    "model": "README mentions model behavior",
    "predict": "README mentions predictive outputs",
    "classify": "README mentions classification",
    "score": "README mentions scoring",
    "recommend": "README mentions recommendation models",
    "chatbot": "README mentions chatbot behavior",
    "assistant": "README mentions assistant behavior",
    "dialogue": "README mentions dialogue systems",
    "llm": "README mentions LLM behavior",
}
DOMAIN_KEYWORD_GROUPS = (
    (("resume", "cv", "curriculum vitae"), "resume or CV workflows"),
    (("recruitment", "hiring", "talent acquisition", "job matching"), "recruitment or hiring workflows"),
    (("candidate", "applicant"), "candidate or applicant evaluation"),
    (("screening",), "screening workflows"),
)
RECRUITMENT_STRONG_CONTEXT_KEYWORDS = (
    "recruitment",
    "hiring",
    "candidate",
    "applicant",
    "job matching",
    "talent acquisition",
    "employment",
)
RECRUITMENT_EXPLICIT_PHRASES = (
    "resume screening",
    "cv screening",
    "candidate ranking",
    "applicant screening",
    "recruitment screening",
    "resume scoring",
    "resume ranking",
)
SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
    ".next",
}


def _contains_keyword(text: str, keyword: str) -> bool:
    normalized_keyword = keyword.lower().replace("-", " ").strip()
    if not normalized_keyword:
        return False
    pattern = r"\b" + r"\s+".join(re.escape(part) for part in normalized_keyword.split()) + r"\b"
    return re.search(pattern, text) is not None


@dataclass(slots=True)
class CandidateFile:
    """Compact file excerpt passed into the scanner model."""

    path: str
    reason: str
    excerpt: str
    signals: list[str]


@dataclass(slots=True)
class RepoInspection:
    """Candidate inventory produced before the Gemini call."""

    repo_path: str
    files_inspected: int
    candidate_files: list[CandidateFile]
    dependency_signals: list[str]
    readme_signals: list[str]
    domain_signals: list[str]
    truncated: bool


def _iter_repo_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in repo_root.rglob("*"):
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.is_file():
            files.append(path)
    return sorted(files)


def _read_text_excerpt(path: Path, *, char_limit: int = 1200) -> str:
    try:
        if path.suffix.lower() == ".ipynb":
            payload = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
            cells = payload.get("cells", [])[:3]
            snippets: list[str] = []
            for cell in cells:
                source = "".join(cell.get("source", []))
                if source.strip():
                    snippets.append(source.strip())
            return "\n\n".join(snippets)[:char_limit]
        return path.read_text(encoding="utf-8", errors="ignore")[:char_limit]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return ""


def _path_matches_candidate(path: Path) -> tuple[bool, str, int]:
    relative = path.as_posix()
    lower_name = path.name.lower()
    lower_relative = relative.lower()

    if path.suffix.lower() in MODEL_EXTENSIONS:
        return True, "model_artifact", 100
    if any(part.lower() in AI_DIRECTORY_NAMES for part in path.parts):
        return True, "ai_directory", 80
    if lower_name in MANIFEST_NAMES:
        return True, "dependency_manifest", 70
    if lower_name.startswith(README_PREFIXES):
        return True, "readme", 65
    for pattern in CANDIDATE_PATTERNS:
        if fnmatch(lower_name, pattern) or fnmatch(lower_relative, pattern):
            return True, "code_pattern", 60
    return False, "", 0


def _extract_manifest_signals(path: Path, text: str) -> list[str]:
    lower_text = text.lower()
    signals: list[str] = []
    for dependency in sorted(DEPENDENCY_KEYWORDS):
        if dependency in lower_text:
            signals.append(f"dependency signal: {path.name} references {dependency}")
    return signals


def _extract_readme_signals(path: Path, text: str) -> list[str]:
    lower_text = text.lower()
    signals: list[str] = []
    for keyword, message in README_SIGNAL_MAP.items():
        if keyword in lower_text:
            signals.append(f"README signal: {path.name} {message.lower()}")
    signals.extend(_extract_domain_signals(path.name, text, verb="mentions"))
    return signals


def _extract_domain_signals(source_label: str, text: str, *, verb: str) -> list[str]:
    normalized_text = text.lower().replace("_", " ").replace("-", " ")
    signals: list[str] = []
    for keywords, label in DOMAIN_KEYWORD_GROUPS:
        if label == "resume or CV workflows":
            has_resume_keyword = any(_contains_keyword(normalized_text, keyword) for keyword in keywords)
            has_employment_context = any(
                _contains_keyword(normalized_text, keyword)
                for keyword in RECRUITMENT_STRONG_CONTEXT_KEYWORDS
            )
            has_explicit_phrase = any(
                _contains_keyword(normalized_text, keyword) for keyword in RECRUITMENT_EXPLICIT_PHRASES
            )
            if (has_resume_keyword and has_employment_context) or has_explicit_phrase:
                signals.append(f"domain signal: {source_label} {verb} {label}")
            continue
        if any(_contains_keyword(normalized_text, keyword) for keyword in keywords):
            signals.append(f"domain signal: {source_label} {verb} {label}")
    return signals


def _extract_code_signals(path: Path, text: str) -> list[str]:
    lower_text = text.lower()
    lower_path = path.as_posix().lower().replace("_", " ").replace("-", " ")
    signals: list[str] = []
    for dependency in sorted(DEPENDENCY_KEYWORDS):
        if f"import {dependency}" in lower_text or f"from {dependency}" in lower_text:
            signals.append(f"dependency signal: {path.as_posix()} imports {dependency}")
    if "model" in path.name.lower():
        signals.append(f"file signal: {path.as_posix()} matched *model*.py")
    if "train" in path.name.lower():
        signals.append(f"file signal: {path.as_posix()} matched *train*.py")
    if "inference" in path.name.lower():
        signals.append(f"file signal: {path.as_posix()} matched *inference*.py")
    if any(part.lower() in AI_DIRECTORY_NAMES for part in path.parts):
        signals.append(f"file signal: {path.as_posix()} is under an AI model directory")
    signals.extend(_extract_domain_signals(path.as_posix(), f"{path.as_posix()} {text}", verb="suggests"))
    if any(keyword in lower_path for keyword in ("resume", "cv", "curriculum vitae")) and any(
        keyword in lower_path for keyword in ("screen", "rank", "recruit", "candidate", "applicant")
    ):
        signals.append(f"file signal: {path.as_posix()} suggests resume screening workflow")
    return signals


def _build_candidate(path: Path, repo_root: Path, reason: str) -> CandidateFile:
    relative_path = path.relative_to(repo_root).as_posix()
    excerpt = _read_text_excerpt(path)
    signals: list[str] = []

    if path.name.lower() in MANIFEST_NAMES:
        signals.extend(_extract_manifest_signals(path, excerpt))
    elif path.name.lower().startswith(README_PREFIXES):
        signals.extend(_extract_readme_signals(path, excerpt))
    else:
        signals.extend(_extract_code_signals(path.relative_to(repo_root), excerpt))

    if not signals:
        signals.append(f"file signal: {relative_path} matched {reason}")

    return CandidateFile(path=relative_path, reason=reason, excerpt=excerpt, signals=signals[:8])


def collect_candidate_artifacts(
    repo_path: str | Path,
    *,
    max_files_to_inspect: int = 200,
) -> RepoInspection:
    """Inspect a repository and extract a compact shortlist for Gemini."""

    repo_root = Path(repo_path)
    discovered_files = _iter_repo_files(repo_root)
    scored_candidates: list[tuple[int, CandidateFile]] = []
    dependency_signals: list[str] = []
    readme_signals: list[str] = []
    domain_signals: list[str] = []

    for path in discovered_files:
        matched, reason, score = _path_matches_candidate(path.relative_to(repo_root))
        if not matched:
            continue

        candidate = _build_candidate(path, repo_root, reason)
        scored_candidates.append((score, candidate))

        for signal in candidate.signals:
            if signal.startswith("dependency signal:") and signal not in dependency_signals:
                dependency_signals.append(signal)
            if signal.startswith("README signal:") and signal not in readme_signals:
                readme_signals.append(signal)
            if signal.startswith("domain signal:") and signal not in domain_signals:
                domain_signals.append(signal)

    scored_candidates.sort(key=lambda item: (-item[0], item[1].path))
    truncated = len(scored_candidates) > max_files_to_inspect
    candidate_files = [candidate for _, candidate in scored_candidates[:max_files_to_inspect]]

    return RepoInspection(
        repo_path=str(repo_root),
        files_inspected=len(candidate_files),
        candidate_files=candidate_files,
        dependency_signals=dependency_signals[:20],
        readme_signals=readme_signals[:20],
        domain_signals=domain_signals[:20],
        truncated=truncated,
    )
