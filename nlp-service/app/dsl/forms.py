"""Schema-driven UI — formularze akcji z DOQL commands[] lub ACTIONS_REGISTRY."""

from app.conversation.system_map import command_meta, known_action_names
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
    "language": {
        "type": "select",
        "label": "Język programowania",
        "options": ["python", "javascript", "java", "go", "rust", "cpp", "php", "ruby"],
    },
    "context": {"type": "string", "label": "Kontekst / wymagania dodatkowe"},
    "include_tests": {"type": "select", "label": "Dołącz testy", "options": ["true", "false"]},
    "chat_id": {"type": "string", "label": "Identyfikator czatu Telegram"},
}


def _field_schema(field_name: str, *, required: bool, default_val: str | None = None) -> FieldSchema:
    fmeta = FIELD_TYPES.get(field_name, {"type": "string", "label": field_name})
    return FieldSchema(
        name=field_name,
        type=fmeta["type"],
        label=fmeta["label"],
        required=required,
        options=fmeta.get("options", []),
        default=default_val,
    )


def get_action_form(action: str) -> ActionFormSchema | None:
    if action not in known_action_names():
        return None

    meta = command_meta(action)
    if not meta:
        return None

    fields: list[FieldSchema] = []
    for field_name in meta.get("required", []):
        fields.append(_field_schema(field_name, required=True))

    optional = meta.get("optional", {})
    if isinstance(optional, dict):
        for field_name, default_val in optional.items():
            default_str = str(default_val) if default_val else None
            fields.append(_field_schema(field_name, required=False, default_val=default_str))

    return ActionFormSchema(
        action=action,
        description=str(meta.get("description", action)),
        fields=fields,
    )
