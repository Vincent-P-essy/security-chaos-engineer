from __future__ import annotations

import pytest

from security_chaos_engineer.loader import load_default_system
from security_chaos_engineer.models import TargetSystem


@pytest.fixture
def system() -> TargetSystem:
    return load_default_system()
