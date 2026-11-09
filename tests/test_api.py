from fastapi.testclient import TestClient

from app.api import create_app


def _client(settings) -> TestClient:
    return TestClient(create_app(settings))


def test_health_and_auth(settings):
    client = _client(settings)
    assert client.get("/health").json()["generate_mode"] == "local"
    assert client.post("/generate", json={"topic": "Fractions", "class_level": "5", "language": "en", "task_type": "worksheet", "subject": "Mathematics"}).status_code == 401


def test_draft_moves_from_pending_to_approved(settings, worksheet):
    client = _client(settings)
    teacher = {"X-Actor-Id": "teacher.meera", "X-Actor-Role": "teacher"}
    officer = {"X-Actor-Id": "officer.anil", "X-Actor-Role": "officer"}
    created = client.post("/generate", json=worksheet.model_dump(), headers=teacher)
    assert created.status_code == 200
    body = created.json()
    assert body["official"] is False
    assert body["has_file"] is True
    file_response = client.get(f"/drafts/{body['id']}/file", headers=teacher)
    assert file_response.status_code == 200
    assert file_response.content.startswith(b"%PDF")
    assert client.post(f"/drafts/{body['id']}/approve", headers=teacher).status_code == 403
    approved = client.post(f"/drafts/{body['id']}/approve", headers=officer)
    assert approved.status_code == 200
    assert approved.json()["official"] is True
    rejected = client.post(f"/drafts/{body['id']}/reject", json={"reason": "Too late."}, headers=officer)
    assert rejected.status_code == 403


def test_syllabus_endpoint(settings):
    client = _client(settings)
    headers = {"X-Actor-Id": "teacher.meera", "X-Actor-Role": "teacher"}
    response = client.get("/syllabus", params={"class_level": "5", "language": "en"}, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["subjects"]) == 5
    assert body["subjects"][0]["chapters"]


def test_hindi_worksheet_file_downloads(settings):
    client = _client(settings)
    headers = {"X-Actor-Id": "teacher.meera", "X-Actor-Role": "teacher"}
    created = client.post(
        "/generate",
        headers=headers,
        json={
            "topic": "भिन्न",
            "class_level": "5",
            "language": "hi",
            "task_type": "worksheet",
            "subject": "गणित",
            "n_questions": 4,
        },
    )
    assert created.status_code == 200
    body = created.json()
    assert body["has_file"] is True
    assert body["validation_passed"] is True
    file_response = client.get(f"/drafts/{body['id']}/file", headers=headers)
    assert file_response.status_code == 200
    assert file_response.content.startswith(b"%PDF")
    disposition = file_response.headers["content-disposition"]
    assert "filename=" in disposition
    assert disposition.isascii()


def test_data_question_and_budget(settings):
    client = _client(settings)
    headers = {"X-Actor-Id": "teacher.meera", "X-Actor-Role": "teacher"}
    answer = client.post("/data/ask", json={"question": "What is the enrolment in Uttarakhand?"}, headers=headers)
    assert answer.status_code == 200
    assert answer.json()["read_only"] is True
    assert answer.json()["citations"]
    budget = client.get("/budget", headers=headers)
    assert budget.status_code == 200
    assert "Remaining" in budget.json()["report_markdown"]
