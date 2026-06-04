"""Backward-compat shim — use app.execution.system."""

from app.execution.system import (
    SYSTEM_EXECUTORS,
    _exec_file_list,
    _exec_file_read,
    _exec_file_write,
    _exec_registry_add,
    _exec_registry_edit,
    _exec_registry_list,
    _exec_settings_get,
    _exec_settings_reset,
    _exec_settings_set,
    _exec_status,
    _is_read_only,
    _validate_file_path,
    execute_system_action,
)

__all__ = [
    "SYSTEM_EXECUTORS",
    "_exec_file_list",
    "_exec_file_read",
    "_exec_file_write",
    "_exec_registry_add",
    "_exec_registry_edit",
    "_exec_registry_list",
    "_exec_settings_get",
    "_exec_settings_reset",
    "_exec_settings_set",
    "_exec_status",
    "_is_read_only",
    "_validate_file_path",
    "execute_system_action",
]
