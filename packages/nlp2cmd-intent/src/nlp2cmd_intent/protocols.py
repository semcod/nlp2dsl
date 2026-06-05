"""Protocols for intent detection plugins."""

from __future__ import annotations

from typing import Protocol

from pact_ir import EntityBag, IntentIR


class IntentDetector(Protocol):
    def detect(self, query: str, *, entities: EntityBag | None = None) -> IntentIR: ...


class EntityExtractor(Protocol):
    def extract(self, query: str) -> EntityBag: ...
