import re
from enum import Enum

from air_quality.provenance import make_provenance
from air_quality import __version__
from air_quality.module import ModuleDomain


class ProvenanceTestModuleName(Enum):
    """Test module name for provenance tests."""

    ROW_COUNT = "row_count"


class ProvenanceTestConfigKey(Enum):
    """Test config keys for provenance tests."""

    ALPHA = "alpha"
    BETA = "beta"
    GAMMA = "gamma"
    A = "a"


class ProvenanceTestExtraKey(Enum):
    """Test extra metadata keys."""

    NOTE = "note"


def test_provenance_deterministic_hash_and_timestamp_format():
    config_a = {
        ProvenanceTestConfigKey.ALPHA: 1,
        ProvenanceTestConfigKey.BETA: 2,
        ProvenanceTestConfigKey.GAMMA: {"x": 10, "y": 20},
    }
    # Different insertion order should produce same hash
    config_b = {
        ProvenanceTestConfigKey.GAMMA: {"y": 20, "x": 10},
        ProvenanceTestConfigKey.BETA: 2,
        ProvenanceTestConfigKey.ALPHA: 1,
    }

    p1 = make_provenance(
        module=ProvenanceTestModuleName.ROW_COUNT,
        domain=ModuleDomain.QC,
        dataset_id="ds-1",
        config=config_a,
    )
    p2 = make_provenance(
        module=ProvenanceTestModuleName.ROW_COUNT,
        domain=ModuleDomain.QC,
        dataset_id="ds-1",
        config=config_b,
    )

    assert (
        p1.config_hash == p2.config_hash
    ), "Hash not stable across key order variations"

    # ISO timestamp basic pattern (allow fractional seconds and timezone offset)
    iso_pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?[+-]00:00"
    assert re.match(
        iso_pattern, p1.run_timestamp
    ), f"Timestamp not ISO UTC: {p1.run_timestamp}"

    assert p1.software_version == __version__


def test_provenance_extra_metadata_optional():
    p = make_provenance(
        module=ProvenanceTestModuleName.ROW_COUNT,
        domain=ModuleDomain.QC,
        dataset_id=None,
        config={ProvenanceTestConfigKey.A: 1},
        extra={ProvenanceTestExtraKey.NOTE: "test"},
    )
    d = p.to_dict()
    assert d["extra"] == {ProvenanceTestExtraKey.NOTE.value: "test"}

    p_no_extra = make_provenance(
        module=ProvenanceTestModuleName.ROW_COUNT,
        domain=ModuleDomain.QC,
        dataset_id=None,
        config={ProvenanceTestConfigKey.A: 1},
    )
    assert p_no_extra.extra is None
