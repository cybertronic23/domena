from __future__ import annotations

import json
import unittest
from itertools import product

from domena import (
    CONTROL_JOB_SCHEMA_VERSION,
    ControlJobStatus,
    DataJobSpec,
    JobAttemptIdentity,
    JobInputReference,
    JobOutputTarget,
    JobTransition,
    JobTransitionReason,
    WorkerLease,
    dumps_data_job,
    is_allowed_job_transition,
    loads_data_job,
)


def make_job(**changes: object) -> DataJobSpec:
    values: dict[str, object] = {
        "job_id": "job-001",
        "workspace_id": "workspace-001",
        "project_id": "project-001",
        "job_kind": "materialize_release",
        "input_references": (
            JobInputReference(
                reference_id="release-001",
                kind="dataset_manifest",
                uri="s3://domena-input/releases/release-001.json",
                fingerprint="a" * 64,
            ),
        ),
        "configuration": {"transform": {"id": "domena.identity", "version": "1"}},
        "requested_engine": "ray-data",
        "requested_runtime": "ray",
        "output_target": JobOutputTarget("lance", "s3://domena-output/release-001.lance"),
        "attempt_number": 1,
        "idempotency_key": "import-release-001",
        "secret_references": ("object-store-worker",),
    }
    values.update(changes)
    return DataJobSpec(**values)  # type: ignore[arg-type]


class DataJobSpecTests(unittest.TestCase):
    def test_round_trip_is_canonical_and_preserves_request_fingerprint(self) -> None:
        job = make_job()
        payload = dumps_data_job(job)
        restored = loads_data_job(payload)

        self.assertEqual(restored, job)
        self.assertEqual(restored.request_fingerprint, job.request_fingerprint)
        self.assertEqual(dumps_data_job(restored), payload)
        self.assertEqual(json.loads(payload)["schema_version"], CONTROL_JOB_SCHEMA_VERSION)

    def test_request_fingerprint_excludes_execution_identity(self) -> None:
        first = make_job()
        retry = make_job(job_id="job-999", attempt_number=3, idempotency_key="another-command")

        self.assertEqual(first.request_fingerprint, retry.request_fingerprint)

    def test_request_fingerprint_changes_for_semantic_configuration(self) -> None:
        first = make_job()
        changed = make_job(
            configuration={"transform": {"id": "domena.identity", "version": "2"}}
        )

        self.assertNotEqual(first.request_fingerprint, changed.request_fingerprint)

    def test_nested_configuration_is_immutable(self) -> None:
        configuration = {"transform": {"id": "domena.identity"}, "channels": ["camera"]}
        job = make_job(configuration=configuration)
        configuration["transform"]["id"] = "changed"  # type: ignore[index]
        configuration["channels"].append("imu")  # type: ignore[union-attr]

        self.assertIn('"id":"domena.identity"', dumps_data_job(job))
        with self.assertRaises(TypeError):
            job.configuration["new"] = True  # type: ignore[index]

    def test_embedded_secret_configuration_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "secret_references"):
            make_job(configuration={"storage": {"access_key": "not-allowed"}})

    def test_credential_bearing_uris_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "embedded credentials"):
            JobOutputTarget("lance", "https://user:password@example.test/output")
        with self.assertRaisesRegex(ValueError, "credential query"):
            JobOutputTarget("lance", "https://example.test/output?token=not-allowed")

    def test_secret_references_are_opaque_and_unique(self) -> None:
        with self.assertRaisesRegex(ValueError, "opaque identifiers"):
            make_job(secret_references=("token=not-allowed",))
        with self.assertRaisesRegex(ValueError, "unique"):
            make_job(secret_references=("worker-store", "worker-store"))

    def test_invalid_payload_is_actionable(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid data job specification"):
            loads_data_job('{"schema_version":"wrong"}')


class JobLifecycleTests(unittest.TestCase):
    ALLOWED = {
        ("queued", "leased", "lease_granted"),
        ("queued", "cancelled", "cancellation_requested"),
        ("leased", "running", "work_started"),
        ("leased", "queued", "lease_expired"),
        ("leased", "cancelling", "cancellation_requested"),
        ("running", "succeeded", "work_succeeded"),
        ("running", "failed", "work_failed"),
        ("running", "cancelling", "cancellation_requested"),
        ("cancelling", "cancelled", "cancellation_acknowledged"),
        ("cancelling", "failed", "work_failed"),
    }

    def test_transition_table_is_exhaustive(self) -> None:
        for from_status, to_status, reason in product(
            ControlJobStatus, ControlJobStatus, JobTransitionReason
        ):
            expected = (from_status.value, to_status.value, reason.value) in self.ALLOWED
            self.assertEqual(
                is_allowed_job_transition(from_status, to_status, reason),
                expected,
                (from_status, to_status, reason),
            )

    def test_valid_worker_transition_requires_attempt_and_audit_identity(self) -> None:
        transition = JobTransition(
            job_id="job-001",
            attempt_id="attempt-001",
            from_status=ControlJobStatus.RUNNING,
            to_status=ControlJobStatus.SUCCEEDED,
            reason=JobTransitionReason.WORK_SUCCEEDED,
            actor_id="worker-001",
            occurred_at="2026-10-01T10:00:00+08:00",
            correlation_id="request-001",
        )
        self.assertEqual(transition.to_status, ControlJobStatus.SUCCEEDED)

        with self.assertRaisesRegex(ValueError, "attempt_id"):
            JobTransition(
                job_id="job-001",
                from_status=ControlJobStatus.RUNNING,
                to_status=ControlJobStatus.FAILED,
                reason=JobTransitionReason.WORK_FAILED,
                actor_id="worker-001",
                occurred_at="2026-10-01T10:00:00+08:00",
                correlation_id="request-001",
            )

    def test_queued_cancellation_is_immediate_and_has_no_attempt(self) -> None:
        transition = JobTransition(
            job_id="job-001",
            from_status=ControlJobStatus.QUEUED,
            to_status=ControlJobStatus.CANCELLED,
            reason=JobTransitionReason.CANCELLATION_REQUESTED,
            actor_id="user-001",
            occurred_at="2026-10-01T10:00:00+08:00",
            correlation_id="request-001",
        )
        self.assertIsNone(transition.attempt_id)

    def test_running_cancellation_requires_acknowledgement(self) -> None:
        self.assertTrue(
            is_allowed_job_transition(
                ControlJobStatus.RUNNING,
                ControlJobStatus.CANCELLING,
                JobTransitionReason.CANCELLATION_REQUESTED,
            )
        )
        self.assertFalse(
            is_allowed_job_transition(
                ControlJobStatus.RUNNING,
                ControlJobStatus.CANCELLED,
                JobTransitionReason.CANCELLATION_REQUESTED,
            )
        )

    def test_terminal_states_never_transition(self) -> None:
        for terminal in (
            ControlJobStatus.SUCCEEDED,
            ControlJobStatus.FAILED,
            ControlJobStatus.CANCELLED,
        ):
            for target, reason in product(ControlJobStatus, JobTransitionReason):
                self.assertFalse(is_allowed_job_transition(terminal, target, reason))

    def test_worker_lease_is_bounded_and_attempt_is_positive(self) -> None:
        attempt = JobAttemptIdentity("job-001", "attempt-001", 1)
        lease = WorkerLease(
            attempt=attempt,
            lease_id="lease-001",
            worker_id="worker-001",
            leased_at="2026-10-01T10:00:00+08:00",
            expires_at="2026-10-01T10:05:00+08:00",
        )
        self.assertEqual(lease.attempt, attempt)

        with self.assertRaisesRegex(ValueError, "later"):
            WorkerLease(
                attempt=attempt,
                lease_id="lease-002",
                worker_id="worker-001",
                leased_at="2026-10-01T10:05:00+08:00",
                expires_at="2026-10-01T10:00:00+08:00",
            )

    def test_job_transition_rejects_naive_timestamp_and_wrong_reason(self) -> None:
        with self.assertRaisesRegex(ValueError, "timezone"):
            JobTransition(
                job_id="job-001",
                attempt_id="attempt-001",
                from_status=ControlJobStatus.LEASED,
                to_status=ControlJobStatus.RUNNING,
                reason=JobTransitionReason.WORK_STARTED,
                actor_id="worker-001",
                occurred_at="2026-10-01T10:00:00",
                correlation_id="request-001",
            )
        with self.assertRaisesRegex(ValueError, "invalid job transition"):
            JobTransition(
                job_id="job-001",
                attempt_id="attempt-001",
                from_status=ControlJobStatus.RUNNING,
                to_status=ControlJobStatus.SUCCEEDED,
                reason=JobTransitionReason.WORK_FAILED,
                actor_id="worker-001",
                occurred_at="2026-10-01T10:00:00+08:00",
                correlation_id="request-001",
            )


if __name__ == "__main__":
    unittest.main()
