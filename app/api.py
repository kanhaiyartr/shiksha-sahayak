"""HTTP API. The route layer does not mark a draft official; approval.py does."""

from __future__ import annotations

import re

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.approval import ApprovalError
from app.config import Settings, load_settings
from app.cost import BudgetError
from app.generate import EmptyTopicError
from app.models import Actor, GeneratedMaterial, GenerateIn
from app.documents import content_disposition
from app.pipeline import (
    budget,
    create_draft,
    estimate,
    get_draft,
    list_drafts,
    officer_approve,
    officer_edit,
    officer_reject,
    read_artifact,
)
from app.syllabus import list_catalog
from agent.readonly_agent import ReadOnlyAgent

_ACTOR_ID = re.compile(r"^[A-Za-z0-9._-]{2,64}$")


class RejectIn(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class AskIn(BaseModel):
    question: str = Field(min_length=3, max_length=500)


def _actor(request: Request) -> Actor:
    role = request.headers.get("x-actor-role", "")
    ident = request.headers.get("x-actor-id", "")
    if role not in ("teacher", "officer") or not _ACTOR_ID.fullmatch(ident):
        raise HTTPException(status_code=401, detail="Send X-Actor-Id and X-Actor-Role (teacher or officer).")
    return Actor(id=ident, role=role)  # type: ignore[arg-type]


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(title="Shiksha Sahayak", version="0.1.0")
    app.state.settings = settings

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "generate_mode": settings.generate_mode}

    @app.get("/syllabus")
    def syllabus_route(
        request: Request,
        class_level: str,
        language: str = "en",
        q: str = "",
    ) -> dict:
        _actor(request)
        if class_level not in {str(number) for number in range(1, 13)}:
            raise HTTPException(status_code=400, detail="Class must be from 1 to 12.")
        if language not in ("en", "hi"):
            raise HTTPException(status_code=400, detail="Language must be en or hi.")
        return list_catalog(class_level, language, q)

    @app.post("/estimate")
    def estimate_route(body: GenerateIn, request: Request) -> dict:
        _actor(request)
        try:
            return estimate(settings, body)
        except EmptyTopicError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/generate")
    def generate_route(body: GenerateIn, request: Request) -> dict:
        try:
            return create_draft(settings, _actor(request), body)
        except BudgetError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except EmptyTopicError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/drafts")
    def drafts_route(request: Request, status: str | None = None) -> list[dict]:
        _actor(request)
        if status is not None and status not in {"pending", "approved", "rejected"}:
            raise HTTPException(status_code=400, detail="Unknown status.")
        return list_drafts(settings, status)

    @app.get("/drafts/{material_id}")
    def draft_route(material_id: str, request: Request) -> dict:
        _actor(request)
        try:
            return get_draft(settings, material_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Draft not found.") from exc

    @app.get("/drafts/{material_id}/file")
    def draft_file_route(material_id: str, request: Request) -> Response:
        _actor(request)
        try:
            payload, content_type, filename = read_artifact(settings, material_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Draft not found.") from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="No downloadable file for this draft.") from exc
        return Response(
            content=payload,
            media_type=content_type,
            headers={"Content-Disposition": content_disposition(filename)},
        )

    @app.post("/drafts/{material_id}/approve")
    def approve_route(material_id: str, request: Request) -> dict:
        try:
            return officer_approve(settings, _actor(request), material_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Draft not found.") from exc
        except ApprovalError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @app.post("/drafts/{material_id}/reject")
    def reject_route(material_id: str, body: RejectIn, request: Request) -> dict:
        try:
            return officer_reject(settings, _actor(request), material_id, body.reason)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Draft not found.") from exc
        except ApprovalError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @app.post("/drafts/{material_id}/edit")
    def edit_route(material_id: str, body: GeneratedMaterial, request: Request) -> dict:
        try:
            return officer_edit(settings, _actor(request), material_id, body)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Draft not found.") from exc
        except ApprovalError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @app.get("/budget")
    def budget_route(request: Request) -> dict:
        _actor(request)
        return budget(settings)

    @app.post("/data/ask")
    def ask_route(body: AskIn, request: Request) -> dict:
        actor = _actor(request)
        answer = ReadOnlyAgent().ask(body.question)
        from app.audit import retention_deadline, write_audit
        from app.db import session

        with session(settings.db_path) as conn:
            write_audit(
                conn,
                actor=actor,
                action="data_question",
                retention_until=retention_deadline(settings.retention_days),
                redaction={},
                detail="Read-only question over the synthetic school file. Question text is not stored.",
            )
        return answer

    return app


app = create_app()
