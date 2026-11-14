import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"

# Make `import reslink` work when running `pytest` from the project root.
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def placeholder_catalog_path() -> Path:
    return FIXTURES / "placeholder_resources.json"
