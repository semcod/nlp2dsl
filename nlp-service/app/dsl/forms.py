"""Schema-driven UI — formularze akcji z ACTIONS_REGISTRY."""

from app.registry import ACTIONS_REGISTRY
from app.schemas import ActionFormSchema, FieldSchema

FIELD_TYPES: dict[str, dict] = {
    "amount": {"type": "number", "label": "Kwota"},
    "currency": {"type": "select", "label": "Waluta", "options": ["PLN", "EUR", "USD", "GBP"]},
    "to": {"type": "email", "label": "Adres e-mail odbiorcy"},
    "subject": {"type": "string", "label": "Temat wiadomości"},
    "message": {"type": "string", "label": "Treść wiadomości"},
    "body": {"type": "string", "label": "Treść"},
    "channel": {"type": "string", "label": "Kanał Slack (np. #general)"},
    "report_type": {
        "type": "select",
        "label": "Typ raportu",
        "options": ["sales", "hr", "finance", "marketing"],
    },
    "format": {"type": "select", "label": "Format", "options": ["pdf", "csv", "xlsx"]},
    "entity": {
        "type": "select",
        "label": "Typ encji CRM",
        "options": ["contact", "client", "lead", "deal"],
    },
    "data": {"type": "string", "label": "Dane (JSON)"},
    "setting_path": {"type": "string", "label": "Ścieżka ustawienia (np. llm.model)"},
    "setting_value": {"type": "string", "label": "Nowa wartość"},
    "section": {
        "type": "select",
        "label": "Sekcja ustawień",
        "options": ["all", "llm", "nlp", "worker", "file_access"],
    },
    "file_path": {"type": "string", "label": "Ścieżka pliku"},
    "content": {"type": "string", "label": "Treść pliku"},
    "directory": {"type": "string", "label": "Katalog"},
    "pattern": {"type": "string", "label": "Wzorzec (np. *.py)"},
    "mode": {"type": "select", "label": "Tryb zapisu", "options": ["write", "append"]},
    "action_name": {"type": "string", "label": "Nazwa akcji"},
    "action_description": {"type": "string", "label": "Opis akcji"},
    "required_fields": {"type": "string", "label": "Wymagane pola (przecinkami)"},
    "aliases": {"type": "string", "label": "Aliasy (przecinkami)"},
    "shell_command": {"type": "string", "label": "Polecenie shell"},
    "description": {"type": "string", "label": "Opis zadania"},
}


def get_action_form(action: str) -> ActionFormSchema | None:
    meta = ACTIONS_REGISTRY.get(action)
    if not meta:
        return None

    fields = []
    for field_name in meta["required"]:
        fmeta = FIELD_TYPES.get(field_name, {"type": "string", "label": field_name})
        fields.append(
            FieldSchema(
                name=field_name,
                type=fmeta["type"],
                label=fmeta["label"],
                required=True,
                options=fmeta.get("options", []),
            )
        )

    for field_name in meta.get("optional", {}):
        fmeta = FIELD_TYPES.get(field_name, {"type": "string", "label": field_name})
        default_val = meta["optional"][field_name]
        fields.append(
            FieldSchema(
                name=field_name,
                type=fmeta["type"],
                label=fmeta["label"],
                required=False,
                options=fmeta.get("options", []),
                default=str(default_val) if default_val else None,
            )
        )

    return ActionFormSchema(
        action=action,
        description=meta["description"],
        fields=fields,
    )
