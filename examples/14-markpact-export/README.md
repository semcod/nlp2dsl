# Przykład 14: Export markpact + pactown

Eksportuje workflow `report_and_email` (jak w przykładzie 04) do warstwy publikacji:

- **markpact** — czytelny README z kontraktami akcji i workflow YAML
- **pactown** — ecosystem manifest spinający platformę nlp2dsl

## Uruchomienie

```bash
# Z katalogu repo (platforma docker compose up)
cd examples/14-markpact-export && python3 main.py
```

## Artefakty

```
.nlp2dsl/generated/
  markpact/
    README.md
    contracts/generate_report.contract.yaml
    contracts/send_email.contract.yaml
    workflows/report_and_email.workflow.yaml
    workflows/report_and_email.dsl.json
  pactown/
    nlp2dsl-platform.pactown.yaml
    services/backend/README.md
    services/nlp-service/README.md
    services/worker/README.md
    services/report-and-email/README.md
```

## Walidacja (opcjonalnie)

```bash
pip install -e ~/github/wronai/markpact ~/github/wronai/pactown

cd .nlp2dsl/generated/pactown
pactown validate nlp2dsl-platform.pactown.yaml
```

Runtime wykonania pozostaje w nlp2dsl (`/workflow/validate`, `/workflow/execute`) — markpact służy do review i testów HTTP.
