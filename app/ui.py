"""One task on each screen. The server does the checks; this file only displays them."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import httpx
import streamlit as st

from app.config import load_settings
from app.offline import list_waiting, mark, queue_request

SETTINGS = load_settings()
TIMEOUT = 120.0

LABELS = {
    "en": {
        "screen": "Screen",
        "screens": ["New request", "Review", "Budget", "School data", "Waiting queue"],
        "role": "Role",
        "staff": "Staff id",
        "title": "Shiksha Sahayak",
        "caption": "A draft is not official until an officer approves it. Do not type student names, phone numbers, Aadhaar numbers, or school login details.",
        "task": "Task",
        "class": "Class",
        "language": "Material language",
        "subject": "Subject",
        "topic": "Chapter",
        "search": "Search subjects or chapters",
        "sample": "Sample syllabus for this prototype. Check the textbook before class.",
        "count": "Number of questions",
        "notes": "Notes for the draft",
        "submit": "Submit draft",
        "remaining": "Remaining under cap (Claude billable only)",
        "first": "Claude-equivalent if cache miss",
        "cached": "Claude-equivalent if cache hit",
        "likely": "Likely this request",
        "against_cap": "Counts against cap",
        "offline": "The server could not be reached. The request is in the waiting queue. Personal data was removed before it was stored.",
        "pending": "Saved as pending. It is not official.",
        "download": "Download file",
        "download_fail": "The draft was saved, but the downloadable file could not be loaded.",
        "approve": "Approve",
        "reject": "Reject",
        "reason": "Reason for rejection or suggested changes",
        "save": "Save edit",
        "notes_edit": "Teacher notes",
        "ask": "Ask about the synthetic school file",
        "question": "Question",
        "send": "Ask",
        "retry": "Send waiting requests",
        "empty": "Nothing here.",
        "local": "Local mode: $0 against the cap. The dollar figures are Claude-equivalent estimates only.",
        "cap": "The monthly Claude cap would be exceeded. The request was not sent.",
        "review_hint": "An officer reviews, edits, approves, or rejects with a reason. Nothing is official until approval.",
        "data_examples": "Try: Top five schools with the least children | How many schools in Uttarakhand have no electricity? | List districts in Uttarakhand | Look up school 99000000001",
        "data_answer": "Answer",
        "data_sources": "Sources",
        "budget_billable": "Billable Claude spend",
        "budget_local": "Local estimate (not billed)",
    },
    "hi": {
        "screen": "स्क्रीन",
        "screens": ["नया अनुरोध", "समीक्षा", "बजट", "स्कूल आँकड़े", "प्रतीक्षा"],
        "role": "भूमिका",
        "staff": "कर्मचारी पहचान",
        "title": "शिक्षा सहायक",
        "caption": "अधिकारी की मंजूरी से पहले कोई मसौदा आधिकारिक नहीं है। छात्र का नाम, फ़ोन, आधार या स्कूल लॉगिन न लिखें।",
        "task": "कार्य",
        "class": "कक्षा",
        "language": "सामग्री की भाषा",
        "subject": "विषय",
        "topic": "अध्याय",
        "search": "विषय या अध्याय खोजें",
        "sample": "यह नमूना पाठ्यक्रम है। कक्षा से पहले पाठ्यपुस्तक देखें।",
        "count": "प्रश्नों की संख्या",
        "notes": "मसौदे के लिए नोट",
        "submit": "मसौदा भेजें",
        "remaining": "सीमा में शेष (केवल क्लाउड बिल)",
        "first": "कैश न लगे तो क्लाउड-समान लागत",
        "cached": "कैश लगे तो क्लाउड-समान लागत",
        "likely": "इस अनुरोध की संभावित लागत",
        "against_cap": "सीमा में गिनी जाने वाली राशि",
        "offline": "सर्वर नहीं मिला। अनुरोध प्रतीक्षा में है। निजी डेटा हटाकर रखा गया है।",
        "pending": "लंबित के रूप में सहेजा गया। यह आधिकारिक नहीं है।",
        "download": "फ़ाइल डाउनलोड करें",
        "download_fail": "मसौदा सहेजा गया, पर डाउनलोड फ़ाइल नहीं मिली।",
        "approve": "मंजूर करें",
        "reject": "अस्वीकार करें",
        "reason": "अस्वीकृति या सुझाव का कारण",
        "save": "संपादन सहेजें",
        "notes_edit": "शिक्षक नोट",
        "ask": "कृत्रिम स्कूल फ़ाइल से पूछें",
        "question": "प्रश्न",
        "send": "पूछें",
        "retry": "प्रतीक्षा के अनुरोध भेजें",
        "empty": "यहाँ कुछ नहीं है।",
        "local": "स्थानीय मोड: सीमा में $0। दिखाए गए डॉलर केवल क्लाउड-समान अनुमान हैं।",
        "cap": "मासिक क्लाउड सीमा पूरी हो जाएगी। अनुरोध नहीं भेजा गया।",
        "review_hint": "अधिकारी समीक्षा, संपादन, मंजूरी या कारण के साथ अस्वीकृति करता है। मंजूरी से पहले कुछ आधिकारिक नहीं है।",
        "data_examples": "उदाहरण: Top five schools with the least children | How many schools in Uttarakhand have no electricity? | List districts in Uttarakhand",
        "data_answer": "उत्तर",
        "data_sources": "स्रोत",
        "budget_billable": "क्लाउड बिल योग्य खर्च",
        "budget_local": "स्थानीय अनुमान (बिल नहीं)",
    },
}

TASKS = {"Worksheet": "worksheet", "Lesson plan": "lesson_plan", "Question bank": "question_bank"}
SCREEN_KEYS = ["request", "review", "budget", "data", "queue"]


def _headers() -> dict[str, str]:
    return {"X-Actor-Id": st.session_state.actor, "X-Actor-Role": st.session_state.role}


def _client() -> httpx.Client:
    return httpx.Client(base_url=SETTINGS.api_base, timeout=TIMEOUT, headers=_headers())


def _detail(response: httpx.Response) -> str:
    payload = response.json()
    detail = payload.get("detail", "The request failed.")
    if isinstance(detail, list):
        return "Check the subject, topic, and class, then submit again."
    return str(detail)


def _payload() -> dict:
    return {
        "topic": st.session_state.topic,
        "class_level": st.session_state.class_level,
        "language": st.session_state.material_language,
        "task_type": TASKS[st.session_state.task_label],
        "subject": st.session_state.subject,
        "n_questions": int(st.session_state.n_questions),
        "notes": st.session_state.notes,
    }


def _fetch_syllabus(class_level: str, language: str, query: str) -> dict | None:
    try:
        with _client() as client:
            response = client.get(
                "/syllabus",
                params={"class_level": class_level, "language": language, "q": query},
            )
    except httpx.HTTPError:
        return None
    if response.status_code != 200:
        return None
    return response.json()


def page_request(text: dict[str, str]) -> None:
    st.subheader(text["screens"][0])
    st.selectbox(text["task"], list(TASKS), key="task_label")
    st.selectbox(text["class"], [str(number) for number in range(1, 13)], index=4, key="class_level")
    st.selectbox(text["language"], ["en", "hi"], key="material_language")
    st.text_input(text["search"], key="syllabus_query")
    catalog = _fetch_syllabus(
        st.session_state.class_level,
        st.session_state.material_language,
        st.session_state.get("syllabus_query", ""),
    )
    if catalog is None:
        st.warning(text["offline"])
        subjects: list[dict] = []
    else:
        st.caption(catalog.get("note") or text["sample"])
        subjects = catalog.get("subjects") or []
    subject_names = [item["name"] for item in subjects]
    if not subject_names:
        st.session_state.subject = ""
        st.session_state.topic = ""
        st.write(text["empty"])
        return
    if st.session_state.get("subject") not in subject_names:
        st.session_state.subject = subject_names[0]
    st.selectbox(text["subject"], subject_names, key="subject")
    chapters = next((item["chapters"] for item in subjects if item["name"] == st.session_state.subject), [])
    chapter_topics = [item["topic"] for item in chapters]
    if not chapter_topics:
        st.session_state.topic = ""
        st.write(text["empty"])
        return
    if st.session_state.get("topic") not in chapter_topics:
        st.session_state.topic = chapter_topics[0]
    st.selectbox(text["topic"], chapter_topics, key="topic")
    st.slider(text["count"], 1, 8, 4, key="n_questions")
    st.text_area(text["notes"], key="notes")
    if len(st.session_state.topic.strip()) >= 2 and len(st.session_state.subject.strip()) >= 2:
        try:
            with _client() as client:
                response = client.post("/estimate", json=_payload())
            if response.status_code == 200:
                quote = response.json()
                st.write(f"{text['remaining']}: ${quote['remaining_usd']:.4f}")
                st.write(f"{text['likely']}: ${quote.get('likely_request_usd', quote['first_request_usd']):.4f}")
                st.write(f"{text['against_cap']}: ${quote.get('counts_against_cap_usd', 0):.4f}")
                st.caption(
                    f"{text['first']}: ${quote['first_request_usd']:.4f} · "
                    f"{text['cached']}: ${quote['cached_request_usd']:.4f}"
                )
                if quote["provider"] == "local":
                    st.caption(text["local"])
                else:
                    st.caption(quote.get("note", ""))
                if not quote["within_cap"]:
                    st.error(text["cap"])
            else:
                st.error(_detail(response))
        except httpx.HTTPError:
            st.warning(text["offline"])
    if st.button(text["submit"], type="primary"):
        body = _payload()
        try:
            with _client() as client:
                response = client.post("/generate", json=body)
            if response.status_code == 200:
                draft = response.json()
                st.success(text["pending"] if not draft["official"] else "Approved.")
                st.write(f"Status: {draft['status']}")
                st.caption(text["review_hint"])
                for check in draft["checks"]:
                    mark_text = "pass" if check["passed"] else "fail"
                    st.write(f"{mark_text} — {check['name']}: {check['detail']}")
                _download_button(text, draft["id"])
            elif response.status_code == 409:
                st.error(text["cap"])
            else:
                st.error(_detail(response))
        except httpx.HTTPError:
            queued = queue_request(SETTINGS.offline_db_path, body, SETTINGS.retention_days)
            st.warning(text["offline"])
            st.write(queued["id"])


def _download_button(text: dict[str, str], draft_id: str) -> None:
    try:
        with _client() as client:
            response = client.get(f"/drafts/{draft_id}/file")
    except httpx.HTTPError:
        st.warning(text.get("download_fail", "The file could not be downloaded."))
        return
    if response.status_code != 200:
        st.warning(text.get("download_fail", "The file could not be downloaded."))
        return
    content_type = response.headers.get("content-type", "application/octet-stream")
    disposition = response.headers.get("content-disposition", "")
    filename = "draft.bin"
    if "filename=" in disposition:
        # Prefer the plain filename= token; ignore filename*= if present after it.
        part = disposition.split("filename=")[-1]
        filename = part.split(";")[0].strip().strip('"')
    st.download_button(
        text["download"],
        data=response.content,
        file_name=filename or "draft.bin",
        mime=content_type,
        key=f"download-{draft_id}",
    )


def _show_material(material: dict) -> None:
    st.markdown(f"**{material['title']}**")
    for section in material["sections"]:
        st.write(section["heading"])
        st.write(section["body"])
    for question in material["questions"]:
        st.write(f"{question['number']}. {question['prompt']}")
    if material.get("answer_key"):
        st.write("Answer key")
        for answer in material["answer_key"]:
            st.write(f"{answer['number']}. {answer['answer']}")
    for source in material["sources"]:
        st.caption(f"{source['title']} — {source['locator']}")


def page_review(text: dict[str, str]) -> None:
    st.subheader(text["screens"][1])
    st.caption(text["review_hint"])
    try:
        with _client() as client:
            response = client.get("/drafts")
        drafts = response.json() if response.status_code == 200 else []
    except httpx.HTTPError:
        st.warning(text["offline"])
        return
    if not drafts:
        st.write(text["empty"])
        return
    labels = {f"{item['status']} · {item['task_type']} · {item['topic']} · {item['id'][:8]}": item for item in drafts}
    choice = st.selectbox("Draft", list(labels))
    draft = labels[choice]
    st.write("Official" if draft["official"] else "Not official")
    st.write(f"Status: {draft['status']}")
    if draft.get("rejection_reason"):
        st.write(draft["rejection_reason"])
    for check in draft["checks"]:
        st.write(("pass" if check["passed"] else "fail") + " — " + check["name"])
    material = draft.get("material")
    if material:
        _show_material(material)
        _download_button(text, draft["id"])
    if st.session_state.role != "officer" or draft["status"] != "pending" or not material:
        return
    edited = dict(material)
    edited["teacher_notes"] = st.text_area(text["notes_edit"], value=material["teacher_notes"])
    if st.button(text["save"]):
        with _client() as client:
            saved = client.post(f"/drafts/{draft['id']}/edit", json=edited)
        st.write(saved.json().get("detail", "Saved. Still pending.") if saved.status_code != 200 else "Saved. Still pending.")
    if st.button(text["approve"], type="primary"):
        with _client() as client:
            result = client.post(f"/drafts/{draft['id']}/approve")
        if result.status_code == 200 and result.json()["official"]:
            st.success("Approved.")
        else:
            st.error(result.json().get("detail", "Not approved."))
    reason = st.text_input(text["reason"])
    if st.button(text["reject"]):
        with _client() as client:
            result = client.post(f"/drafts/{draft['id']}/reject", json={"reason": reason or "Needs changes."})
        st.write(result.json().get("status") or result.json().get("detail"))


def page_budget(text: dict[str, str]) -> None:
    st.subheader(text["screens"][2])
    try:
        with _client() as client:
            response = client.get("/budget")
    except httpx.HTTPError:
        st.warning(text["offline"])
        return
    if response.status_code != 200:
        st.error("The budget could not be loaded.")
        return
    body = response.json()
    st.write(f"{text['remaining']}: ${body['remaining_usd']:.4f} of ${body['cap_usd']:.2f}")
    st.write(f"{text['budget_billable']}: ${body.get('billable_usd', body['spent_usd']):.6f}")
    st.write(f"{text['budget_local']}: ${body.get('local_estimated_usd', 0):.6f}")
    st.markdown(body["report_markdown"])


def page_data(text: dict[str, str]) -> None:
    st.subheader(text["screens"][3])
    st.caption(text["ask"])
    st.caption(text["data_examples"])
    with st.form("school_data_form", clear_on_submit=False):
        question = st.text_input(text["question"], key="data_question")
        submitted = st.form_submit_button(text["send"], type="primary")
    if submitted:
        if not question.strip():
            st.warning(text["empty"])
        else:
            try:
                with _client() as client:
                    response = client.post("/data/ask", json={"question": question.strip()})
            except httpx.HTTPError:
                st.warning(text["offline"])
                return
            if response.status_code != 200:
                detail = response.json().get("detail", "No answer.") if response.headers.get("content-type", "").startswith("application/json") else "No answer."
                st.error(detail)
                st.session_state.pop("data_answer", None)
                return
            st.session_state.data_answer = response.json()
    body = st.session_state.get("data_answer")
    if not body:
        return
    st.markdown(f"**{text['data_answer']}**")
    st.write(body["answer"])
    if body.get("citations"):
        st.markdown(f"**{text['data_sources']}**")
        for source in body["citations"]:
            st.caption(f"{source['title']} — {source['locator']}")


def page_queue(text: dict[str, str]) -> None:
    st.subheader(text["screens"][4])
    waiting = list_waiting(SETTINGS.offline_db_path)
    if not waiting:
        st.write(text["empty"])
        return
    for item in waiting:
        st.write(item["id"])
    if st.button(text["retry"], type="primary"):
        for item in waiting:
            try:
                with _client() as client:
                    response = client.post("/generate", json=json.loads(item["payload"]))
                if response.status_code == 200:
                    mark(SETTINGS.offline_db_path, item["id"], "submitted")
                else:
                    mark(SETTINGS.offline_db_path, item["id"], "waiting", "server rejected")
            except httpx.HTTPError:
                mark(SETTINGS.offline_db_path, item["id"], "waiting", "still offline")
        st.rerun()


def main() -> None:
    st.set_page_config(page_title="Shiksha Sahayak", layout="centered")
    ui_language = st.sidebar.selectbox("Interface", ["en", "hi"])
    text = LABELS[ui_language]
    st.title(text["title"])
    st.caption(text["caption"])
    if "role" not in st.session_state:
        st.session_state.role = "teacher"
    if "actor" not in st.session_state:
        st.session_state.actor = "teacher.meera"
    st.sidebar.selectbox(text["role"], ["teacher", "officer"], key="role")
    if st.session_state.get("_last_role") != st.session_state.role:
        st.session_state.actor = "officer.anil" if st.session_state.role == "officer" else "teacher.meera"
        st.session_state._last_role = st.session_state.role
    st.sidebar.text_input(text["staff"], key="actor")
    screen = st.sidebar.radio(text["screen"], SCREEN_KEYS, format_func=lambda key: text["screens"][SCREEN_KEYS.index(key)])
    pages = {
        "request": page_request,
        "review": page_review,
        "budget": page_budget,
        "data": page_data,
        "queue": page_queue,
    }
    pages[screen](text)


main()
