import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from domena import (
    Construction,
    DatasetManifest,
    DatasetMember,
    EvidenceReference,
    SourceNamespace,
    dumps_manifest,
    fingerprint_episode,
    fingerprint_manifest,
    inspect_manifest,
    loads_manifest,
    read_episode,
    resolve_local_member,
    validate_manifest,
    write_episode,
)


FIXTURES = Path(__file__).parent / "fixtures" / "m1a-episodes"


class DatasetManifestTests(unittest.TestCase):
    def make_manifest(self) -> DatasetManifest:
        episode = read_episode(FIXTURES / "mock-pick-001.json")
        member = DatasetMember(
            source_namespace=SourceNamespace(1, "domena.local.mock"),
            episode_id=episode.episode_id,
            episode_fingerprint=fingerprint_episode(episode),
            locator="episodes/mock-pick-001.json",
            split="train",
            evidence=(EvidenceReference("quality-report", "qa-001"),),
        )
        manifest = DatasetManifest(
            dataset_name="mock-manipulation",
            release_id="mock-manipulation-v1",
            members=(member,),
            construction=Construction("domena.tests", "0.1", selection_rationale="curated fixture", created_at="2026-09-30T00:00:00Z"),
            aggregate_member_count=1,
        )
        return replace(manifest, release_fingerprint=fingerprint_manifest(manifest))

    def test_canonical_episode_fingerprint_is_stable(self) -> None:
        episode = read_episode(FIXTURES / "mock-pick-001.json")
        self.assertEqual(fingerprint_episode(episode), fingerprint_episode(episode))
        self.assertEqual(len(fingerprint_episode(episode)), 64)

    def test_manifest_round_trip_and_inspection(self) -> None:
        manifest = self.make_manifest()
        restored = loads_manifest(dumps_manifest(manifest))
        inspection = inspect_manifest(restored)
        self.assertEqual(restored, manifest)
        self.assertEqual(inspection.member_count, 1)
        self.assertEqual(inspection.splits, ("train",))

    def test_release_fingerprint_ignores_volatile_construction_metadata(self) -> None:
        original = self.make_manifest()
        changed = replace(original, construction=replace(original.construction, created_at="2030-01-01T00:00:00Z", selection_rationale="new notes"))
        self.assertEqual(fingerprint_manifest(original), fingerprint_manifest(changed))

    def test_duplicate_composite_identity_and_namespace_conflict_are_rejected(self) -> None:
        manifest = self.make_manifest()
        duplicate = replace(manifest.members[0], source_namespace=SourceNamespace(1, "renamed"))
        invalid = replace(manifest, members=(manifest.members[0], duplicate), release_fingerprint=None, aggregate_member_count=2)
        codes = {issue.code for issue in validate_manifest(invalid).issues}
        self.assertTrue({"duplicate_member", "namespace_conflict"} <= codes)

    def test_local_resolution_verifies_episode_identity_and_fingerprint(self) -> None:
        manifest = self.make_manifest()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            episode_dir = root / "episodes"
            episode_dir.mkdir()
            write_episode(read_episode(FIXTURES / "mock-pick-001.json"), episode_dir / "mock-pick-001.json")
            self.assertEqual(resolve_local_member(root, manifest.members[0]).episode_id, "mock-pick-001")
            bad = replace(manifest.members[0], episode_fingerprint="0" * 64)
            with self.assertRaises(ValueError):
                resolve_local_member(root, bad)

    def test_external_locator_remains_unresolved(self) -> None:
        manifest = self.make_manifest()
        external = replace(manifest.members[0], locator="s3://private/episode.json")
        self.assertIsNone(resolve_local_member(FIXTURES, external))


if __name__ == "__main__":
    unittest.main()
