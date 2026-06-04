"""
Akcje delegowane do Mullm (workspace / orchestrator).

Sync z: mullm/integrations/nlp2dsl/mullm_registry.py
"""

MULLM_ACTIONS: dict[str, dict] = {
    "mullm_shell_task": {
        "description": "Utwórz i uruchom zadanie shell w Mullm",
        "category": "mullm",
        "execution": "delegate",
        "required": ["shell_command"],
        "optional": {"title": "Zadanie Mullm"},
        "aliases": [
            "uruchom zadanie",
            "wykonaj polecenie",
            "zadanie shell",
            "utwórz i uruchom",
            "run ",
            "exec ",
            "shell ",
        ],
        "param_aliases": {
            "polecenie": "shell_command",
            "komenda": "shell_command",
            "tytuł": "title",
            "tytul": "title",
        },
    },
    "mullm_create_ticket": {
        "description": "Utwórz ticket w kolejce Mullm (bez shell)",
        "category": "mullm",
        "execution": "delegate",
        "required": ["title"],
        "optional": {"description": ""},
        "aliases": [
            "utwórz ticket",
            "dodaj ticket",
            "nowe zadanie",
            "ticket mullm",
            "kolejka zadań",
        ],
        "param_aliases": {
            "tytuł": "title",
            "tytul": "title",
            "opis": "description",
        },
    },
    "mullm_list_files": {
        "description": "Pokaż pliki i zasoby w Mullm (RAG + Access Fabric)",
        "category": "mullm",
        "execution": "delegate",
        "required": [],
        "optional": {},
        "aliases": [
            "lista plików mullm",
            "lista plikow mullm",
            "pliki mullm",
            "zasoby mullm",
            "wykaz plików w mullm",
        ],
        "param_aliases": {},
    },
}

ACTIONS = MULLM_ACTIONS
