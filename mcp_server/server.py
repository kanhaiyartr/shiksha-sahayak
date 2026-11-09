"""MCP entrypoint. Every tool reads the synthetic file. None of them write."""

from __future__ import annotations

try:
    from mcp.server.mcpserver import MCPServer as Server
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as Server

from mcp_server import catalog

mcp = Server("shiksha-udise")


@mcp.tool()
def list_states() -> list[str]:
    """List states in the synthetic school file. Read only. There are no student records."""
    return catalog.list_states()


@mcp.tool()
def list_districts(state: str) -> dict:
    """List districts for one synthetic state. Read only."""
    return catalog.list_districts(state)


@mcp.tool()
def enrolment_summary(state: str = "") -> dict:
    """Sum listed enrolment and teachers. Read only. This is not a student list."""
    return catalog.enrolment_summary(state or None)


@mcp.tool()
def schools_missing_facility(facility: str, state: str = "") -> dict:
    """List synthetic schools marked no for electricity, drinking_water, or functional_toilet."""
    return catalog.schools_missing_facility(facility, state or None)


@mcp.tool()
def get_school(udise_code: str) -> dict:
    """Fetch one synthetic school by its fake UDISE-style code. Read only."""
    return catalog.get_school(udise_code)


@mcp.tool()
def schools_by_enrolment(limit: int = 5, order: str = "asc", state: str = "", district: str = "") -> dict:
    """Rank synthetic schools by listed enrolment. order=asc for least, desc for most. Not a pupil list."""
    return catalog.schools_by_enrolment(limit, order, state or None, district or None)


TOOL_NAMES = (
    "list_states",
    "list_districts",
    "enrolment_summary",
    "schools_missing_facility",
    "schools_by_enrolment",
    "get_school",
)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
