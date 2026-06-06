"""NLP pipeline endpoints — parse, to-dsl, actions, access."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, HTTPException

from app.conversation.system_map import command_meta, known_action_names
from app.dsl.pipeline import map_to_dsl_with_enrichment, plan_lifecycle_from_nlp
from app.parser_llm import LLM_MODEL, _detect_provider
from app.schemas import DialogResponse, NLPRequest, NLPResult, OrientRequest
from nlp2dsl_sdk.workflow import PlanResult, parse_result_from_nlp

log = logging.getLogger("router.nlp")
router = APIRouter(tags=["nlp"])


@router.post("/nlp/orient")
async def orient_text(req: OrientRequest) -> dict[str, Any]:
    """Orientacja zapytania (file_list / shell / workflow) — bez LLM, przed pełnym parse."""
    from app.routing.orientation import orient_query

    return orient_query(req.text, connector=req.connector).to_dict()


@router.post("/nlp/parse", response_model=NLPResult)
async def parse_text(req: NLPRequest) -> NLPResult:
    """Etap 1: tekst → intent + entities."""
    return await _run_parser(req)


@router.post("/nlp/to-dsl", response_model=DialogResponse)
async def text_to_dsl(req: NLPRequest) -> DialogResponse:
    """Pełny pipeline: tekst → NLP → DSL."""
    nlp_result = await _run_parser(req)

    if nlp_result.intent.intent == "unknown":
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={
                "error": "Nie rozpoznano intencji",
                "text": req.text,
                "hint": "Spróbuj np. 'Wyślij fakturę na 1500 PLN do klient@firma.pl'",
            },
        )

    return await map_to_dsl_with_enrichment(nlp_result)


@router.post("/nlp/plan", response_model=PlanResult)
async def plan_text(req: NLPRequest) -> PlanResult:
    """Lifecycle plan: text → parse → deterministic workflow plan."""
    nlp_result = await _run_parser(req)

    if nlp_result.intent.intent == "unknown":
        parse = parse_result_from_nlp(req.text, req.mode, nlp_result)
        return PlanResult(
            status="blocked",
            parse=parse,
            prompt_user=(
                "Nie rozpoznano intencji. Spróbuj podać akcję, odbiorcę i wymagane dane."
            ),
            source="nlp-service.parser",
            trace=[{"stage": "parse", "status": "blocked", "intent": "unknown"}],
        )

    return await plan_lifecycle_from_nlp(nlp_result, text=req.text, mode=req.mode)


@router.get("/nlp/access/config")
async def access_config() -> dict[str, Any]:
    """Załadowany nlp2dsl.yaml — obszary, agenci, grupy etykiet."""
    from app.access.config import get_access_config

    cfg = get_access_config()
    return {
        "path": cfg.path,
        "version": cfg.version,
        "default_agent": cfg.default_agent,
        "integrations": cfg.enabled_integrations,
        "resource_areas": [
            {
                "id": a.get("id"),
                "title": a.get("title"),
                "uri_patterns": a.get("uri_patterns"),
                "labels": a.get("labels"),
                "actions": list((a.get("actions") or {}).keys()),
            }
            for a in cfg.resource_areas
        ],
        "agents": list(cfg.agents.keys()),
        "label_groups": cfg.label_groups,
        "native_routes": len(cfg.native_routes),
    }


@router.get("/nlp/access/check")
async def access_check(
    agent_id: str,
    action: str,
    resource_area: str | None = None,
    uri: str | None = None,
    permission_action: str = "execute",
) -> dict[str, Any]:
    """Sprawdź uprawnienie agenta (debug / integracja Mullm)."""
    from app.access.policy import authorize_action

    meta = command_meta(action)
    decision = authorize_action(
        agent_id,
        action,
        resource_area=resource_area or meta.get("resource_area"),
        uri=uri,
        permission_action=permission_action or meta.get("permission_action"),
        action_meta=meta,
    )
    return decision.to_dict()


@router.post("/nlp/access/reload")
async def access_reload() -> dict[str, str]:
    """Przeładuj nlp2dsl.yaml bez restartu."""
    from app.access.config import reload_access_config

    cfg = reload_access_config()
    return {"status": "ok", "path": cfg.path or ""}


@router.get("/nlp/actions")
async def list_actions() -> dict[str, Any]:
    """Zwraca rejestr akcji z aliasami (vocabulary DSL) — w zakresie DOQL gdy aktywne."""
    from app.registry import get_action_contracts
    from dsl_contracts import action_catalog_payload

    return action_catalog_payload(get_action_contracts())


@router.get("/health")
async def health() -> dict[str, Any]:
    from app.routing.observability import routing_metrics_snapshot
    from app.store.factory import get_conversation_store

    llm_provider = _detect_provider()
    store = get_conversation_store()
    return {
        "status": "ok",
        "service": "nlp-service",
        "llm_engine": "litellm",
        "llm_provider": llm_provider if llm_provider != "none" else "disabled (rules only)",
        "llm_model": LLM_MODEL if llm_provider != "none" else None,
        "conversation_store": type(store).__name__,
        "active_conversations": await store.count(),
        "actions": sorted(known_action_names()),
        "routing_metrics": routing_metrics_snapshot(),
    }


async def _run_parser(req: NLPRequest) -> NLPResult:
    """Execute parser according to mode."""
    from app.routing.parser.resolve_mode import parse_with_mode

    if req.mode == "llm" and _detect_provider() == "none":
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail="No LLM provider configured. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or OLLAMA_URL.",
        )
    return await parse_with_mode(req.text, req.mode)
