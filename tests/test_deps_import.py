import importlib


def test_import_polars_lazy():
    pl = importlib.import_module("polars")
    # Ensure LazyFrame class is available
    assert hasattr(pl, "LazyFrame") or hasattr(pl, "lazy"), "Polars Lazy APIs not found"


def test_import_pyarrow_table():
    pa = importlib.import_module("pyarrow")
    assert hasattr(pa, "Table"), "PyArrow Table not found"


def test_import_pandas_dataframe():
    pd = importlib.import_module("pandas")
    assert hasattr(pd, "DataFrame"), "pandas DataFrame not found"
