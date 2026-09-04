from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Any


@dataclass(frozen=True)
class Pattern:
    code: str
    severity: str
    regex: re.Pattern[str]
    rationale: str


PATTERNS = (
    Pattern(
        "centered_rolling",
        "high",
        re.compile(r"rolling\s*\([^\n\)]*center\s*=\s*True", re.IGNORECASE),
        "Centered rolling can use observations on both sides of the current row; unsafe in a causal signal path unless explicitly lagged/label-only.",
    ),
    Pattern(
        "negative_shift",
        "high",
        re.compile(r"\.shift\s*\(\s*-\s*\d+"),
        "Negative shift moves future observations backward and is a common future-leakage path.",
    ),
    Pattern(
        "fixed_forward_window",
        "high",
        re.compile(r"FixedForwardWindowIndexer"),
        "Forward-looking window indexer requires explicit label-only justification.",
    ),
    Pattern(
        "pine_lookahead_on",
        "high",
        re.compile(r"barmerge\.lookahead_on"),
        "Pine lookahead_on can leak higher-timeframe future values into historical bars.",
    ),
    Pattern(
        "pine_pivot_review",
        "review",
        re.compile(r"ta\.pivot(?:high|low)\s*\("),
        "Pine pivots confirm only after right-side bars; verify signals use the confirmation time rather than retroactive pivot time.",
    ),
)


def scan_text(text: str, path: str = "<memory>") -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    lines = text.splitlines()
    for line_no, line in enumerate(lines, start=1):
        for pattern in PATTERNS:
            if pattern.regex.search(line):
                findings.append(
                    {
                        "path": path,
                        "line": line_no,
                        "code": pattern.code,
                        "severity": pattern.severity,
                        "rationale": pattern.rationale,
                        "snippet": line.strip()[:300],
                    }
                )
    return findings


def iter_code_files(root: str | Path) -> Iterable[Path]:
    root = Path(root)
    if root.is_file():
        yield root
        return
    excluded_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__", "tests"}
    excluded_files = {Path(__file__).resolve()}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in excluded_dirs for part in path.parts):
            continue
        if path.resolve() in excluded_files:
            continue
        if path.suffix.lower() in {".py", ".pine", ".pinescript"}:
            yield path


def scan_path(root: str | Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in iter_code_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        findings.extend(scan_text(text, str(path)))
    return findings
