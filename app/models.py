"""Shared request and draft schemas. The model fills GeneratedMaterial only."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Language = Literal["en", "hi"]
TaskType = Literal["worksheet", "lesson_plan", "question_bank"]
Role = Literal["teacher", "officer"]
Status = Literal["pending", "approved", "rejected"]


class GenerateIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    topic: str = Field(min_length=2, max_length=120)
    class_level: str = Field(pattern=r"^(?:[1-9]|1[0-2])$")
    language: Language
    task_type: TaskType
    subject: str = Field(min_length=2, max_length=60)
    n_questions: int = Field(default=4, ge=1, le=8)
    notes: str = Field(default="", max_length=1500)
    model: str | None = Field(default=None, max_length=64)


class Section(BaseModel):
    model_config = ConfigDict(extra="forbid")

    heading: str = Field(min_length=1, max_length=80)
    body: str = Field(min_length=1, max_length=600)


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")

    number: int = Field(ge=1, le=8)
    prompt: str = Field(min_length=1, max_length=300)
    marks: int = Field(default=1, ge=1, le=5)


class Answer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    number: int = Field(ge=1, le=8)
    answer: str = Field(min_length=1, max_length=300)


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=160)
    locator: str = Field(min_length=1, max_length=200)
    quote: str = Field(default="", max_length=300)


class GeneratedMaterial(BaseModel):
    """Structured draft. There is no status field: only the approval code sets that."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=160)
    language: Language
    task_type: TaskType
    class_level: str = Field(pattern=r"^(?:[1-9]|1[0-2])$")
    subject: str = Field(min_length=1, max_length=60)
    topic: str = Field(min_length=1, max_length=120)
    sections: list[Section] = Field(max_length=12)
    questions: list[Question] = Field(max_length=8)
    answer_key: list[Answer] = Field(default_factory=list, max_length=8)
    teacher_notes: str = Field(max_length=800)
    sources: list[Source] = Field(min_length=1, max_length=6)


class Check(BaseModel):
    name: str
    passed: bool
    detail: str


class ValidationReport(BaseModel):
    passed: bool
    checks: list[Check]


class Actor(BaseModel):
    id: str
    role: Role


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0

    def add(self, other: Usage) -> Usage:
        return Usage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cache_write_tokens=self.cache_write_tokens + other.cache_write_tokens,
            cache_read_tokens=self.cache_read_tokens + other.cache_read_tokens,
        )
