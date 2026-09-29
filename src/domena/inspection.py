"""Small, source-neutral inspection helpers."""

from __future__ import annotations

from dataclasses import dataclass

from .contract import Episode


@dataclass(frozen=True, slots=True)
class EpisodeInspection:
    episode_id: str
    step_count: int
    timestamp_count: int
    observation_channels: tuple[str, ...]
    action_channels: tuple[str, ...]
    state_channels: tuple[str, ...]
    feedback_channels: tuple[str, ...]
    asset_count: int


def inspect_episode(episode: Episode) -> EpisodeInspection:
    """Summarise generic trajectory shape without interpreting modality values."""
    return EpisodeInspection(
        episode_id=episode.episode_id,
        step_count=len(episode.steps),
        timestamp_count=sum(step.timestamp_ns is not None for step in episode.steps),
        observation_channels=_channels(episode, "observations"),
        action_channels=_channels(episode, "actions"),
        state_channels=_channels(episode, "state"),
        feedback_channels=_channels(episode, "feedback"),
        asset_count=len(episode.assets),
    )


def _channels(episode: Episode, name: str) -> tuple[str, ...]:
    return tuple(sorted({channel for step in episode.steps for channel in getattr(step, name)}))
