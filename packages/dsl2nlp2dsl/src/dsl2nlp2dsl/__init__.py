"""NLP2DSL control DSL — CQRS bus and lifecycle commands."""

from dsl2nlp2dsl.bus import dispatch, execute_dsl, execute_dsl_line
from dsl2nlp2dsl.result import DslResult

__all__ = ["DslResult", "dispatch", "execute_dsl", "execute_dsl_line"]
