"""Local-first dataset manifest contract, validation, and JSON operations."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from .contract import JSONValue, SCHEMA_VERSION
from .serialization import fingerprint_episode, read_episode
from .validation import ValidationIssue

DATASET_MANIFEST_SCHEMA_VERSION = "domena.dataset-manifest/v0.1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SPLITS = frozenset({"train", "validation", "test"})


@dataclass(frozen=True, slots=True)
class SourceNamespace:
    namespace_id: int
    name: str


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    kind: str
    id: str
    uri: str | None = None


@dataclass(frozen=True, slots=True)
class DatasetMember:
    source_namespace: SourceNamespace
    episode_id: str
    episode_fingerprint: str
    locator: str
    split: str | None = None
    evidence: tuple[EvidenceReference, ...] = ()

    @property
    def identity(self) -> tuple[int, str]:
        return (self.source_namespace.namespace_id, self.episode_id)


@dataclass(frozen=True, slots=True)
class Construction:
    tool_id: str
    tool_version: str
    selection_rationale: str | None = None
    recipe_reference: str | None = None
    parent_release_ids: tuple[str, ...] = ()
    created_at: str | None = None
    evidence: tuple[EvidenceReference, ...] = ()


@dataclass(frozen=True, slots=True)
class DatasetManifest:
    dataset_name: str
    release_id: str
    members: tuple[DatasetMember, ...]
    construction: Construction
    experience_schema_versions: tuple[str, ...] = (SCHEMA_VERSION,)
    aggregate_member_count: int | None = None
    release_fingerprint: str | None = None
    extensions: dict[str, JSONValue] = field(default_factory=dict)
    schema_version: str = DATASET_MANIFEST_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class DatasetManifestValidationResult:
    release_id: str
    issues: tuple[ValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        return not self.issues


@dataclass(frozen=True, slots=True)
class DatasetManifestInspection:
    dataset_name: str
    release_id: str
    member_count: int
    namespace_count: int
    splits: tuple[str, ...]
    release_fingerprint: str


def fingerprint_manifest(manifest: DatasetManifest) -> str:
    """Return a deterministic SHA-256 over semantic release content only."""
    semantic = {
        "schema_version": manifest.schema_version,
        "experience_schema_versions": list(manifest.experience_schema_versions),
        "members": [
            {
                "source_namespace_id": member.source_namespace.namespace_id,
                "episode_id": member.episode_id,
                "episode_fingerprint": member.episode_fingerprint,
                "split": member.split,
            }
            for member in manifest.members
        ],
    }
    payload = json.dumps(semantic, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_manifest(manifest: DatasetManifest) -> DatasetManifestValidationResult:
    issues: list[ValidationIssue] = []
    _nonempty(issues, "dataset_name", manifest.dataset_name)
    _nonempty(issues, "release_id", manifest.release_id)
    if manifest.schema_version != DATASET_MANIFEST_SCHEMA_VERSION:
        _issue(issues, "unsupported_schema", "schema_version", f"expected {DATASET_MANIFEST_SCHEMA_VERSION!r}")
    if not manifest.experience_schema_versions or any(version != SCHEMA_VERSION for version in manifest.experience_schema_versions):
        _issue(issues, "unsupported_experience_schema", "experience_schema_versions", f"only {SCHEMA_VERSION!r} is supported")
    _nonempty(issues, "construction.tool_id", manifest.construction.tool_id)
    _nonempty(issues, "construction.tool_version", manifest.construction.tool_version)
    _evidence(issues, "construction.evidence", manifest.construction.evidence)
    namespace_names: dict[int, str] = {}
    identities: set[tuple[int, str]] = set()
    for index, member in enumerate(manifest.members):
        path = f"members[{index}]"
        namespace = member.source_namespace
        if isinstance(namespace.namespace_id, bool) or not isinstance(namespace.namespace_id, int) or namespace.namespace_id <= 0:
            _issue(issues, "invalid_namespace_id", f"{path}.source_namespace.namespace_id", "must be a positive integer")
        _nonempty(issues, f"{path}.source_namespace.name", namespace.name)
        known_name = namespace_names.setdefault(namespace.namespace_id, namespace.name)
        if known_name != namespace.name:
            _issue(issues, "namespace_conflict", f"{path}.source_namespace.name", "same namespace ID must use one name snapshot")
        _nonempty(issues, f"{path}.episode_id", member.episode_id)
        if member.identity in identities:
            _issue(issues, "duplicate_member", f"{path}.episode_id", "source namespace ID and episode ID must be unique together")
        identities.add(member.identity)
        if not isinstance(member.episode_fingerprint, str) or not _SHA256.fullmatch(member.episode_fingerprint):
            _issue(issues, "invalid_fingerprint", f"{path}.episode_fingerprint", "must be a lower-case SHA-256 hex digest")
        _locator(issues, f"{path}.locator", member.locator)
        if member.split is not None and member.split not in _SPLITS:
            _issue(issues, "invalid_split", f"{path}.split", "must be train, validation, or test")
        _evidence(issues, f"{path}.evidence", member.evidence)
    if manifest.aggregate_member_count is not None and manifest.aggregate_member_count != len(manifest.members):
        _issue(issues, "aggregate_mismatch", "aggregate_member_count", "must equal member count")
    if manifest.release_fingerprint is not None:
        if not _SHA256.fullmatch(manifest.release_fingerprint):
            _issue(issues, "invalid_fingerprint", "release_fingerprint", "must be a lower-case SHA-256 hex digest")
        elif manifest.release_fingerprint != fingerprint_manifest(manifest):
            _issue(issues, "release_fingerprint_mismatch", "release_fingerprint", "does not match canonical semantic content")
    if not isinstance(manifest.extensions, Mapping):
        _issue(issues, "invalid_extensions", "extensions", "must be an object")
    else:
        for key, value in manifest.extensions.items():
            if not isinstance(key, str) or ":" not in key or key.startswith(":") or key.endswith(":"):
                _issue(issues, "unnamespaced_extension", f"extensions.{key}", "extension keys must use namespace:name")
            try:
                json.dumps(value, ensure_ascii=False, allow_nan=False)
            except (TypeError, ValueError):
                _issue(issues, "non_json_value", f"extensions.{key}", "must be JSON-compatible")
    return DatasetManifestValidationResult(manifest.release_id, tuple(issues))


def dumps_manifest(manifest: DatasetManifest) -> str:
    _require_valid(manifest)
    return json.dumps(_to_data(manifest), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def loads_manifest(payload: str | bytes) -> DatasetManifest:
    try:
        data = json.loads(payload)
        manifest = _from_data(_object(data, "manifest"))
    except (TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid dataset manifest: {exc}") from exc
    _require_valid(manifest)
    return manifest


def write_manifest(manifest: DatasetManifest, path: str | Path) -> None:
    Path(path).write_text(dumps_manifest(manifest), encoding="utf-8")


def read_manifest(path: str | Path) -> DatasetManifest:
    return loads_manifest(Path(path).read_text(encoding="utf-8"))


def inspect_manifest(manifest: DatasetManifest) -> DatasetManifestInspection:
    return DatasetManifestInspection(
        dataset_name=manifest.dataset_name,
        release_id=manifest.release_id,
        member_count=len(manifest.members),
        namespace_count=len({member.source_namespace.namespace_id for member in manifest.members}),
        splits=tuple(sorted({member.split for member in manifest.members if member.split is not None})),
        release_fingerprint=fingerprint_manifest(manifest),
    )


def resolve_local_member(manifest_directory: str | Path, member: DatasetMember):
    """Read and verify a local-relative M1a episode; external locators remain unresolved."""
    if _is_external_locator(member.locator):
        return None
    root = Path(manifest_directory).resolve()
    candidate = (root / member.locator).resolve()
    if root != candidate and root not in candidate.parents:
        raise ValueError("local member locator escapes manifest directory")
    episode = read_episode(candidate)
    if episode.episode_id != member.episode_id:
        raise ValueError(f"local member episode ID mismatch: expected {member.episode_id!r}")
    if fingerprint_episode(episode) != member.episode_fingerprint:
        raise ValueError("local member episode fingerprint mismatch")
    return episode


def _to_data(manifest: DatasetManifest) -> dict[str, Any]:
    return {
        "schema_version": manifest.schema_version, "dataset_name": manifest.dataset_name, "release_id": manifest.release_id,
        "experience_schema_versions": list(manifest.experience_schema_versions), "aggregate_member_count": manifest.aggregate_member_count,
        "release_fingerprint": manifest.release_fingerprint, "extensions": manifest.extensions,
        "construction": {**asdict(manifest.construction), "parent_release_ids": list(manifest.construction.parent_release_ids), "evidence": [_evidence_data(item) for item in manifest.construction.evidence]},
        "members": [{"source_namespace": asdict(member.source_namespace), "episode_id": member.episode_id, "episode_fingerprint": member.episode_fingerprint, "locator": member.locator, "split": member.split, "evidence": [_evidence_data(item) for item in member.evidence]} for member in manifest.members],
    }


def _from_data(data: dict[str, Any]) -> DatasetManifest:
    construction = _object(data["construction"], "construction")
    return DatasetManifest(
        schema_version=data["schema_version"], dataset_name=data["dataset_name"], release_id=data["release_id"],
        experience_schema_versions=tuple(data.get("experience_schema_versions", [])), aggregate_member_count=data.get("aggregate_member_count"), release_fingerprint=data.get("release_fingerprint"), extensions=data.get("extensions", {}),
        construction=Construction(tool_id=construction["tool_id"], tool_version=construction["tool_version"], selection_rationale=construction.get("selection_rationale"), recipe_reference=construction.get("recipe_reference"), parent_release_ids=tuple(construction.get("parent_release_ids", [])), created_at=construction.get("created_at"), evidence=tuple(_evidence_from_data(item) for item in construction.get("evidence", []))),
        members=tuple(_member_from_data(item) for item in data.get("members", [])),
    )


def _member_from_data(item: Any) -> DatasetMember:
    data = _object(item, "member"); namespace = _object(data["source_namespace"], "source_namespace")
    return DatasetMember(SourceNamespace(namespace["namespace_id"], namespace["name"]), data["episode_id"], data["episode_fingerprint"], data["locator"], data.get("split"), tuple(_evidence_from_data(entry) for entry in data.get("evidence", [])))


def _evidence_data(value: EvidenceReference) -> dict[str, str | None]: return {"kind": value.kind, "id": value.id, "uri": value.uri}
def _evidence_from_data(value: Any) -> EvidenceReference:
    data = _object(value, "evidence"); return EvidenceReference(data["kind"], data["id"], data.get("uri"))
def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict): raise ValueError(f"{name} must be an object")
    return value
def _require_valid(manifest: DatasetManifest) -> None:
    result = validate_manifest(manifest)
    if not result.is_valid: raise ValueError("invalid dataset manifest: " + "; ".join(f"{issue.path}: {issue.message}" for issue in result.issues))
def _issue(issues: list[ValidationIssue], code: str, path: str, message: str) -> None: issues.append(ValidationIssue(code, path, message))
def _nonempty(issues: list[ValidationIssue], path: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip(): _issue(issues, "invalid_identifier", path, "must be a non-empty string")
def _evidence(issues: list[ValidationIssue], path: str, values: Any) -> None:
    if not isinstance(values, tuple): _issue(issues, "invalid_evidence", path, "must be a tuple"); return
    for index, value in enumerate(values):
        _nonempty(issues, f"{path}[{index}].kind", value.kind); _nonempty(issues, f"{path}[{index}].id", value.id)
def _is_external_locator(locator: str) -> bool: return bool(urlparse(locator).scheme)
def _locator(issues: list[ValidationIssue], path: str, value: Any) -> None:
    _nonempty(issues, path, value)
    if isinstance(value, str) and not _is_external_locator(value) and (Path(value).is_absolute() or ".." in Path(value).parts): _issue(issues, "invalid_local_locator", path, "local locator must be a relative path within manifest directory")
