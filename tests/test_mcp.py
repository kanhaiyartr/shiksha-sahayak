from mcp_server import catalog
from mcp_server.catalog import UnknownTool


def test_dataset_is_synthetic_and_has_no_student_columns():
    catalog._cached_rows.cache_clear()
    rows = catalog.load_rows()
    assert len(rows) == 78
    assert catalog.list_states() == ["Uttarakhand"]
    assert len(catalog.list_districts("Uttarakhand")["districts"]) == 13
    assert "student_name" not in rows[0]
    assert all(row["record_type"] == "synthetic" for row in rows)
    assert all(row["state"] == "Uttarakhand" for row in rows)
    assert all(row["udise_code"].startswith("99") and len(row["udise_code"]) == 11 for row in rows)


def test_queries_do_not_change_the_file():
    before = catalog.file_bytes()
    catalog.list_states()
    catalog.enrolment_summary("Uttarakhand")
    catalog.schools_missing_facility("electricity", "Uttarakhand")
    catalog.get_school("99000000001")
    assert catalog.file_bytes() == before


def test_unknown_and_write_tools_are_rejected():
    for name in ("delete_school", "update_school", "insert_school", "write_file"):
        try:
            catalog.dispatch(name, {})
            rejected = False
        except UnknownTool:
            rejected = True
        assert rejected
    assert catalog.READ_ONLY_TOOLS.isdisjoint({"delete_school", "update_school", "insert_school"})


def test_missing_facility_matches_the_file():
    rows = [
        row for row in catalog.load_rows()
        if row["state"] == "Uttarakhand" and row["electricity"] == "no"
    ]
    result = catalog.schools_missing_facility("electricity", "Uttarakhand")
    assert result["count"] == len(rows)
    assert result["count"] > 0
    assert len(result["shown"]) <= 20


def test_server_exposes_only_those_tools():
    from mcp_server import server

    assert set(server.TOOL_NAMES) == catalog.READ_ONLY_TOOLS
    registered = {tool.name for tool in server.mcp._tool_manager.list_tools()}
    assert registered == set(server.TOOL_NAMES)
