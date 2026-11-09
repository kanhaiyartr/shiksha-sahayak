from types import SimpleNamespace

from app.generate import ClaudeGenerator, local_material, system_text
from app.models import GenerateIn
from app.offline import queue_request
from app.validate import validate_material


def test_local_worksheet_uses_chapter_facts_not_placeholders():
    spec = GenerateIn(topic="Fractions", class_level="5", language="en", task_type="worksheet", subject="Mathematics", n_questions=4)
    material, hint = local_material(spec)
    blob = " ".join(question.prompt for question in material.questions) + " " + " ".join(answer.answer for answer in material.answer_key)
    assert "Write one fact about Fractions" not in blob
    assert "A short textbook answer about Fractions" not in blob
    assert "numerator" in blob.casefold() or "denominator" in blob.casefold() or "1/2" in blob or "equal parts" in blob.casefold()
    assert "equal parts" in hint["note"].casefold() or "definition" in hint
    assert hint.get("definition")
    report = validate_material(material, spec)
    assert report.passed, [check for check in report.checks if not check.passed]


def test_local_lesson_plan_teaches_the_chapter():
    spec = GenerateIn(topic="Light", class_level="6", language="en", task_type="lesson_plan", subject="Science")
    material, _hint = local_material(spec)
    teach = next(section.body for section in material.sections if section.heading == "Teach")
    assert "straight" in teach.casefold() or "shadow" in teach.casefold() or "torch" in teach.casefold()
    assert material.answer_key == []
    assert "worksheet" in system_text("worksheet").casefold() or "Ground every question" in system_text("worksheet")


def test_claude_payload_forces_the_syllabus_tool_and_caches_the_prompt():
    spec = GenerateIn(topic="Light", class_level="6", language="en", task_type="worksheet", subject="Science")
    material, _hint = local_material(spec)

    class Messages:
        def __init__(self):
            self.created = []
            self.parsed = []

        def create(self, **kwargs):
            self.created.append(kwargs)
            block = {"type": "tool_use", "id": "toolu_test", "name": "lookup_syllabus_hint", "input": {"topic": "IGNORE THIS"}}
            usage = SimpleNamespace(input_tokens=20, output_tokens=10, cache_creation_input_tokens=80, cache_read_input_tokens=0)
            return SimpleNamespace(content=[block], usage=usage)

        def parse(self, **kwargs):
            self.parsed.append(kwargs)
            usage = SimpleNamespace(input_tokens=30, output_tokens=40, cache_creation_input_tokens=0, cache_read_input_tokens=80)
            return SimpleNamespace(parsed_output=material, usage=usage)

    messages = Messages()
    result, usage, hint = ClaudeGenerator(SimpleNamespace(messages=messages), "claude-sonnet-5-5").generate(spec, "")
    sent = messages.created[0]
    assert sent["tool_choice"] == {"type": "tool", "name": "lookup_syllabus_hint"}
    assert sent["system"][0]["cache_control"]["type"] == "ephemeral"
    assert "<untrusted_teacher_input>" in sent["messages"][0]["content"]
    assert "IGNORE THIS" not in hint["locator"]
    assert "Light" in hint["locator"]
    assert usage.cache_write_tokens == 80
    assert usage.cache_read_tokens == 80
    assert result.topic == "Light"
    assert messages.parsed[0]["output_format"].__name__ == "GeneratedMaterial"


def test_waiting_queue_strips_personal_data_before_saving(settings):
    queued = queue_request(
        settings.offline_db_path,
        {
            "topic": "Verbs",
            "class_level": "3",
            "language": "en",
            "task_type": "question_bank",
            "subject": "English",
            "notes": "Email priya.zz@example.com and phone 9876543210",
        },
        settings.retention_days,
    )
    stored = settings.offline_db_path.read_text(encoding="utf-8", errors="ignore")
    assert "9876543210" not in stored
    assert "priya.zz@example.com" not in stored
    assert queued["pii_counts"]["phone"] == 1
