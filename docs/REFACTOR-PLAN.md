# Plan refaktoryzacji nlp2dsl (integracja Mullm i rozszerzalność)

## Diagnoza (stan obecny)

| Problem | Skutek |
|---------|--------|
| **4 kopie rejestru akcji** (`registry.py`, `backend/workflow.py`, `worker.py`, runtime `system_executor`) | Nowa akcja = 3–4 pliki, dryf |
| **Chat tylko `parse_rules`** | Słabe rozpoznanie vs `/nlp/to-dsl` (auto/LLM) |
| **Wykonanie binarne** system → lokalnie, reszta → worker | Brak miejsca na Mullm / zewnętrzne backendy |
| **`main.py` ~500 linii** | Trudne testy i pluginy |
| **LLM prompt statyczny** | Nowe akcje (system, code, Mullm) niewidoczne dla LLM |
| **Duplikat schematów** backend ↔ nlp-service | Koszt utrzymania |

## Cel architektury docelowej

```
Tekst → parsing.facade (rules|llm|auto)
     → orchestrator (stan + formularz)
     → mapper → DSL
     → executors.router
           ├─ system (lokalnie)
           ├─ worker (HTTP)
           └─ mullm / inne (HTTP, env)
```

Zasada z README zostaje: **LLM rozumie → registry waliduje → mapper buduje → executor wykonuje**.

---

## Fazy

### Faza 1 — Fundament (zrobione w tym PR)

- [x] `nlp-service/integrations/loader.py` — pluginy z `INTEGRATIONS=mullm`
- [x] `nlp-service/integrations/mullm/registry.py` — akcje Mullm
- [x] `MULLM_ACTIONS` w `registry.py`
- [x] `app/parsing/facade.py` — jeden punkt parsowania
- [x] Orchestrator używa `parse_text(..., mode=os.getenv("NLP_CHAT_MODE","auto"))`
- [x] `NLPEntities` + `FIELD_TYPES` dla pól Mullm
- [x] Backend: przy `uruchom` nie wysyła kroków `mullm` do workera (`execution_backend: mullm`)

### Faza 2 — Porządek modułów (następny sprint)

- Rozbić `nlp-service/app/main.py` na `routers/` (nlp, chat, schema, system, ws)
- `backend/routers/workflow.py` — usunąć lokalny `ACTIONS_REGISTRY`, proxy do `/nlp/actions`
- `worker/registry.py` — walidacja handlerów vs `ACTIONS_REGISTRY` przy starcie
- `parsing/prompt_builder.py` — `SYSTEM_PROMPT` z registry dynamicznie

### Faza 3 — Pakiet wspólny

- `packages/contract/` — `ActionMeta`, schematy DSL/NLP współdzielone z SDK
- Editable install w Dockerfile backend + nlp-service + worker

### Faza 4 — Executor Mullm w nlp2dsl

- `integrations/mullm/client.py` — `POST {MULLM_API}/api/...` (ticket, shell)
- `executors/router.py` w nlp-service dla akcji system+mullm
- Opcjonalnie: backend auto-wykonuje Mullm bez pośrednictwa web BFF

---

## Konwencja akcji zewnętrznych

```python
{
  "mullm_shell_task": {
    "category": "mullm",      # nie "system", nie business-worker
    "required": ["shell_command"],
    "execution": "delegate",  # opcjonalnie w meta
    ...
  }
}
```

Kategorie: `business` | `system` | `mullm` | (przyszłe: `koru`, …)

---

## Zmienne środowiskowe

| Zmienna | Domyślnie | Opis |
|---------|-----------|------|
| `INTEGRATIONS` | `mullm` | Lista pluginów (comma-separated) |
| `NLP_CHAT_MODE` | `auto` | Tryb parsera w rozmowie |
| `MULLM_API_URL` | — | Backend Mullm (Faza 4) |

---

## Sync z repo Mullm

- Źródło prawdy akcji Mullm: `mullm/integrations/nlp2dsl/mullm_registry.py`
- Kopia / sync: `nlp2dsl/nlp-service/integrations/mullm/registry.py`
- Skrypt (opcjonalnie): `scripts/sync-mullm-registry.sh`

Mullm `conductor.py` może zostać cienkim klientem HTTP — logika dialogu w nlp2dsl.
