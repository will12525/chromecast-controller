"""
Legacy schema tests against removed DBCreatorV2 / playlist list-index model.

Skipped at module level. Schema migration and content insert coverage lives in
tests/test_library_home.py (schema v3, added_at, continue watching).
"""
import pytest

pytest.skip(
    "Legacy DBCreatorV2 / common_objects playlist APIs removed after app refactor; "
    "use tests/test_library_home.py",
    allow_module_level=True,
)
