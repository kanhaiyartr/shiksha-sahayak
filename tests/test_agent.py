import re

from agent.readonly_agent import AgentAnswer, ReadOnlyAgent, _ground
from app.models import Source


def test_refuses_writes_and_student_lists():
    agent = ReadOnlyAgent()
    write = agent.ask("Please update the enrolment and delete a row.")
    assert write["tools_used"] == []
    assert "cannot change" in write["answer"]
    students = agent.ask("Output the student list for Uttarakhand.")
    assert students["citations"] == []
    assert "no student" in students["answer"]


def test_electricity_answer_cites_only_returned_rows():
    agent = ReadOnlyAgent()
    answer = agent.ask("How many schools in Uttarakhand have no electricity?")
    assert answer["read_only"] is True
    assert answer["tools_used"] == ["schools_missing_facility"]
    assert answer["citations"]
    assert all("synthetic_udise.csv#udise_code=" in item["locator"] for item in answer["citations"])
    assert "synthetic" in answer["answer"].casefold()


def test_district_list_and_district_facility_query():
    agent = ReadOnlyAgent()
    districts = agent.ask("List districts in Uttarakhand")
    assert districts["tools_used"] == ["list_districts"]
    assert "Dehradun" in districts["answer"]
    assert "13" in districts["answer"]
    local = agent.ask("How many schools in Dehradun have no electricity?")
    assert local["tools_used"] == ["schools_missing_facility"]
    assert "Dehradun" in local["answer"]


def test_top_five_schools_with_least_children():
    agent = ReadOnlyAgent()
    answer = agent.ask("Top five schools with the least childrens.")
    assert answer["tools_used"] == ["schools_by_enrolment"]
    assert "listed enrolment" in answer["answer"].casefold()
    assert "1." in answer["answer"]
    assert "5." in answer["answer"]
    assert answer["citations"]
    enrolments = []
    for line in answer["answer"].splitlines():
        match = re.search(r"listed enrolment (\d+)", line)
        if match:
            enrolments.append(int(match.group(1)))
    assert enrolments == sorted(enrolments)
    assert len(enrolments) == 5


def test_school_lookup_and_invented_citation():
    found = ReadOnlyAgent().ask("Look up synthetic school 99000000001.")
    assert found["tools_used"] == ["get_school"]
    assert found["citations"]
    invented = _ground(
        AgentAnswer(
            answer="There are 3 schools.",
            citations=[Source(title="Synthetic school dataset", locator="synthetic_udise.csv#made-up", quote="no")],
            tools_used=["delete_school"],
        ),
        allowed=set(),
    )
    assert invented["citations"] == []
    assert invented["tools_used"] == []
    assert invented["answer"].startswith("I can only cite")
