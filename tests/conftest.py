from __future__ import annotations

import pytest

from app.config import STANDARD_MODEL, Settings
from app.models import Actor, GenerateIn


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        db_path=tmp_path / "app.sqlite",
        offline_db_path=tmp_path / "offline.sqlite",
        monthly_cap_usd=5,
        retention_days=30,
        generate_mode="local",
        model=STANDARD_MODEL,
    )


@pytest.fixture
def teacher() -> Actor:
    return Actor(id="teacher.meera", role="teacher")


@pytest.fixture
def officer() -> Actor:
    return Actor(id="officer.anil", role="officer")


@pytest.fixture
def worksheet() -> GenerateIn:
    return GenerateIn(
        topic="Fractions",
        class_level="5",
        language="en",
        task_type="worksheet",
        subject="Mathematics",
        n_questions=4,
    )
