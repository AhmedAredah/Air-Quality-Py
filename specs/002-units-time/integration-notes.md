# Integration Notes — US6: Multi-Column Unit Metadata

**Feature**: 002-units-time  
**User Story**: US6 Multi-Column Unit Metadata  
**Status**: Phase 8 Implementation Complete ✅  
**Date**: 2025-11-08

## Purpose

Document integration touchpoints for `validate_units_schema()` with `TimeSeriesDataset` and other dataset classes.

## Implementation Status

**Phase 7 Complete** (2025-11-08):
- ✅ T701: `validate_units_schema()` implemented in `src/air_quality/units.py`
- ✅ T702: Column-name error context included in UnitError messages
- ✅ T703: Immutability guarantee (returns new dict)
- ✅ T704: Skip markers removed from 15 tests
- ✅ T705: All 15 tests passing in `tests/test_units_schema_validation.py`
- ✅ T706: Integration notes updated with validated patterns

**Phase 8 Complete** (2025-11-08):
- ✅ T801: TimeSeriesDataset.__init__ accepts column_units parameter
- ✅ T802: validate_units_schema() integrated in dataset construction
- ✅ T803: column_units property added to TimeSeriesDataset
- ✅ T804: Created tests/test_dataset_units_integration.py (12 tests)
- ✅ T805: All 12 integration tests passing
- ✅ T806: Existing 18 dataset tests passing (no regressions)

**Validated Implementation Pattern:**

```python
def validate_units_schema(mapping: Dict[str, Union[Unit, str]]) -> Dict[str, Unit]:
    """Normalize and validate dataset unit metadata.
    
    Constitution Section 3: Metadata normalization at dataset construction.
    Constitution Section 9: UnitError includes offending column name.
    """
    normalized: Dict[str, Unit] = {}
    
    for column_name, unit_value in mapping.items():
        try:
            normalized[column_name] = Unit.parse(unit_value)
        except UnitError as e:
            raise UnitError(
                f"Invalid unit for column '{column_name}': {str(e)}"
            ) from e
    
    return normalized
```

## Integration Overview

The `validate_units_schema()` function serves as the normalization layer between user-provided unit metadata and dataset internal representation.

### Current Dataset Architecture

**Relevant files:**

- `src/air_quality/dataset/base.py` - Base dataset class with metadata infrastructure
- `src/air_quality/dataset/time_series.py` - TimeSeriesDataset implementation

**Metadata structure** (from Constitution Sec 3):

```python
metadata = {
    "dataset_id": str,
    "site_id": str,
    "pollutant": str,
    "time_range": tuple[datetime, datetime],
    "column_units": dict[str, Unit],  # ← Integration point
    # ... other metadata fields
}
```

## Integration Points

### 1. Dataset Construction

**Location**: `TimeSeriesDataset.__init__()` or factory methods

**Behavior**:

- Accept optional `column_units` parameter as `dict[str, Unit | str]`
- Call `validate_units_schema(column_units)` during initialization
- Store normalized result in `metadata["column_units"]`
- If validation fails, raise `UnitError` with column context

**Error handling**:

```python
# Pseudo-code (implementation phase)
try:
    self.metadata["column_units"] = validate_units_schema(column_units)
except UnitError as e:
    # Error message includes offending column name per contract
    raise UnitError(f"Invalid unit metadata: {e}") from e
```

### 2. Property Exposure

**Location**: `TimeSeriesDataset` (or base class)

**Behavior**:

- Add `@property column_units -> dict[str, Unit] | None`
- Return `metadata.get("column_units")` directly
- No validation at property access (already validated at construction)

**Example**:

```python
@property
def column_units(self) -> dict[str, Unit] | None:
    """Column-to-unit mapping if provided at construction."""
    return self.metadata.get("column_units")
```

### 3. Validation Requirements (per contracts/units_api.md)

**Function signature**:

```python
def validate_units_schema(mapping: dict[str, Unit | str]) -> dict[str, Unit]:
    """
    Normalize unit metadata from str|Unit to Unit.
    
    Args:
        mapping: Column name to unit mapping (str or Unit values)
        
    Returns:
        Normalized dict with Unit values only
        
    Raises:
        UnitError: If any value is invalid unit string; 
                   message MUST include offending column name
    """
    raise NotImplementedError("Phase 8 stub")
```

**Contract requirements**:

- ✅ Accepts `dict[str, Unit | str]` (mixed types allowed) - **VALIDATED**
- ✅ Returns `dict[str, Unit]` (normalized) - **VALIDATED**
- ✅ `UnitError` includes column name in message for invalid units - **VALIDATED**
- ✅ Passes through existing `Unit` enum values unchanged - **VALIDATED**
- ✅ Parses string values via `Unit.parse()` - **VALIDATED**
- ✅ Immutability: Returns new dict (does not mutate input) - **VALIDATED**
- ✅ Fail-fast: Raises on first invalid unit encountered - **VALIDATED**

### 4. Validated Test Coverage (15/15 passing)

**Test Results** (Phase 7 - 2025-11-08):
```
tests/test_units_schema_validation.py::TestValidateUnitsSchema::
  ✅ test_validate_units_schema_all_enum_values
  ✅ test_validate_units_schema_all_string_values
  ✅ test_validate_units_schema_mixed_types
  ✅ test_validate_units_schema_invalid_unit_raises_with_column
  ✅ test_validate_units_schema_empty_mapping
  ✅ test_validate_units_schema_single_column
  ✅ test_validate_units_schema_preserves_column_names
  ✅ test_validate_units_schema_case_sensitivity_follows_parse
  ✅ test_validate_units_schema_multiple_invalid_reports_first
  ✅ test_validate_units_schema_returns_new_dict
  ✅ test_validate_units_schema_with_all_supported_units

tests/test_units_schema_validation.py::TestValidateUnitsSchemaIntegration::
  ✅ test_validate_units_schema_dataset_construction_scenario
  ✅ test_validate_units_schema_error_context_for_debugging
  ✅ test_validate_units_schema_typical_air_quality_columns
  ✅ test_validate_units_schema_fail_fast_behavior

All 15 tests passing - 100% coverage on schema validation functionality
```

### 5. Constitution Compliance

**Section 3 (Data & Metadata Standards)**:

- ✓ Unit metadata is optional (`column_units` may be absent)
- ✓ When present, must be normalized and validated - **IMPLEMENTED**
- ✓ Fail-fast on invalid units (don't silently ignore) - **VALIDATED**

**Section 9 (API Design & Error Taxonomy)**:

- ✓ Use existing `UnitError` from `exceptions.py` - **IMPLEMENTED**
- ✓ Error messages include context (column name) - **VALIDATED**
- ✓ Type-annotated with no implicit `Any` - **VALIDATED**

**Section 15 (Constitution - Provenance & Units)**:

- ✓ Centralized validation (no per-dataset custom logic) - **IMPLEMENTED**
- ✓ DRY principle: single source of truth for unit schema validation - **VALIDATED**

## Implementation Dependencies

**Completed Prerequisites**:

- ✅ `Unit.parse()` - Implemented and tested (Phase 2)
- ✅ Unit enum members - All 4 units defined and validated
- ✅ `UnitError` exception - Available from `air_quality.exceptions`

**Next Phase** (Phase 8 - Dataset Integration):

1. ✅ Implement `validate_units_schema()` - **COMPLETE**
2. ✅ Integrate into `TimeSeriesDataset` construction - **COMPLETE**
3. ✅ Add `column_units` property to dataset classes - **COMPLETE**
4. ✅ Update dataset tests to verify unit metadata handling - **COMPLETE**
5. ✅ Verify existing dataset tests still pass - **COMPLETE (18/18)**

**Validated Dataset Integration Pattern**:

```python
class TimeSeriesDataset(BaseDataset):
    """Time series dataset with datetime index validation.
    
    Args:
        column_units: Optional mapping of column names to units.
                      Accepts Unit enums or strings.
                      Validated via validate_units_schema().
    
    Raises:
        UnitError: If invalid unit provided for any column.
    """
    
    def __init__(
        self,
        data: pl.LazyFrame,
        metadata: Optional[Dict[str, Any]] = None,
        mapping: Optional[Dict[str, str]] = None,
        time_index_name: str = "datetime",
        column_units: Optional[Dict[str, Union[Unit, str]]] = None,
    ):
        if metadata is None:
            metadata = {}
        
        # Validate and normalize column units
        if column_units is not None:
            normalized_units = validate_units_schema(column_units)
            metadata["column_units"] = normalized_units
        
        super().__init__(data=data, metadata=metadata, mapping=mapping)
        # ... existing validation logic
    
    @property
    def column_units(self) -> Optional[Dict[str, Unit]]:
        """Column-to-unit mapping if provided at construction."""
        return self.metadata.get("column_units")
    
    @classmethod
    def from_dataframe(
        cls,
        df: pd.DataFrame,
        time_index_name: str = "datetime",
        column_units: Optional[Dict[str, Union[Unit, str]]] = None,
    ) -> "TimeSeriesDataset":
        # ... existing conversion logic
        return cls(
            data=lazy_frame,
            time_index_name=time_index_name,
            column_units=column_units,  # Passed through to __init__
        )
    
    @classmethod
    def from_arrow(
        cls,
        table: pa.Table,
        time_index_name: str = "datetime",
        column_units: Optional[Dict[str, Union[Unit, str]]] = None,
    ) -> "TimeSeriesDataset":
        # ... existing conversion logic
        return cls(
            data=lazy_frame,
            time_index_name=time_index_name,
            column_units=column_units,  # Passed through to __init__
        )
```

## Test Coverage

**Test file**: `tests/test_units_schema_validation.py` (Phase 7 - 15/15 tests passing)

**Phase 7 Scenarios**:
- Valid mapping (all Unit enums) → returns unchanged
- Valid mapping (all strings) → normalizes to Unit enums
- Mixed mapping (Unit + strings) → normalizes strings only
- Invalid unit string → raises UnitError with column name
- Empty mapping → returns empty dict
- Case sensitivity → follows `Unit.parse()` behavior

**Test file**: `tests/test_dataset_units_integration.py` (Phase 8 - 12/12 tests passing)

**Phase 8 Scenarios**:
- ✅ Dataset construction with valid column_units (strings and Units)
- ✅ Property returns normalized mapping
- ✅ Invalid units raise UnitError with column name
- ✅ None/missing column_units handled gracefully
- ✅ Integration with from_dataframe and from_arrow
- ✅ Metadata preservation through dataset operations
- ✅ Multiple columns with different units
- ✅ Empty dict handling
- ✅ Mixed type normalization (Unit enum + string)
- ✅ Immutability: Property returns same object reference

**Regression Tests**: Existing 18 dataset tests passing (no breaking changes)

## Future Extensions

**Potential enhancements** (not in current scope):

- Support for derived units (e.g., ratios, products)
- Unit compatibility checking across related columns
- Automatic unit conversion suggestions in error messages
- Integration with provenance tracking (log unit transformations)

## Notes

- This is a **design-time integration note** only
- No code changes to dataset classes during stub phase
- Implementation occurs after constitution gate approval
- Tests remain skipped until implementation phase
- Integration must respect existing dataset architecture (no breaking changes)

---
**Document Status**: Phase 8 Implementation Complete ✅  
**Next Action**: Phase 9 - Public API Exports (T901-T907)  
**Related Tasks**: 
- T701-T706: Schema validation implementation (COMPLETE)
- T801-T806: Dataset integration (COMPLETE)
- T901-T907: Public API exports (PENDING)

**Test Summary**:
- ✅ 15/15 schema validation tests passing
- ✅ 12/12 integration tests passing
- ✅ 18/18 existing dataset tests passing (no regressions)
- ✅ 105/117 total tests passing (90% complete)

