"""Structural validation for Domena's public episode contract."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

from .contract import AssetReference, Episode, JSONValue, OutcomeStatus, SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    path: str
    message: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    episode_id: str
    issues: tuple[ValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        return not self.issues


def validate_episode(episode: Episode) -> ValidationResult:
    """Return all generic contract violations without raising on malformed data."""
    issues: list[ValidationIssue] = []
    if episode.schema_version != SCHEMA_VERSION:
        issues.append(_issue("unsupported_schema", "schema_version", f"expected {SCHEMA_VERSION!r}"))
    _nonempty(issues, "episode_id", episode.episode_id)
    _nonempty(issues, "task.task_id", episode.task.task_id)
    _json_object(issues, "task.success_criteria", episode.task.success_criteria)
    _json_object(issues, "outcome.details", episode.outcome.details)
    _json_object(issues, "provenance", episode.provenance)
    if not isinstance(episode.outcome.status, OutcomeStatus):
        issues.append(_issue("invalid_outcome", "outcome.status", "must be an OutcomeStatus"))

    asset_ids: set[str] = set()
    for position, asset in enumerate(episode.assets):
        path = f"assets[{position}]"
        _nonempty(issues, f"{path}.asset_id", asset.asset_id)
        _nonempty(issues, f"{path}.uri", asset.uri)
        if asset.asset_id in asset_ids:
            issues.append(_issue("duplicate_asset", f"{path}.asset_id", "asset_id must be unique"))
        asset_ids.add(asset.asset_id)

    for position, frame in enumerate(episode.physical_context.frames):
        _nonempty(issues, f"physical_context.frames[{position}].frame_id", frame.frame_id)
    for position, asset_id in enumerate(episode.physical_context.calibration_asset_ids):
        if asset_id not in asset_ids:
            issues.append(_issue("unknown_asset", f"physical_context.calibration_asset_ids[{position}]", f"unknown asset {asset_id!r}"))

    previous_timestamp: int | None = None
    for position, step in enumerate(episode.steps):
        path = f"steps[{position}]"
        if step.index != position:
            issues.append(_issue("invalid_step_order", f"{path}.index", f"expected contiguous index {position}"))
        if step.timestamp_ns is not None:
            if isinstance(step.timestamp_ns, bool) or not isinstance(step.timestamp_ns, int):
                issues.append(_issue("invalid_timestamp", f"{path}.timestamp_ns", "must be an integer nanosecond value"))
            elif previous_timestamp is not None and step.timestamp_ns < previous_timestamp:
                issues.append(_issue("decreasing_timestamp", f"{path}.timestamp_ns", "must be non-decreasing"))
            else:
                previous_timestamp = step.timestamp_ns
        for group_name in ("observations", "actions", "state", "feedback"):
            channels = getattr(step, group_name)
            _channels(issues, f"{path}.{group_name}", channels, asset_ids)

    if not isinstance(episode.extensions, Mapping):
        issues.append(_issue("invalid_extensions", "extensions", "must be a mapping"))
        return ValidationResult(episode_id=episode.episode_id, issues=tuple(issues))
    for key, value in episode.extensions.items():
        path = f"extensions.{key}"
        if not isinstance(key, str) or ":" not in key or key.startswith(":") or key.endswith(":"):
            issues.append(_issue("unnamespaced_extension", path, "extension keys must use namespace:name"))
        _json(issues, path, value)
    return ValidationResult(episode_id=episode.episode_id, issues=tuple(issues))


def _channels(issues: list[ValidationIssue], path: str, channels: Any, asset_ids: set[str]) -> None:
    if not isinstance(channels, Mapping):
        issues.append(_issue("invalid_channels", path, "must be a mapping"))
        return
    for key, value in channels.items():
        child_path = f"{path}.{key}"
        if not isinstance(key, str) or not key:
            issues.append(_issue("invalid_channel_name", child_path, "channel names must be non-empty strings"))
        _channel_value(issues, child_path, value, asset_ids)


def _channel_value(issues: list[ValidationIssue], path: str, value: Any, asset_ids: set[str]) -> None:
    if isinstance(value, AssetReference):
        if value.asset_id not in asset_ids:
            issues.append(_issue("unknown_asset", path, f"unknown asset {value.asset_id!r}"))
        return
    _json(issues, path, value)


def _json(issues: list[ValidationIssue], path: str, value: Any) -> None:
    if not _is_json(value):
        issues.append(_issue("non_json_value", path, "must be JSON-compatible or an AssetReference"))


def _json_object(issues: list[ValidationIssue], path: str, value: Any) -> None:
    if not isinstance(value, Mapping):
        issues.append(_issue("invalid_metadata", path, "must be a JSON object"))
        return
    _json(issues, path, dict(value))


def _is_json(value: Any) -> bool:
    if value is None or isinstance(value, (bool, str)):
        return True
    if isinstance(value, int) and not isinstance(value, bool):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_is_json(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _is_json(item) for key, item in value.items())
    return False


def _nonempty(issues: list[ValidationIssue], path: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(_issue("invalid_identifier", path, "must be a non-empty string"))


def _issue(code: str, path: str, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, path=path, message=message)
