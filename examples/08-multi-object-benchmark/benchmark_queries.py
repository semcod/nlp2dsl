"""20 zapytań testowych — różne obiekty i akcje MVP."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkQuery:
    id: str
    text: str
    expected_intent: str  # substring match in workflow name or step actions
    expected_actions: tuple[str, ...]
    category: str


BENCHMARK_QUERIES: tuple[BenchmarkQuery, ...] = (
    BenchmarkQuery(
        "q01",
        "Wystaw fakturę na 3200 PLN do dostawca@firma.pl",
        "send_invoice",
        ("send_invoice",),
        "invoice",
    ),
    BenchmarkQuery(
        "q02",
        "Invoice for 890 USD to billing@corp.com",
        "send_invoice",
        ("send_invoice",),
        "invoice",
    ),
    BenchmarkQuery(
        "q03",
        "Wyślij powiadomienie na Slack #devops: deploy produkcji zakończony",
        "notify_slack",
        ("notify_slack",),
        "slack",
    ),
    BenchmarkQuery(
        "q04",
        "Notify Telegram chat -1001234567890: serwer API nie odpowiada",
        "notify_telegram",
        ("notify_telegram",),
        "telegram",
    ),
    BenchmarkQuery(
        "q05",
        "Wyślij na Microsoft Teams kanał general: spotkanie sprint review jutro 10:00",
        "notify_teams",
        ("notify_teams",),
        "teams",
    ),
    BenchmarkQuery(
        "q06",
        "Zaktualizuj lead w CRM: firma ACME, status qualified, owner Jan Kowalski",
        "crm_update",
        ("crm_update",),
        "crm",
    ),
    BenchmarkQuery(
        "q07",
        "Generuj raport marketingowy w CSV",
        "generate_report",
        ("generate_report",),
        "report",
    ),
    BenchmarkQuery(
        "q08",
        "Co tydzień raport HR w formacie xlsx",
        "generate_report",
        ("generate_report",),
        "report",
    ),
    BenchmarkQuery(
        "q09",
        "Wyślij fakturę 1500 PLN do klient@firma.pl i powiadom #billing na Slacku",
        "invoice",
        ("send_invoice", "notify_slack"),
        "composite",
    ),
    BenchmarkQuery(
        "q10",
        "Miesięczny raport finansów PDF i wyślij email do cfo@firma.pl",
        "report",
        ("generate_report", "send_email"),
        "composite",
    ),
    BenchmarkQuery(
        "q11",
        "Napisz w Pythonie funkcję obliczającą medianę listy liczb z testami",
        "generate_code",
        ("generate_code",),
        "code",
    ),
    BenchmarkQuery(
        "q12",
        "Pokaż status systemu i wersję",
        "system_status",
        ("system_status",),
        "system",
    ),
    BenchmarkQuery(
        "q13",
        "Jakie akcje biznesowe są dostępne?",
        "system_registry",
        ("system_registry_list",),
        "system",
    ),
    BenchmarkQuery(
        "q14",
        "Przypomnij dev@firma.pl o code review PR-442",
        "send_email",
        ("send_email",),
        "email",
    ),
    BenchmarkQuery(
        "q15",
        "Powiadom kanał #sales o podpisaniu umowy z klientem Beta Corp",
        "notify_slack",
        ("notify_slack",),
        "slack",
    ),
    BenchmarkQuery(
        "q16",
        "Raport kwartalny sprzedaży CSV i wyślij go na #analytics",
        "report",
        ("generate_report", "notify_slack"),
        "composite",
    ),
    BenchmarkQuery(
        "q17",
        "Dodaj kontakt do CRM typ contact z emailem anna@firma.pl",
        "crm_update",
        ("crm_update",),
        "crm",
    ),
    BenchmarkQuery(
        "q18",
        "Przygotuj raport finansowy PDF na koniec miesiąca",
        "generate_report",
        ("generate_report",),
        "report",
    ),
    BenchmarkQuery(
        "q19",
        "Napisz do hr@firma.pl: wniosek urlopowy został zaakceptowany",
        "send_email",
        ("send_email",),
        "email",
    ),
    BenchmarkQuery(
        "q20",
        "Pełny flow: faktura 12000 PLN do enterprise@corp.com, email do ksiegowosc@firma.pl i Slack #finance",
        "invoice",
        ("send_invoice", "send_email", "notify_slack"),
        "composite",
    ),
)
