import warnings

import pytest

from air_quality.exceptions import (
    SchemaError,
    DataValidationError,
    UnitError,
    AlgorithmConvergenceError,
    ConfigurationError,
    PerformanceWarning,
)


def test_schema_error():
    with pytest.raises(SchemaError):
        raise SchemaError("missing columns: ['datetime']")


def test_data_validation_error():
    with pytest.raises(DataValidationError):
        raise DataValidationError("empty dataset")


def test_unit_error():
    with pytest.raises(UnitError):
        raise UnitError("ppm -> ug/m3 conversion failed")


def test_algorithm_convergence_error():
    with pytest.raises(AlgorithmConvergenceError):
        raise AlgorithmConvergenceError("EM algorithm did not converge")


def test_configuration_error():
    with pytest.raises(ConfigurationError):
        raise ConfigurationError("unsupported mode: 'fast-and-loose'")


def test_performance_warning():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        warnings.warn("fallback path taken", PerformanceWarning)
        assert any(
            isinstance(w.message, PerformanceWarning) for w in caught
        ), "PerformanceWarning not captured"
