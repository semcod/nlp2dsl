# Kontrola dostępu i zasoby (`nlp2dsl.yaml`)

## Plik konfiguracyjny

| Plik | Opis |
|------|------|
| `nlp2dsl.yaml` | Główna konfiguracja (w repo) |
| `nlp2dsl.local.yaml` | Lokalne nadpisania (opcjonalnie) |
| `NLP2DSL_CONFIG` | Ścieżka do YAML |

Docker montuje `nlp2dsl.yaml` do `/app/nlp2dsl.yaml`.

## Struktura

```yaml
resource_areas:    # obszary + URI patterns + akcje DSL
agents:            # grants per agent (allow/deny/approval)
label_groups:      # grupy etykiet → area_ids
native_routing:    # intencje obsługiwane przed rules/LLM
integrations:      # włączone pluginy (mullm, …)
access_control:    # deny_by_default, allowed_uri_schemes
```

## Obszar zasobów

Każdy obszar ma:
- `id` — np. `mullm:rag`, `email:inbox`
- `uri_patterns` — `mullm://**`, `https://mail.example.com/**`
- `labels` — do grup i polityk
- `actions` — definicje akcji DSL (aliasy, category, permission_action)

## Agenci i uprawnienia

```yaml
agents:
  files_agent:
    grants:
      - resource_area: mullm:rag
        actions: [list, read]
        effect: allow
      - uri_pattern: "mullm://ticket/**"
        actions: [write]
        effect: approval
```

`effect`: `allow` | `deny` | `approval`

Nagłówek HTTP: `X-NLP2DSL-Agent: files_agent`  
Env: `NLP2DSL_AGENT_ID=shell_agent`

## API

| Endpoint | Opis |
|----------|------|
| `GET /nlp/access/config` | Podgląd załadowanej konfiguracji |
| `GET /nlp/access/check?agent_id=&action=` | Decyzja ACL |
| `POST /nlp/access/reload` | Przeładuj YAML |

## Native routing

`native_routing` + aliasy akcji z YAML — **przed** parserem rules/LLM.

Np. `lista plikow` → `mullm_list_files` bez komunikatu „Nie rozpoznałem intencji”.

Mullm `conductor` może nadal mieć własny fast-path; nlp2dsl sam obsługuje to samo przy bezpośrednim wywołaniu chat API.

## Dodanie nowego obszaru (np. Gmail)

1. Wpis w `resource_areas` z `uri_patterns` i `connector: email`
2. Akcje w `actions` (opcjonalnie)
3. Grants w `agents` dla `mail_agent`
4. `POST /nlp/access/reload`
