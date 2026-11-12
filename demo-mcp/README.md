# demo-mcp

Small but practical upstream MCP for gateway demos: **notes + tasks**.

## Tools

| Tool | Purpose |
| --- | --- |
| `notes_create` | Create a note (`title`, `body`, optional `tags`) |
| `notes_list` | List recent notes |
| `notes_search` | Search notes by text/tags |
| `notes_get` | Fetch one note by id |
| `tasks_add` | Add a task with priority |
| `tasks_list` | List open/done/all tasks |
| `tasks_complete` | Mark a task done |

Data is stored in `demo-mcp/data/workspace.json` and seeded with sample notes/tasks on first run.

## Run

```bash
pip install .
python -m demo_mcp.server
```

Endpoint: `http://localhost:8100/mcp`
