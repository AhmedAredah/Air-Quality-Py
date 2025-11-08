import re

from air_quality.provenance import make_provenance
from air_quality import __version__


def test_provenance_deterministic_hash_and_timestamp_format():
    config_a = {"alpha": 1, "beta": 2, "gamma": {"x": 10, "y": 20}}
    # Different insertion order should produce same hash
    config_b = {"gamma": {"y": 20, "x": 10}, "beta": 2, "alpha": 1}

    p1 = make_provenance(
        module_name="row_count", domain="generic", dataset_id="ds-1", config=config_a
    )
    p2 = make_provenance(
        module_name="row_count", domain="generic", dataset_id="ds-1", config=config_b
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
        module_name="row_count",
        domain="generic",
        dataset_id=None,
        config={"a": 1},
        extra={"note": "test"},
    )
    d = p.to_dict()
    assert d["extra"] == {"note": "test"}

    p_no_extra = make_provenance(
        module_name="row_count", domain="generic", dataset_id=None, config={"a": 1}
    )
    assert p_no_extra.extra is None
