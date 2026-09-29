"""Deterministic local JSON envelope for supported episode values."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

from .contract import (
    SCHEMA_VERSION,
    Asset,
    AssetReference,
    Episode,
    FrameReference,
    Outcome,
    OutcomeStatus,
    PhysicalContext,
    Step,
    TaskContext,
)
from .validation import validate_episode

_ASSET_REFERENCE_TAG = "$domena_asset"


def dumps_episode(episode: Episode) -> str:
    """Encode a valid episode using stable JSON key ordering."""
    _require_valid(episode)
    return json.dumps(_episode_to_data(episode), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fingerprint_episode(episode: Episode) -> str:
    """Return the SHA-256 of the canonical local Episode JSON envelope."""
    return hashlib.sha256(dumps_episode(episode).encode("utf-8")).hexdigest()


def loads_episode(payload: str | bytes) -> Episode:
    """Decode and validate a Domena v0.1 JSON envelope."""
    try:
        data = json.loads(payload)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("payload is not valid JSON") from exc
    if not isinstance(data, dict):
        raise ValueError("episode envelope must be a JSON object")
    try:
        episode = _episode_from_data(data)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid episode envelope: {exc}") from exc
    _require_valid(episode)
    return episode


def write_episode(episode: Episode, path: str | Path) -> None:
    Path(path).write_text(dumps_episode(episode), encoding="utf-8")


def read_episode(path: str | Path) -> Episode:
    return loads_episode(Path(path).read_text(encoding="utf-8"))


def _require_valid(episode: Episode) -> None:
    result = validate_episode(episode)
    if not result.is_valid:
        description = "; ".join(f"{issue.path}: {issue.message}" for issue in result.issues)
        raise ValueError(f"invalid episode {episode.episode_id!r}: {description}")


def _episode_to_data(episode: Episode) -> dict[str, Any]:
    return {
        "schema_version": episode.schema_version,
        "episode_id": episode.episode_id,
        "task": {"task_id": episode.task.task_id, "success_criteria": episode.task.success_criteria},
        "physical_context": {
            "embodiment_id": episode.physical_context.embodiment_id,
            "environment_id": episode.physical_context.environment_id,
            "clock_domain": episode.physical_context.clock_domain,
            "frames": [{"frame_id": frame.frame_id, "parent_frame_id": frame.parent_frame_id} for frame in episode.physical_context.frames],
            "calibration_asset_ids": list(episode.physical_context.calibration_asset_ids),
        },
        "assets": [
            {"asset_id": asset.asset_id, "uri": asset.uri, "media_type": asset.media_type, "checksum": asset.checksum}
            for asset in episode.assets
        ],
        "steps": [
            {
                "index": step.index,
                "timestamp_ns": step.timestamp_ns,
                "observations": _encode_channel_map(step.observations),
                "actions": _encode_channel_map(step.actions),
                "state": _encode_channel_map(step.state),
                "feedback": _encode_channel_map(step.feedback),
            }
            for step in episode.steps
        ],
        "outcome": {"status": episode.outcome.status.value, "details": episode.outcome.details},
        "provenance": episode.provenance,
        "extensions": episode.extensions,
    }


def _encode_channel_map(channels: dict[str, Any]) -> dict[str, Any]:
    return {key: {_ASSET_REFERENCE_TAG: value.asset_id} if isinstance(value, AssetReference) else value for key, value in channels.items()}


def _episode_from_data(data: dict[str, Any]) -> Episode:
    physical_data = _object(data["physical_context"], "physical_context")
    task_data = _object(data["task"], "task")
    outcome_data = _object(data["outcome"], "outcome")
    frames = tuple(
        FrameReference(frame_id=_object(frame, "frame")["frame_id"], parent_frame_id=_object(frame, "frame").get("parent_frame_id"))
        for frame in _list(physical_data.get("frames", []), "physical_context.frames")
    )
    assets = tuple(
        Asset(
            asset_id=_object(asset, "asset")["asset_id"],
            uri=_object(asset, "asset")["uri"],
            media_type=_object(asset, "asset").get("media_type"),
            checksum=_object(asset, "asset").get("checksum"),
        )
        for asset in _list(data.get("assets", []), "assets")
    )
    steps = tuple(_step_from_data(_object(step, "step")) for step in _list(data.get("steps", []), "steps"))
    return Episode(
        schema_version=data["schema_version"],
        episode_id=data["episode_id"],
        task=TaskContext(task_id=task_data["task_id"], success_criteria=task_data.get("success_criteria", {})),
        physical_context=PhysicalContext(
            embodiment_id=physical_data.get("embodiment_id"),
            environment_id=physical_data.get("environment_id"),
            clock_domain=physical_data.get("clock_domain"),
            frames=frames,
            calibration_asset_ids=tuple(_list(physical_data.get("calibration_asset_ids", []), "calibration_asset_ids")),
        ),
        assets=assets,
        steps=steps,
        outcome=Outcome(status=OutcomeStatus(outcome_data.get("status", "unknown")), details=outcome_data.get("details", {})),
        provenance=data.get("provenance", {}),
        extensions=data.get("extensions", {}),
    )


def _step_from_data(data: dict[str, Any]) -> Step:
    return Step(
        index=data["index"],
        timestamp_ns=data.get("timestamp_ns"),
        observations=_decode_channel_map(data.get("observations", {})),
        actions=_decode_channel_map(data.get("actions", {})),
        state=_decode_channel_map(data.get("state", {})),
        feedback=_decode_channel_map(data.get("feedback", {})),
    )


def _decode_channel_map(data: Any) -> dict[str, Any]:
    values = _object(data, "channels")
    decoded: dict[str, Any] = {}
    for key, value in values.items():
        if isinstance(value, dict) and set(value) == {_ASSET_REFERENCE_TAG}:
            decoded[key] = AssetReference(asset_id=value[_ASSET_REFERENCE_TAG])
        else:
            decoded[key] = value
    return decoded


def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be an array")
    return value
