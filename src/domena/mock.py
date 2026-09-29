"""A source-isolated example, not a simulator or robot adapter."""

from .contract import Asset, AssetReference, Episode, FrameReference, Outcome, OutcomeStatus, PhysicalContext, Step, TaskContext


def make_mock_episode() -> Episode:
    """Return a compact valid episode suitable for local tests and examples."""
    return Episode(
        episode_id="mock-pick-001",
        task=TaskContext(task_id="pick.place", success_criteria={"object_in_target": True}),
        physical_context=PhysicalContext(
            embodiment_id="mock-arm-v1",
            environment_id="mock-workcell-a",
            clock_domain="monotonic_ns",
            frames=(FrameReference(frame_id="base"), FrameReference(frame_id="camera", parent_frame_id="base")),
            calibration_asset_ids=("camera-calibration",),
        ),
        assets=(
            Asset(asset_id="camera-calibration", uri="assets/calibration.json", media_type="application/json"),
            Asset(asset_id="front-image-0", uri="assets/front-000.png", media_type="image/png"),
        ),
        steps=(
            Step(index=0, timestamp_ns=1_000, observations={"front_rgb": AssetReference("front-image-0")}, state={"gripper_open": True}),
            Step(index=1, timestamp_ns=2_000, actions={"gripper": "close"}, feedback={"contact": True}),
        ),
        outcome=Outcome(status=OutcomeStatus.SUCCESS, details={"reason": "object_in_target"}),
        provenance={"source": "mock", "recording_id": "example-001"},
        extensions={"mock:scenario": "pick-place"},
    )
