"""Practical demo MCP: personal notes + tasks for gateway demos."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

# Docker health/sync uses Host: demo-mcp:8100 — disable strict DNS rebinding for demo.
mcp = FastMCP(
    "demo-mcp",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    ),
)
mcp.settings.host = "0.0.0.0"
mcp.settings.port = 8100

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "workspace.json"
_LOCK = Lock()


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_store() -> dict[str, Any]:
    return {
        "notes": [
            {
                "id": "note_welcome",
                "title": "Thesis demo note",
                "body": "MCP Gateway can expose only selected tools from this server.",
                "tags": ["demo", "thesis"],
                "created_at": _utcnow(),
            },
            {
                "id": "note_meeting",
                "title": "Meeting follow-ups",
                "body": "Ask reviewer about access-control evaluation scenarios.",
                "tags": ["meeting"],
                "created_at": _utcnow(),
            },
        ],
        "tasks": [
            {
                "id": "task_prep_demo",
                "title": "Prepare gateway live demo",
                "priority": "high",
                "status": "open",
                "created_at": _utcnow(),
                "completed_at": None,
            }
        ],
    }


def _load() -> dict[str, Any]:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        store = _empty_store()
        DATA_PATH.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")
        return store
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def _save(store: dict[str, Any]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


def _with_store(mutator):
    with _LOCK:
        store = _load()
        result = mutator(store)
        _save(store)
        return result


@mcp.tool()
def notes_create(title: str, body: str, tags: str = "") -> dict[str, Any]:
    """Create a personal note. Tags are comma-separated (e.g. 'work,demo')."""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    def mutate(store: dict[str, Any]) -> dict[str, Any]:
        note = {
            "id": f"note_{uuid.uuid4().hex[:8]}",
            "title": title.strip(),
            "body": body.strip(),
            "tags": tag_list,
            "created_at": _utcnow(),
        }
        store.setdefault("notes", []).insert(0, note)
        return note

    return _with_store(mutate)


@mcp.tool()
def notes_list(limit: int = 20) -> dict[str, Any]:
    """List recent notes (id, title, tags, created_at)."""
    limit = max(1, min(limit, 100))
    with _LOCK:
        notes = _load().get("notes", [])[:limit]
    return {
        "count": len(notes),
        "notes": [
            {
                "id": n["id"],
                "title": n["title"],
                "tags": n.get("tags", []),
                "created_at": n.get("created_at"),
            }
            for n in notes
        ],
    }


@mcp.tool()
def notes_search(query: str) -> dict[str, Any]:
    """Search notes by title, body, or tags."""
    q = query.strip().lower()
    with _LOCK:
        notes = _load().get("notes", [])
    hits = []
    for n in notes:
        blob = " ".join(
            [
                n.get("title", ""),
                n.get("body", ""),
                " ".join(n.get("tags", [])),
            ]
        ).lower()
        if q and q in blob:
            hits.append(
                {
                    "id": n["id"],
                    "title": n["title"],
                    "snippet": n.get("body", "")[:160],
                    "tags": n.get("tags", []),
                }
            )
    return {"query": query, "count": len(hits), "matches": hits}


@mcp.tool()
def notes_get(note_id: str) -> dict[str, Any]:
    """Get one note by id, including full body."""
    with _LOCK:
        notes = _load().get("notes", [])
    for n in notes:
        if n["id"] == note_id:
            return n
    return {"error": "not_found", "note_id": note_id}


@mcp.tool()
def tasks_add(title: str, priority: str = "medium") -> dict[str, Any]:
    """Add a task. Priority: low | medium | high."""
    priority = priority.strip().lower()
    if priority not in {"low", "medium", "high"}:
        priority = "medium"

    def mutate(store: dict[str, Any]) -> dict[str, Any]:
        task = {
            "id": f"task_{uuid.uuid4().hex[:8]}",
            "title": title.strip(),
            "priority": priority,
            "status": "open",
            "created_at": _utcnow(),
            "completed_at": None,
        }
        store.setdefault("tasks", []).insert(0, task)
        return task

    return _with_store(mutate)


@mcp.tool()
def tasks_list(status: str = "open") -> dict[str, Any]:
    """List tasks. Status: open | done | all."""
    status = status.strip().lower()
    if status not in {"open", "done", "all"}:
        status = "open"
    with _LOCK:
        tasks = _load().get("tasks", [])
    if status != "all":
        tasks = [t for t in tasks if t.get("status") == status]
    return {"status": status, "count": len(tasks), "tasks": tasks}


@mcp.tool()
def tasks_complete(task_id: str) -> dict[str, Any]:
    """Mark a task as done."""

    def mutate(store: dict[str, Any]) -> dict[str, Any]:
        for task in store.get("tasks", []):
            if task["id"] == task_id:
                task["status"] = "done"
                task["completed_at"] = _utcnow()
                return task
        return {"error": "not_found", "task_id": task_id}

    return _with_store(mutate)


def main() -> None:
    _load()
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
