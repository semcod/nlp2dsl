"""Orientacja zapytania — file_list vs shell vs workflow (przed pełnym resolve_intent)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any, Literal

QueryCategory = Literal[
    "file_list_registry",
    "file_list_host",
    "shell",
    "workflow",
    "system_local",
    "unknown",
]

_FILE_LIST_RE = re.compile(
    r"(lista\s+plik|jakie\s+pliki|poka[zż]\s+plik|wykaz\s+plik|"
    r"list\s+files|show\s+files|list\s+user\s+files|lista\s+user\s+files|"
    r"user\s+files|lista\s+plik[oó]w\s+usera|"
    r"dost[eę]pne\s+plik|pliki\s+w\s+scope|zasoby\s+w\s+systemie)",
    re.IGNORECASE,
)

_REGISTRY_HINTS = (
    "rejestr",
    "access fabric",
    "wgrane",
    "localfs",
    "w workspace",
    "indeks rag",
    "mullm",
    "nie shell",
    "w scope",
)

_HOST_HINTS = (
    "na linux",
    "linuxie",
    "na hoście",
    "na hoscie",
    "hosta",
    "katalog domow",
    "katalogu domowym",
    "home directory",
    "folder domow",
    "systemowego usera",
    "/home/",
    " na ~",
)

_SHELL_PREFIX_RE = re.compile(
    r"^(run|exec|shell|wykonaj|uruchom)\s+",
    re.IGNORECASE,
)

_SHELL_NL_RE = re.compile(
    r"(?i)(dysk|miejsce\s+na\s+dysk|docker|kontener|git\s|status\s+git|"
    r"proces(y|ów)?|df\s|du\s-|free\s|systemctl|journalctl|"
    r"sprawd[zź]\s+(?!plik)|policz\s+)",
)

_WORKFLOW_RE = re.compile(
    r"(?i)(faktur|invoice|wyślij\s+mail|wyslij\s+mail|raport|crm|slack|telegram|workflow)",
)

_NLP2CMD_RUN_RE = re.compile(
    r"(?i)(wejd[zź]\s+na\s+|otw[oó]rz\s+|narysuj|rysuj|"
    r"jspaint|firefox|thunderbird|chrome|chromium|"
    r"minimizuj|zminimalizuj|desktop|przegl[aą]dark|"
    r"canvas|\.app\b|https?://|www\.)",
)

_PATH_TOKEN_RE = re.compile(
    r"lista\s+plik[oó]w?\s+(?:w\s+|z\s+|folderze\s+|katalogu\s+)?(\S+)",
    re.IGNORECASE,
)

_PATH_HINT_SKIP = frozenset(
    {
        "usera",
        "użytkownika",
        "uzytkownika",
        "user",
        "systemu",
        "systemowego",
        "system",
        "linux",
        "linuxie",
        "/",
        "rejestru",
        "rejestr",
        "w",
        "z",
        "na",
        "i",
        "oraz",
        "the",
        "files",
        "file",
        "plikow",
        "plików",
        "pliki",
        "plik",
        "access",
        "fabric",
        "projektu",
        "projectu",
        "project",
    }
)

_ROOT_LIST_RE = re.compile(r"lista\s+plik[oó]w?\s+/\s*$", re.IGNORECASE)
_SYSTEM_LIST_RE = re.compile(r"\b(systemu|systemow|system\b)", re.IGNORECASE)
_PROJECT_LIST_RE = re.compile(
    r"lista\s+plik[oó]w?\s+(?:projektu|projectu|project)\s+(\S+)",
    re.IGNORECASE,
)
_PROJECT_LIST_ONLY_RE = re.compile(
    r"lista\s+plik[oó]w?\s+(?:projektu|projectu|project)\s*$",
    re.IGNORECASE,
)
_LIST_PATH_REMAINDER_RE = re.compile(
    r"lista\s+plik[oó]w?\s+(?:w\s+|z\s+|folderze\s+|katalogu\s+)(.+)$",
    re.IGNORECASE,
)


@dataclass
class OrientationResult:
    category: QueryCategory
    suggested_action: str | None
    confidence: float
    reason_codes: list[str] = field(default_factory=list)
    shell_command: str | None = None
    list_scope: str | None = None
    connector: str = "mullm"

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "suggested_action": self.suggested_action,
            "confidence": self.confidence,
            "reason_codes": self.reason_codes,
            "shell_command": self.shell_command,
            "list_scope": self.list_scope,
            "connector": self.connector,
        }


def _has_registry_hint(text: str) -> bool:
    lowered = text.lower()
    return any(h in lowered for h in _REGISTRY_HINTS)


def _has_host_hint(text: str) -> bool:
    lowered = text.lower()
    return any(h in lowered for h in _HOST_HINTS) or "~" in lowered


def _is_file_list_query(text: str) -> bool:
    lowered = text.lower().strip()
    if _FILE_LIST_RE.search(lowered):
        return True
    return bool(
        re.search(r"\buser\s+files?\b", lowered)
        or re.search(r"\bfiles?\s+user\b", lowered)
        or (re.search(r"\bplik", lowered) and re.search(r"\b(lista|list|wykaz|poka)", lowered))
    )


def _file_list_scope(text: str) -> str:
    lowered = text.lower()
    if re.search(r"\b(systemu|systemow)", lowered):
        return "system"
    if re.search(r"\b(usera|użytkownika|user\s+files|moje\s+plik|wgrane|upload)\b", lowered):
        return "user"
    if re.search(r"\b(rag|indeks)\b", lowered) and "plik" in lowered:
        return "rag"
    m = _PROJECT_LIST_RE.search(lowered)
    if m:
        return m.group(1).strip(".,;:\"'").lower()
    m = _PATH_TOKEN_RE.search(lowered)
    if m:
        token = m.group(1).strip(".,;:\"'").lower()
        if token in ("linux", "linuxie"):
            return "host"
        if token not in _PATH_HINT_SKIP and not _has_registry_hint(token):
            return token
    return "all"


def _host_list_root() -> str:
    return (os.getenv("MULLM_SHELL_HOST_PREFIX") or "/host-home").strip() or "/host-home"


def _normalize_orient_path(path: str, root: str) -> str:
    p = path.strip()
    if p.startswith("~"):
        return root + p[1:]
    if p.startswith("$HOME"):
        return root + p[5:]
    return p


def _resolve_project_host_path(project_name: str, root: str) -> tuple[str, list[str]]:
    name = project_name.strip().strip(".,;:\"'")
    slug = re.sub(r"[^\w.-]+", "_", name.lower()) or "project"
    org = (os.getenv("MULLM_SHELL_PROJECT_ORG") or "wronai").strip() or "wronai"
    path = f"{root}/github/{org}/{name}"
    return path, [f"orientation_path_project_{slug}", "orientation_path_project"]


def _resolve_list_path_remainder(remainder: str, root: str) -> tuple[str, list[str]]:
    raw = remainder.strip().strip(".,;:\"'")
    parts = [p for p in re.split(r"[\s/]+", raw) if p]
    if not parts:
        return root, ["orientation_path_default"]
    if parts[0].lower() in ("github", "gitlab"):
        path = f"{root}/{'/'.join(parts)}"
        return path, [f"orientation_path_hint_{'_'.join(parts).lower()}"]
    if len(parts) == 1:
        token = parts[0]
        return f"{root}/{token}", [f"orientation_path_hint_{token.lower()}"]
    path = f"{root}/{'/'.join(parts)}"
    return path, [f"orientation_path_hint_{'_'.join(parts).lower()}"]


def _resolve_file_list_host_command(text: str) -> tuple[str, list[str]]:
    root = _host_list_root()
    raw = text.strip()
    lowered = raw.lower()

    if _ROOT_LIST_RE.search(lowered):
        return "ls -la /", ["orientation_path_root"]

    if re.search(r"\b(usera|użytkownika|user\s+files|systemowego\s+usera)\b", lowered):
        return f"ls -la {root}", ["orientation_path_host_home"]

    if _SYSTEM_LIST_RE.search(lowered):
        return "ls -la /", ["orientation_path_system_root"]

    if _PROJECT_LIST_ONLY_RE.search(lowered):
        return f"ls -la {root}/github", ["orientation_path_projects"]

    m = _PROJECT_LIST_RE.search(lowered)
    if m:
        path, codes = _resolve_project_host_path(m.group(1), root)
        return f"ls -la {path}", codes

    m = _LIST_PATH_REMAINDER_RE.search(raw)
    if m:
        path, codes = _resolve_list_path_remainder(m.group(1), root)
        return f"ls -la {path}", codes

    for pat in (r"(~[/\w.-]*)", r"(\$HOME[/\w.-]*)"):
        m = re.search(pat, raw)
        if m:
            path = _normalize_orient_path(m.group(1), root)
            return f"ls -la {path}", ["orientation_path_explicit"]

    m = re.search(r"(/[\w./-]+)", raw)
    if m:
        path = m.group(1).strip()
        if path == "/":
            return "ls -la /", ["orientation_path_root"]
        return f"ls -la {path}", ["orientation_path_explicit"]

    m = _PATH_TOKEN_RE.search(lowered)
    if m:
        token = m.group(1).strip(".,;:\"'")
        tl = token.lower()
        if tl in ("linux", "linuxie"):
            return f"ls -la {root}", ["orientation_path_host_home"]
        if tl not in _PATH_HINT_SKIP and not _has_registry_hint(token):
            return f"ls -la {root}/{token}", [f"orientation_path_hint_{tl}"]

    return f"ls -la {root}", ["orientation_path_default"]


def _orient_file_list(raw: str, *, conn: str) -> OrientationResult:
    scope = _file_list_scope(raw)
    if _has_registry_hint(raw):
        return OrientationResult(
            category="file_list_registry",
            suggested_action="mullm_list_files",
            confidence=0.93,
            reason_codes=["orientation_file_list_registry", f"scope_{scope}"],
            list_scope=scope,
            connector=conn,
        )
    if conn == "mullm" or _has_host_hint(raw):
        shell_cmd, path_codes = _resolve_file_list_host_command(raw)
        conf = 0.91 if _has_host_hint(raw) else 0.88
        if any(c.startswith("orientation_path_hint_") for c in path_codes):
            conf = max(conf, 0.9)
        return OrientationResult(
            category="file_list_host",
            suggested_action="mullm_shell_task",
            confidence=conf,
            reason_codes=["orientation_file_list_host", f"scope_{scope}", *path_codes],
            shell_command=shell_cmd,
            list_scope=scope,
            connector=conn,
        )
    return OrientationResult(
        category="system_local",
        suggested_action="system_file_list",
        confidence=0.84,
        reason_codes=["orientation_system_file_list", f"scope_{scope}"],
        list_scope=scope,
        connector=conn,
    )


def _orient_shell_prefix(raw: str, *, conn: str) -> OrientationResult | None:
    if not _SHELL_PREFIX_RE.match(raw):
        return None
    cmd = _SHELL_PREFIX_RE.sub("", raw).strip()
    return OrientationResult(
        category="shell",
        suggested_action="mullm_shell_task",
        confidence=0.92,
        reason_codes=["shell_prefix", "orientation_shell"],
        shell_command=cmd or None,
        connector=conn,
    )


def orient_query(text: str, *, connector: str = "mullm") -> OrientationResult:
    """
    Klasyfikuje zapytanie bez LLM — Mullm BFF woła to przed regułami / OpenRouter.

    connector=mullm: lista plików usera domyślnie → katalog domowy (host), chyba że jawny rejestr.
    connector=local: „pokaż pliki” → system_file_list (projekt lokalny).
    """
    raw = (text or "").strip()
    conn = (connector or "mullm").lower().strip()
    if not raw:
        return OrientationResult(
            category="unknown",
            suggested_action=None,
            confidence=0.0,
            reason_codes=["empty_message"],
            connector=conn,
        )

    if hit := _orient_shell_prefix(raw, conn=conn):
        return hit

    if _is_file_list_query(raw):
        return _orient_file_list(raw, conn=conn)

    if _SHELL_NL_RE.search(raw):
        return OrientationResult(
            category="shell",
            suggested_action="mullm_shell_task",
            confidence=0.82,
            reason_codes=["orientation_shell_nl"],
            connector=conn,
        )

    if _WORKFLOW_RE.search(raw):
        return OrientationResult(
            category="workflow",
            suggested_action=None,
            confidence=0.75,
            reason_codes=["orientation_workflow_hint"],
            connector=conn,
        )

    if _NLP2CMD_RUN_RE.search(raw):
        return OrientationResult(
            category="shell",
            suggested_action="mullm_shell_task",
            confidence=0.84,
            reason_codes=["orientation_nlp2cmd_run"],
            connector=conn,
        )

    return OrientationResult(
        category="unknown",
        suggested_action=None,
        confidence=0.35,
        reason_codes=["orientation_unknown"],
        connector=conn,
    )
