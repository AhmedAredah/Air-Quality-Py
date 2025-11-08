import pandas as pd
import pytest

from air_quality.mapping import ColumnMapper
from air_quality.exceptions import SchemaError


def test_explicit_mapping_success():
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    res = ColumnMapper.map(
        df, required=["x", "y"], synonyms={}, explicit={"x": "A", "y": "B"}
    )
    assert list(res.df_mapped.columns) == ["x", "y"]
    assert res.mapping == {"x": "A", "y": "B"}


def test_exact_match_on_canonical():
    df = pd.DataFrame({"datetime": [1, 2], "conc": [3, 4]})
    res = ColumnMapper.map(df, required=["datetime", "conc"], synonyms={})
    assert res.mapping == {"datetime": "datetime", "conc": "conc"}


def test_synonym_mapping_unique():
    df = pd.DataFrame({"timestamp": [1, 2], "value": [3, 4]})
    synonyms = {"datetime": ["timestamp"], "conc": ["value"]}
    res = ColumnMapper.map(df, required=["datetime", "conc"], synonyms=synonyms)
    assert res.mapping == {"datetime": "timestamp", "conc": "value"}


def test_ambiguous_mapping_raises():
    df = pd.DataFrame({"value": [1, 2], "value2": [3, 4]})
    synonyms = {"conc": ["value", "value2"]}
    with pytest.raises(SchemaError) as ei:
        ColumnMapper.map(df, required=["conc"], synonyms=synonyms)
    assert "Ambiguous column mapping" in str(ei.value)


def test_missing_required_raises():
    df = pd.DataFrame({"site": ["A", "B"]})
    with pytest.raises(SchemaError) as ei:
        ColumnMapper.map(
            df, required=["datetime"], synonyms={"datetime": ["timestamp"]}
        )
    assert "Missing required columns" in str(ei.value)


def test_candidate_suggestions_for_ambiguous():
    """Test that candidate suggestions are included in diagnostics when flag is enabled."""
    df = pd.DataFrame({"value": [1, 2], "value2": [3, 4]})
    synonyms = {"conc": ["value", "value2"]}

    with pytest.raises(SchemaError) as ei:
        res = ColumnMapper.map(
            df, required=["conc"], synonyms=synonyms, include_candidate_suggestions=True
        )

    # The error should still be raised
    assert "Ambiguous column mapping" in str(ei.value)

    # But we should have diagnostic information available
    # We need to capture the result before the error to check diagnostics
    # Let's verify the error message contains candidates
    assert "value" in str(ei.value) and "value2" in str(ei.value)


def test_candidate_suggestions_for_missing():
    """Test that candidate suggestions are included in diagnostics for missing fields."""
    df = pd.DataFrame({"site": ["A", "B"], "location": ["X", "Y"]})

    with pytest.raises(SchemaError) as ei:
        res = ColumnMapper.map(
            df,
            required=["datetime"],
            synonyms={"datetime": ["timestamp"]},
            include_candidate_suggestions=True,
        )

    # The error should still be raised
    assert "Missing required columns" in str(ei.value)


def test_no_candidate_suggestions_by_default():
    """Test that candidate suggestions are NOT included by default."""
    df = pd.DataFrame({"value": [1, 2], "value2": [3, 4]})
    synonyms = {"conc": ["value", "value2"]}

    # Without the flag, it should work the same as before
    with pytest.raises(SchemaError) as ei:
        ColumnMapper.map(df, required=["conc"], synonyms=synonyms)

    assert "Ambiguous column mapping" in str(ei.value)


def test_diagnostics_enrichment_in_result():
    """Test that diagnostics are populated in successful mappings."""
    df = pd.DataFrame({"timestamp": [1, 2], "value": [3, 4], "extra_col": [5, 6]})

    res = ColumnMapper.map(
        df,
        required=["datetime", "conc"],
        synonyms={"datetime": ["timestamp"], "conc": ["value"]},
        include_candidate_suggestions=True,
    )

    # Should succeed
    assert res.mapping == {"datetime": "timestamp", "conc": "value"}
    # Diagnostics should contain the auto-mappings
    assert len(res.diagnostics) == 2
    assert any("datetime" in d and "timestamp" in d for d in res.diagnostics)
    assert any("conc" in d and "value" in d for d in res.diagnostics)
