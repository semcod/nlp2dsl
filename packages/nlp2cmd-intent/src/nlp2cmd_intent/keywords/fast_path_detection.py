"""Fast-path intent detection helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional, Sequence

from nlp2cmd_intent.keywords.keyword_patterns import KeywordPatterns


@dataclass(frozen=True)
class FastPathHit:
    domain: str
    intent: str
    confidence: float
    entities: dict[str, Any] = field(default_factory=dict)
    matched_keyword: str = ""


ExplicitOverride = tuple[str, str, str, str]


def normalize_url(raw: str) -> str:
    u = (raw or "").strip().strip('""')
    if not u:
        return u
    if u.startswith(("http://", "https://", "file://")):
        return u
    if u.startswith("www."):
        return f"https://{u}"
    if re.match(r"^[a-zA-Z0-9][\w\-\.]*\.[a-zA-Z]{2,}(?:/[^\s\'\"]*)?$", u):
        return f"https://{u}"
    return u


def match_explicit_overrides(
    overrides: Sequence[ExplicitOverride],
    text_normalized: str,
) -> Optional[FastPathHit]:
    for kw, domain, intent, matched_kw in overrides:
        if kw in text_normalized:
            return FastPathHit(domain=domain, intent=intent, confidence=0.95, matched_keyword=matched_kw)
    return None


def match_exact_commands(text_lower: str) -> Optional[FastPathHit]:
    # Exact single-word / short command matches
    _EXACT_COMMANDS = {
        "ps": ("shell", "list_processes"),
        "ls": ("shell", "list"),
        "top": ("shell", "list_processes"),
        "df": ("shell", "disk_usage"),
        "du": ("shell", "disk_usage"),
        "pwd": ("shell", "list"),
    }
    stripped = text_lower.strip()
    if stripped in _EXACT_COMMANDS:
        domain, intent = _EXACT_COMMANDS[stripped]
        return FastPathHit(domain=domain, intent=intent, confidence=0.95, matched_keyword=stripped)

def run_domain_fast_path_after_exact(
    text_lower: str,
    patterns: KeywordPatterns,
) -> Optional[FastPathHit]:
    # SQL keyword fast-path (highest priority — explicit SQL syntax)
    _SQL_EXACT = {
        "select ": "select", "insert into": "insert", "update ": "update",
        "delete from": "delete", "delete from ": "delete",  # More specific
        "create table": "create_table", "drop table": "drop_table",
        "alter table": "alter_table", "truncate ": "truncate",
        "create index": "create_index", "create view": "create_view",
        "create database": "create_database",
    }
    for kw, intent in _SQL_EXACT.items():
        if kw in text_lower:
            return FastPathHit(domain="sql", intent=intent, confidence=0.95)

    # Docker fast-path — explicit docker/container terms (ordered: specific first)
    _DOCKER_TERMS = [
        ("docker compose", "compose_up"), ("docker-compose", "compose_up"),
        ("compose up", "compose_up"), ("uruchom docker compose", "compose_up"),
        ("docker ps", "list"), ("docker run", "run"), ("docker stop", "stop"),
        ("docker start", "start"), ("docker rm", "remove"), ("docker rmi", "remove_image"),
        ("docker pull", "pull"), ("docker push", "push"), ("docker build", "build"),
        ("docker exec", "exec"), ("docker logs", "logs"), ("docker image", "images"),
        ("docker volume", "volume"), ("docker network", "network"),
        ("docker ", "list"),
    ]
    for kw, intent in _DOCKER_TERMS:
        if kw in text_lower:
            return FastPathHit(domain="docker", intent=intent, confidence=0.9)

    # Docker container-specific terms (with action context)
    _DOCKER_CONTAINER_ACTIONS = [
        ("uruchom kontener", "run"), ("run container", "run"), ("start container", "start"),
        ("uruchom container", "run"), ("run kontener", "run"), ("start kontener", "start"),
        ("zatrzymaj kontener", "stop"), ("stop container", "stop"),
        ("zatrzymaj container", "stop"), ("stop kontener", "stop"),
        ("uruchom zatrzymany kontener", "start"),
        ("usuń kontener", "remove"), ("remove container", "remove"), ("delete container", "remove"),
        ("usun kontener", "remove"), ("remove kontener", "remove"), ("delete kontener", "remove"),
        ("wykonaj komendę w kontenerze", "exec"), ("wykonaj polecenie w kontenerze", "exec"),
        ("exec in container", "exec"), ("wejdź do kontenera", "exec"), ("shell kontenera", "exec"),
        ("wejdź do container", "exec"), ("shell container", "exec"),
        ("pokaż logi kontenera", "logs"), ("container logs", "logs"),
        ("pokaż logi container", "logs"), ("logi kontenera", "logs"), ("container logs", "logs"),
        ("pobierz obraz", "pull"), ("pull image", "pull"), ("ściągnij obraz", "pull"),
        ("pobierz image", "pull"), ("sciagnij image", "pull"), ("pull obraz", "pull"),
        ("wypchnij obraz", "push"), ("wyślij obraz", "push"), ("push image", "push"),
        ("wypchnij image", "push"), ("push obraz", "push"),
        ("opublikuj obraz", "push"), ("wypchnij", "push"),
        ("zbuduj obraz", "build"), ("build image", "build"),
        ("zbuduj image", "build"), ("build obraz", "build"), ("stwórz obraz", "build"),
        ("list containers", "list"), ("pokaż kontenery", "list"),
        ("kontenery docker", "list"), ("docker containers", "list"),
        ("kontener", "list"), ("container", "list"),
    ]
    for kw, intent in _DOCKER_CONTAINER_ACTIONS:
        if kw in text_lower:
            return FastPathHit(domain="docker", intent=intent, confidence=0.88)

    # Kubernetes fast-path — explicit k8s terms (ordered: specific first)
    _K8S_TERMS = [
        ("kubectl ", "get"), ("kubernetes", "get"), ("k8s", "get"),
        ("opisz deployment", "describe"), ("opisz pod", "describe"),
        ("describe deployment", "describe"), ("describe pod", "describe"),
        ("skaluj deployment", "scale"), ("scale deployment", "scale"),
        ("skaluj do", "scale"), ("scale to", "scale"),
        ("stwórz serwis", "create_service"), ("create service", "create_service"),
        ("utwórz serwis", "create_service"),
        ("stwórz configmap", "create_configmap"), ("create configmap", "create_configmap"),
        ("utwórz configmap", "create_configmap"),
        ("stwórz secret", "create_secret"), ("create secret", "create_secret"),
        ("utwórz secret", "create_secret"),
        ("stwórz ingress", "create_ingress"), ("create ingress", "create_ingress"),
        ("utwórz ingress", "create_ingress"),
        ("stwórz deployment", "create"), ("create deployment", "create"),
        ("utwórz deployment", "create"), ("stwórz zasób", "create"),
        ("utwórz namespace", "create"), ("create namespace", "create"),
        ("pokaż logi poda", "logs"), ("pod logs", "logs"),
        ("pody w klastrze", "get"), ("pods in cluster", "get"),
        ("pokaż pody", "get"), ("show pods", "get"), ("get pods", "get"),
        (" pods", "get"), ("pod ", "get"), (" pod ", "get"),
        ("deployment", "get"), ("namespace", "get"),
        ("klaster", "get"), ("cluster", "get"),
        ("ingress", "get"), ("configmap", "get"), ("secret", "get"),
        ("service mesh", "get"), ("helm ", "get"),
    ]
    for kw, intent in _K8S_TERMS:
        if kw in text_lower:
            # For namespace detection, extract namespace value into entities
            if intent == "get" and "namespace" in text_lower:
                import re as _re
                ns_match = _re.search(r'namespace\s+(\S+)', text_lower)
                entities = {"namespace": ns_match.group(1)} if ns_match else {}
                return FastPathHit(domain="kubernetes", intent=intent, confidence=0.9, entities=entities)
            # For scale operations, extract replica count
            elif intent == "scale" and ("replik" in text_lower or "replica" in text_lower):
                import re as _re
                replica_match = _re.search(r'(\d+)\s+(?:replik|repliki|replicas)', text_lower)
                if replica_match:
                    entities = {"replicas": replica_match.group(1)}
                    return FastPathHit(domain="kubernetes", intent=intent, confidence=0.9, entities=entities)
            return FastPathHit(domain="kubernetes", intent=intent, confidence=0.9)

    # Shell fast-path — file/process/system terms (only when no docker/k8s context)
    # Guard: skip shell matching if browser signals are present
    _browser_context_signals = {"klucz", "key", "api", "token", ".env", "stron", "przegladark", "przeglądark"}
    _has_browser_context = any(s in text_lower for s in _browser_context_signals)

    _SHELL_TERMS = {
        "configuration files": "find", "config files": "find",
        "find files": "find", "find file": "find",
        "search files": "find", "search for files": "find",
        "pliki konfiguracyjne": "find",
        "znajdź pliki": "find", "znajdź plik": "find",
        "zawartość katalogu": "list", "zawartość folderu": "list",
        "directory contents": "list", "folder contents": "list",
        "list files": "list", "list directory": "list",
        "pokaż pliki": "list", "pokaz pliki": "list",
        "lista plików": "list", "lista plikow": "list",
        "show files": "list", "show file": "list",
        "uruchomione procesy": "list_processes", "running processes": "list_processes",
        "pokaż procesy": "list_processes", "show processes": "list_processes",
        "miejsce na dysku": "disk_usage", "disk space": "disk_usage",
        "disk usage": "disk_usage", "wolne miejsce": "disk_usage",
        "sprawdź dysk": "disk_usage",
        "grep ": "search", "szukaj w pliku": "search", "search in file": "search",
        "znajdź słowo": "search", "szukaj w logach": "search",
        "skopiuj plik": "copy", "copy file": "copy", "skopiuj ": "copy",
        "przenieś plik": "move", "move file": "move", "przenieś ": "move",
        "usuń plik": "remove", "delete file": "remove", "usuń stary": "remove",
        "usun plik": "remove", "skasuj plik": "remove", "skasuj": "remove",
        "zmień uprawnienia": "permissions_chmod", "uprawnienia pliku": "permissions_chmod",
        "change permissions": "permissions_chmod", "chmod ": "permissions_chmod",
        "spakuj folder": "compress_tar", "spakuj ": "compress_tar",
        "compress folder": "compress_tar", "skompresuj": "compress_tar",
        "utwórz katalog": "create_dir", "utwórz folder": "create_dir",
        "stwórz katalog": "create_dir", "stwórz folder": "create_dir",
        "create directory": "create_dir", "make directory": "create_dir",
        "mkdir ": "create_dir",
        "zabij proces": "process_kill", "zakończ proces": "process_kill",
        "kill process": "process_kill", "terminate process": "process_kill",
        "kill ": "process_kill",
        "interfejsy sieciowe": "network_interfaces", "network interfaces": "network_interfaces",
        "show network": "network_interfaces", "adresy ip": "network_interfaces",
        "ip addr": "network_interfaces", "ifconfig": "network_interfaces",
    }
    for kw, intent in _SHELL_TERMS.items():
        if kw in text_lower:
            # Skip shell match if browser signals present (e.g. "skopiuj klucz API")
            if _has_browser_context and intent in ("copy", "move", "remove"):
                continue
            entities = {}
            # Extract file patterns for find operations
            if intent == "find" and ("*" in text_lower or ".py" in text_lower or ".txt" in text_lower or ".json" in text_lower):
                import re as _re
                # Look for file patterns like *.py, *.txt, etc.
                file_pattern_match = _re.search(r'(\*\\\?[a-zA-Z0-9]+|\*[a-zA-Z0-9]+)', text_lower)
                if file_pattern_match:
                    entities["pattern"] = file_pattern_match.group(1)
                elif ".py" in text_lower:
                    entities["pattern"] = "*.py"
                elif ".txt" in text_lower:
                    entities["pattern"] = "*.txt"
                elif ".json" in text_lower:
                    entities["pattern"] = "*.json"
            
            # Extract PID for kill operations
            if intent == "process_kill":
                import re as _re
                pid_match = _re.search(r'(?:pid\s*)?(\d{2,})', text_lower)
                if pid_match:
                    entities["pid"] = pid_match.group(1)

            # Extract directory name for mkdir operations
            if intent == "create_dir":
                import re as _re
                dir_match = _re.search(r'(?:katalog|folder|directory)\s+([\w./_-]+)', text_lower)
                if dir_match:
                    entities["directory"] = dir_match.group(1)

            # Extract permissions and file for chmod operations
            if intent == "permissions_chmod":
                import re as _re
                perm_match = _re.search(r'\b(\d{3,4})\b', text_lower)
                if perm_match:
                    entities["permissions"] = perm_match.group(1)
                file_match = _re.search(r'(?:pliku?\s+|of\s+|file\s+)([\w./_-]+)', text_lower)
                if file_match:
                    entities["file"] = file_match.group(1)

            # Extract source for compress/tar operations
            if intent == "compress_tar":
                import re as _re
                src_match = _re.search(r'(?:folder|katalog|directory)\s+([\w./_-]+)', text_lower)
                if src_match:
                    entities["source"] = src_match.group(1)

            return FastPathHit(domain="shell", intent=intent, confidence=0.88, entities=entities)

    # SQL natural language fast-path (after docker/k8s/shell)
    # Ordered list — more specific first to avoid false matches
    _SQL_NL = [
        # DDL — table creation/deletion (highest priority)
        ("stwórz tabelę", "create_table"), ("utwórz tabelę", "create_table"),
        ("create table", "create_table"), ("nowa tabela", "create_table"),
        ("usuń tabelę", "drop_table"), ("skasuj tabelę", "drop_table"),
        ("drop table", "drop_table"), ("zniszcz tabelę", "drop_table"),
        # DML — insert/update/delete
        ("dodaj nowy rekord", "insert"), ("dodaj rekord", "insert"),
        ("add new record", "insert"), ("add record", "insert"),
        ("wstaw rekord", "insert"), ("insert record", "insert"),
        ("zaktualizuj status", "update"), ("zaktualizuj rekord", "update"),
        ("update record", "update"), ("zmień wartość", "update"),
        ("usuń rekord", "delete"), ("delete record", "delete"),
        ("skasuj rekord", "delete"),
        ("usuń stare dane", "delete"), ("usuń dane", "delete"),
        ("delete old data", "delete"), ("remove old data", "delete"),
        # Aggregates
        ("policz liczbę", "aggregate"), ("policz rekordy", "aggregate"),
        ("count(", "aggregate"), ("sum(", "aggregate"), ("avg(", "aggregate"),
        ("zsumuj", "aggregate"), ("count records", "aggregate"),
        # Joins
        ("inner join", "join"), ("left join", "join"), ("right join", "join"),
        ("join tables", "join"), ("połącz tabele", "join"), ("złącz tabele", "join"),
        # Select
        ("from the table", "select"), ("from table", "select"),
        ("z tabeli", "select"), ("wyświetl dane", "select"),
        ("pokaż rekordy", "select"), ("show records", "select"),
        ("all users", "select"), ("all records", "select"),
        ("wszystkich użytkowników", "select"), ("wszystkie rekordy", "select"),
        ("pokaż użytkowników", "select"), ("show users", "select"),
        ("lista użytkowników", "select"), ("list users", "select"),
        ("pokaż dane", "select"), ("show data", "select"),
        ("wyświetl dane", "select"), ("display data", "select"),
        (" tabeli ", "select"), (" table ", "select"),
        # Record counting with numbers
        ("rekordów", "select"), ("rekordow", "select"), ("records", "select"),
        ("wierszy", "select"), ("rows", "select"),
    ]
    for kw, intent in _SQL_NL:
        if kw in text_lower:
            entities = {}
            # Extract table name for common patterns
            if kw in ["z tabeli", "from table", "from the table"]:
                import re as _re
                # Look for table name after the pattern
                table_match = _re.search(rf'{re.escape(kw)}\s+(\w+)', text_lower)
                if table_match:
                    entities["table"] = table_match.group(1)
            elif " tabeli " in text_lower or " table " in text_lower:
                import re as _re
                # Look for table name around "tabeli" or "table"
                table_match = _re.search(r'(\w+)\s+tabeli|tabeli\s+(\w+)|(\w+)\s+table|table\s+(\w+)', text_lower)
                if table_match:
                    # Find the non-None group
                    table_name = next((group for group in table_match.groups() if group), None)
                    if table_name:
                        entities["table"] = table_name
            elif kw in ["pokaż użytkowników", "show users", "lista użytkowników", "list users"]:
                import re as _re
                # Extract table name from user-related patterns
                entities["table"] = "users"
            
            # Extract WHERE conditions for patterns containing "gdzie", "where"
            if "gdzie" in text_lower or "where" in text_lower:
                import re as _re
                # Look for WHERE condition
                where_match = _re.search(r'(?:gdzie|where)\s+([^,.!?]+)', text_lower)
                if where_match:
                    entities["where"] = where_match.group(1).strip()
            
            # Extract LIMIT numbers for record counting patterns
            if kw in ["rekordów", "rekordow", "records", "wierszy", "rows"]:
                import re as _re
                # Look for numbers before the pattern
                limit_match = _re.search(r'(\d+)\s+(?:rekordów|rekordow|records|wierszy|rows)', text_lower)
                if limit_match:
                    entities["limit"] = limit_match.group(1)
            
            return FastPathHit(domain="sql", intent=intent, confidence=0.85, entities=entities)

    # ═══ BROWSER FAST-PATH: Polish browser phrases (before URL detection) ═══
    # These patterns catch multi-step browser commands that would otherwise
    # fall through to general keyword matching and false-match networking_ext
    _BROWSER_PHRASE_PATTERNS = [
        # Opening browser
        (r"otw[oó]rz\s+przegl[aą]dark[eę]", "browser", "open_browser"),
        (r"uruchom\s+przegl[aą]dark[eę]", "browser", "open_browser"),
        (r"w[łl][aą]cz\s+przegl[aą]dark[eę]", "browser", "open_browser"),
        # Navigate to page (critical — "stronę" was false-matching networking_ext/route)
        (r"(?:wejd[zź]|przejd[zź]|id[zź])\s+na\s+stron[eę]", "browser", "navigate"),
        (r"otw[oó]rz\s+stron[eę]", "browser", "navigate"),
        # "otwórz X.ai" / "otwórz X.com" — domain in context of open verb
        (r"(?:otw[oó]rz|wejd[zź]|uruchom).+\.[a-z]{2,}", "browser", "navigate"),
        # New tab / card / multiple tabs
        (r"(?:nowy|otw[oó]rz)\s+tab", "browser", "new_tab"),
        (r"now[aą]\s+kart[eę]", "browser", "new_tab"),
        (r"(?:otw[oó]rz|open)\s+\d+\s+(?:tab|kart)", "browser", "new_tab"),
        # Browser data operations
        (r"(?:wyci[aą]gnij|skopiuj|pobierz).+(?:klucz|key|token|api)", "browser", "extract_data"),
        (r"zapiszs*\s+(?:do|w)\s+\.env", "browser", "save_env"),
        (r"zapi[sś]z?\s+(?:do|w)\s+\.env", "browser", "save_env"),
        (r"(?:wype[lł]nij|uzupe[lł]nij)\s+formul", "browser", "fill_form"),
    ]
    for pattern, domain, intent in _BROWSER_PHRASE_PATTERNS:
        if re.search(pattern, text_lower):
            # Try to extract URL/domain from text
            url_match = re.search(r"\b(https?://[^\s'\"]+)", text_lower)
            domain_in_text = re.search(
                r'\b([a-zA-Z0-9][\w\-]*\.(?:com|org|net|io|ai|dev|pl|app|co|de|uk|eu)(?:/[^\s\'\"]*)?)',
                text_lower,
            )
            entities = {}
            if url_match:
                entities["url"] = normalize_url(url_match.group(1))
            elif domain_in_text:
                entities["url"] = normalize_url(domain_in_text.group(1))
            return FastPathHit(
                domain=domain, intent=intent, confidence=0.92,
                entities=entities, matched_keyword=pattern,
            )

    # Browser complex intents (before generic URL)
    _BROWSER_COMPLEX = [
        ("znajdź formularz i wypełnij", "browser", "explore_and_fill"),
        ("znajdz formularz i wypelnij", "browser", "explore_and_fill"),
        ("znajdź stronę kontaktu i wypełnij", "browser", "explore_and_fill"),
        ("znajdz strone kontaktu i wypelnij", "browser", "explore_and_fill"),
        ("find form and fill", "browser", "explore_and_fill"),
        ("szukaj kontaktu i wypełnij", "browser", "explore_and_fill"),
        ("szukaj kontaktu i wypelnij", "browser", "explore_and_fill"),
        ("znajdź formularz", "browser", "find_form"),
        ("znajdz formularz", "browser", "find_form"),
        ("szukaj formularza", "browser", "find_form"),
        ("find form", "browser", "find_form"),
        ("search form", "browser", "find_form"),
        ("locate form", "browser", "find_form"),
        ("znajdź stronę kontaktu", "browser", "find_form"),
        ("znajdz strone kontaktu", "browser", "find_form"),
        ("szukaj kontaktu", "browser", "find_form"),
        ("znajdź kontakt", "browser", "find_form"),
    ]
    for kw, domain, intent in _BROWSER_COMPLEX:
        if kw in text_lower:
            url_match = re.search(r"\b(https?://[^\s'\"]+)", text_lower)
            entities = {"url": normalize_url(url_match.group(1))} if url_match else {}
            return FastPathHit(domain=domain, intent=intent, confidence=0.95, entities=entities)

    # 1) Full explicit URLs
    url_match = re.search(r"\b(https?://[^\s'\"]+)", text_lower)
    if url_match:
        return FastPathHit(
            domain="browser",
            intent="navigate",
            confidence=0.95,
            entities={"url": normalize_url(url_match.group(1))},
        )

    # 2) www.* URLs
    www_match = re.search(r"\b(www\.[^\s'\"]+)", text_lower)
    if www_match:
        return FastPathHit(
            domain="browser",
            intent="navigate",
            confidence=0.92,
            entities={"url": normalize_url(www_match.group(1))},
        )

    # 3) Bare domains (optionally with a path)
    domain_match = re.search(
        r"\b([a-zA-Z0-9][\w\-]*\.(?:com|org|net|io|ai|dev|pl|app|de|uk|eu|gov|edu|tv|co)(?:/[^\s'\"]*)?)\b",
        text_lower,
    )
    if domain_match:
        return FastPathHit(
            domain="browser",
            intent="navigate",
            confidence=0.9,
            entities={"url": normalize_url(domain_match.group(1))},
        )

    # Browser keywords
    browser_keywords = patterns.fast_path_browser_keywords
    if any(kw in text_lower for kw in browser_keywords):
        return FastPathHit(
            domain="browser",
            intent="web_action",
            confidence=0.8,
        )

    # Search keywords
    search_keywords = patterns.fast_path_search_keywords
    if any(kw in text_lower for kw in search_keywords):
        return FastPathHit(
            domain="shell",
            intent="search_web",
            confidence=0.8,
        )

def fast_path_detect(
    text_lower: str,
    patterns: KeywordPatterns,
    *,
    domain_rules: bool = True,
) -> Optional[FastPathHit]:
    text_normalized = " ".join(text_lower.split())
    if hit := match_explicit_overrides(patterns.explicit_overrides, text_normalized):
        return hit
    if hit := match_exact_commands(text_lower):
        return hit
    if not domain_rules:
        return None
    return run_domain_fast_path_after_exact(text_lower, patterns)
