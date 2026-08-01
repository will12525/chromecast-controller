"""
Legacy DatabaseHandlerV2 / DBCreatorV2 integration tests.

Skipped at module level. DBHandler (schema v2/v3 shelves + progress) is covered by
tests/test_library_home.py.
"""
import pytest

pytest.skip(
    "Legacy DatabaseHandlerV2 / DBCreatorV2 removed after app refactor; "
    "use tests/test_library_home.py",
    allow_module_level=True,
)
