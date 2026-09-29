"""Public, source-neutral value objects for an interaction episode."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TypeAlias

SCHEMA_VERSION = "domena.experience/v0.1"

JSONScalar: TypeAlias = None | bool | int | float | str
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]


@dataclass(frozen=True, slots=True)
class Asset:
    """Metadata for externally stored binary or media data."""

    asset_id: str
    uri: str
    media_type: str | None = None
    checksum: str | None = None


@dataclass(frozen=True, slots=True)
class AssetReference:
    """A reference from a channel value to an asset in the episode registry."""

    asset_id: str


ChannelValue: TypeAlias = JSONValue | AssetReference


@dataclass(frozen=True, slots=True)
class FrameReference:
    """A coordinate frame and its optional parent frame."""

    frame_id: str
    parent_frame_id: str | None = None


@dataclass(frozen=True, slots=True)
class TaskContext:
    task_id: str
    success_criteria: dict[str, JSONValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PhysicalContext:
    embodiment_id: str | None = None
    environment_id: str | None = None
    clock_domain: str | None = None
    frames: tuple[FrameReference, ...] = ()
    calibration_asset_ids: tuple[str, ...] = ()


class OutcomeStatus(StrEnum):
    UNKNOWN = "unknown"
    SUCCESS = "success"
    FAILURE = "failure"
    INCOMPLETE = "incomplete"


@dataclass(frozen=True, slots=True)
class Outcome:
    status: OutcomeStatus = OutcomeStatus.UNKNOWN
    details: dict[str, JSONValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Step:
    index: int
    timestamp_ns: int | None = None
    observations: dict[str, ChannelValue] = field(default_factory=dict)
    actions: dict[str, ChannelValue] = field(default_factory=dict)
    state: dict[str, ChannelValue] = field(default_factory=dict)
    feedback: dict[str, ChannelValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Episode:
    """One bounded, source-neutral interaction trajectory."""

    episode_id: str
    task: TaskContext
    steps: tuple[Step, ...] = ()
    outcome: Outcome = field(default_factory=Outcome)
    physical_context: PhysicalContext = field(default_factory=PhysicalContext)
    assets: tuple[Asset, ...] = ()
    provenance: dict[str, JSONValue] = field(default_factory=dict)
    extensions: dict[str, JSONValue] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION
