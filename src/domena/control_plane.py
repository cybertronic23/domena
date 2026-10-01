"""Versioned control-plane to data-plane job exchange contracts."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping
from urllib.parse import parse_qsl, urlsplit

from .contract import JSONValue

CONTROL_JOB_SCHEMA_VERSION = "domena.control-job/v0.1"

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SENSITIVE_NAMES = frozenset(
    {
        "access_key",
        "access_key_id",
        "api_key",
        "authorization",
        "bearer",
        "credential",
        "credentials",
        "password",
        "secret",
        "secret_access_key",
        "secret_key",
        "token",
    }
)


class ControlJobStatus(StrEnum):
    """Authoritative product lifecycle state, distinct from terminal data-plane evidence."""

    QUEUED = "queued"
    LEASED = "leased"
    RUNNING = "running"
    CANCELLING = "cancelling"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobTransitionReason(StrEnum):
    LEASE_GRANTED = "lease_granted"
    WORK_STARTED = "work_started"
    WORK_SUCCEEDED = "work_succeeded"
    WORK_FAILED = "work_failed"
    CANCELLATION_REQUESTED = "cancellation_requested"
    CANCELLATION_ACKNOWLEDGED = "cancellation_acknowledged"
    LEASE_EXPIRED = "lease_expired"


_ALLOWED_TRANSITIONS = frozenset(
    {
        (ControlJobStatus.QUEUED, ControlJobStatus.LEASED, JobTransitionReason.LEASE_GRANTED),
        (
            ControlJobStatus.QUEUED,
            ControlJobStatus.CANCELLED,
            JobTransitionReason.CANCELLATION_REQUESTED,
        ),
        (ControlJobStatus.LEASED, ControlJobStatus.RUNNING, JobTransitionReason.WORK_STARTED),
        (ControlJobStatus.LEASED, ControlJobStatus.QUEUED, JobTransitionReason.LEASE_EXPIRED),
        (
            ControlJobStatus.LEASED,
            ControlJobStatus.CANCELLING,
            JobTransitionReason.CANCELLATION_REQUESTED,
        ),
        (
            ControlJobStatus.RUNNING,
            ControlJobStatus.SUCCEEDED,
            JobTransitionReason.WORK_SUCCEEDED,
        ),
        (ControlJobStatus.RUNNING, ControlJobStatus.FAILED, JobTransitionReason.WORK_FAILED),
        (
            ControlJobStatus.RUNNING,
            ControlJobStatus.CANCELLING,
            JobTransitionReason.CANCELLATION_REQUESTED,
        ),
        (
            ControlJobStatus.CANCELLING,
            ControlJobStatus.CANCELLED,
            JobTransitionReason.CANCELLATION_ACKNOWLEDGED,
        ),
        (
            ControlJobStatus.CANCELLING,
            ControlJobStatus.FAILED,
            JobTransitionReason.WORK_FAILED,
        ),
    }
)


def _parse_aware_time(name: str, value: str) -> datetime:
    _nonempty(name, value)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone offset")
    return parsed


@dataclass(frozen=True, slots=True)
class JobAttemptIdentity:
    """Immutable identity of one execution attempt for a stable product job."""

    job_id: str
    attempt_id: str
    attempt_number: int

    def __post_init__(self) -> None:
        _nonempty("job_id", self.job_id)
        _nonempty("attempt_id", self.attempt_id)
        if isinstance(self.attempt_number, bool) or not isinstance(self.attempt_number, int):
            raise ValueError("attempt_number must be a positive integer")
        if self.attempt_number < 1:
            raise ValueError("attempt_number must be a positive integer")


@dataclass(frozen=True, slots=True)
class WorkerLease:
    """Bounded authorization for one worker to execute one immutable attempt."""

    attempt: JobAttemptIdentity
    lease_id: str
    worker_id: str
    leased_at: str
    expires_at: str

    def __post_init__(self) -> None:
        _nonempty("lease_id", self.lease_id)
        _nonempty("worker_id", self.worker_id)
        leased_at = _parse_aware_time("leased_at", self.leased_at)
        expires_at = _parse_aware_time("expires_at", self.expires_at)
        if expires_at <= leased_at:
            raise ValueError("expires_at must be later than leased_at")


@dataclass(frozen=True, slots=True)
class JobTransition:
    """Auditable evidence for one accepted product job state transition."""

    job_id: str
    from_status: ControlJobStatus
    to_status: ControlJobStatus
    reason: JobTransitionReason
    actor_id: str
    occurred_at: str
    correlation_id: str
    attempt_id: str | None = None

    def __post_init__(self) -> None:
        _nonempty("job_id", self.job_id)
        _nonempty("actor_id", self.actor_id)
        _nonempty("correlation_id", self.correlation_id)
        _parse_aware_time("occurred_at", self.occurred_at)
        if (self.from_status, self.to_status, self.reason) not in _ALLOWED_TRANSITIONS:
            raise ValueError(
                "invalid job transition: "
                f"{self.from_status.value} -> {self.to_status.value} ({self.reason.value})"
            )
        attempt_required = self.from_status in {
            ControlJobStatus.LEASED,
            ControlJobStatus.RUNNING,
            ControlJobStatus.CANCELLING,
        } or self.to_status in {
            ControlJobStatus.LEASED,
            ControlJobStatus.RUNNING,
            ControlJobStatus.CANCELLING,
            ControlJobStatus.SUCCEEDED,
            ControlJobStatus.FAILED,
        }
        if attempt_required:
            _nonempty("attempt_id", self.attempt_id)
        elif self.attempt_id is not None:
            raise ValueError("queued cancellation must not claim an execution attempt")


def is_allowed_job_transition(
    from_status: ControlJobStatus,
    to_status: ControlJobStatus,
    reason: JobTransitionReason,
) -> bool:
    """Return whether the lifecycle accepts the exact transition and reason."""

    return (from_status, to_status, reason) in _ALLOWED_TRANSITIONS


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _fingerprint(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _nonempty(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _normalized_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")


def _validate_uri(name: str, value: str) -> None:
    _nonempty(name, value)
    parsed = urlsplit(value)
    if parsed.username is not None or parsed.password is not None:
        raise ValueError(f"{name} must not contain embedded credentials")
    for key, _ in parse_qsl(parsed.query, keep_blank_values=True):
        if _normalized_name(key) in _SENSITIVE_NAMES:
            raise ValueError(f"{name} must not contain credential query parameters")


def _freeze_json(value: JSONValue, path: str) -> JSONValue:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError(f"{path} must contain finite JSON numbers")
        return value
    if isinstance(value, list) or isinstance(value, tuple):
        return tuple(_freeze_json(item, f"{path}[{index}]") for index, item in enumerate(value))  # type: ignore[return-value]
    if isinstance(value, Mapping):
        frozen: dict[str, JSONValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path} keys must be strings")
            if _normalized_name(key) in _SENSITIVE_NAMES:
                raise ValueError(
                    f"{path}.{key} looks like embedded credential material; "
                    "use secret_references instead"
                )
            frozen[key] = _freeze_json(item, f"{path}.{key}")
        return MappingProxyType(frozen)  # type: ignore[return-value]
    raise TypeError(f"{path} must contain only JSON-compatible values")


def _thaw_json(value: JSONValue) -> JSONValue:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class JobInputReference:
    """A non-secret reference to one immutable or registered job input."""

    reference_id: str
    kind: str
    uri: str
    fingerprint: str | None = None

    def __post_init__(self) -> None:
        _nonempty("reference_id", self.reference_id)
        _nonempty("kind", self.kind)
        _validate_uri("input reference uri", self.uri)
        if self.fingerprint is not None and not _SHA256.fullmatch(self.fingerprint):
            raise ValueError("input reference fingerprint must be a lower-case SHA-256 digest")


@dataclass(frozen=True, slots=True)
class JobOutputTarget:
    """A non-secret target selected by the control plane for job output."""

    kind: str
    uri: str

    def __post_init__(self) -> None:
        _nonempty("output target kind", self.kind)
        _validate_uri("output target uri", self.uri)


@dataclass(frozen=True, slots=True)
class DataJobSpec:
    """Immutable v0.1 envelope leased by the Go control plane to a Python worker."""

    job_id: str
    workspace_id: str
    project_id: str
    job_kind: str
    input_references: tuple[JobInputReference, ...]
    configuration: Mapping[str, JSONValue]
    requested_engine: str
    requested_runtime: str
    output_target: JobOutputTarget
    attempt_number: int
    idempotency_key: str
    secret_references: tuple[str, ...] = ()
    schema_version: str = CONTROL_JOB_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != CONTROL_JOB_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {CONTROL_JOB_SCHEMA_VERSION!r}")
        for name in (
            "job_id",
            "workspace_id",
            "project_id",
            "job_kind",
            "requested_engine",
            "requested_runtime",
            "idempotency_key",
        ):
            _nonempty(name, getattr(self, name))
        if not self.input_references:
            raise ValueError("input_references must not be empty")
        if isinstance(self.attempt_number, bool) or self.attempt_number < 1:
            raise ValueError("attempt_number must be a positive integer")
        if len(set(self.secret_references)) != len(self.secret_references):
            raise ValueError("secret_references must be unique")
        for reference in self.secret_references:
            _nonempty("secret reference", reference)
            if "://" in reference or "=" in reference:
                raise ValueError("secret references must be opaque identifiers, not credentials")
        configuration = _freeze_json(dict(self.configuration), "configuration")
        assert isinstance(configuration, Mapping)
        object.__setattr__(self, "configuration", configuration)

    @property
    def request_fingerprint(self) -> str:
        """Fingerprint the idempotent command payload, excluding execution identity."""

        return _fingerprint(_request_data(self))


def _input_data(value: JobInputReference) -> dict[str, object]:
    return {
        "reference_id": value.reference_id,
        "kind": value.kind,
        "uri": value.uri,
        "fingerprint": value.fingerprint,
    }


def _output_data(value: JobOutputTarget) -> dict[str, str]:
    return {"kind": value.kind, "uri": value.uri}


def _request_data(spec: DataJobSpec) -> dict[str, object]:
    return {
        "schema_version": spec.schema_version,
        "workspace_id": spec.workspace_id,
        "project_id": spec.project_id,
        "job_kind": spec.job_kind,
        "input_references": [_input_data(value) for value in spec.input_references],
        "configuration": _thaw_json(spec.configuration),
        "requested_engine": spec.requested_engine,
        "requested_runtime": spec.requested_runtime,
        "output_target": _output_data(spec.output_target),
        "secret_references": list(spec.secret_references),
    }


def data_job_to_dict(spec: DataJobSpec) -> dict[str, object]:
    """Return the complete wire representation of a data-job specification."""

    return {
        **_request_data(spec),
        "job_id": spec.job_id,
        "attempt_number": spec.attempt_number,
        "idempotency_key": spec.idempotency_key,
    }


def dumps_data_job(spec: DataJobSpec) -> str:
    return _canonical_json(data_job_to_dict(spec))


def loads_data_job(payload: str | bytes) -> DataJobSpec:
    try:
        raw = json.loads(payload)
        if not isinstance(raw, dict):
            raise ValueError("job specification must be an object")
        input_values = raw["input_references"]
        output_value = raw["output_target"]
        if not isinstance(input_values, list):
            raise ValueError("input_references must be an array")
        if not isinstance(output_value, dict):
            raise ValueError("output_target must be an object")
        return DataJobSpec(
            schema_version=raw["schema_version"],
            job_id=raw["job_id"],
            workspace_id=raw["workspace_id"],
            project_id=raw["project_id"],
            job_kind=raw["job_kind"],
            input_references=tuple(JobInputReference(**value) for value in input_values),
            configuration=raw["configuration"],
            requested_engine=raw["requested_engine"],
            requested_runtime=raw["requested_runtime"],
            output_target=JobOutputTarget(**output_value),
            attempt_number=raw["attempt_number"],
            idempotency_key=raw["idempotency_key"],
            secret_references=tuple(raw.get("secret_references", [])),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid data job specification: {exc}") from exc
