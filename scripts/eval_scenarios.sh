#!/usr/bin/env bash
set -euo pipefail

API="${API:-http://localhost:8000}"

echo "== health =="
curl -sf "$API/health"
echo

echo "== admin login =="
LOGIN=$(curl -sf -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"dev-admin-key"}' \
  "$API/api/auth/login")
ADMIN_SESSION=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["session_token"])' "$LOGIN")
auth_admin=(-H "Authorization: Bearer ${ADMIN_SESSION}" -H "Content-Type: application/json")

echo "== ensure demo server + sync =="
curl -sf "${auth_admin[@]}" -X POST -d '{}' "$API/api/servers/demo" >/tmp/gw-demo.json
SERVER_ID=$(python3 -c 'import json; print(json.load(open("/tmp/gw-demo.json"))["id"])')
curl -sf "${auth_admin[@]}" -X POST "$API/api/servers/${SERVER_ID}/sync" >/tmp/gw-sync.json
echo "synced server_id=$SERVER_ID"

echo "== create normal user =="
RAND=$RANDOM
USER_JSON=$(curl -sf "${auth_admin[@]}" \
  -d "{\"name\":\"Eval User\",\"username\":\"eval${RAND}\",\"email\":\"eval${RAND}@example.com\",\"password\":\"eval-pass-123\",\"role\":\"user\"}" \
  "$API/api/users")
USERNAME=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["username"])' "$USER_JSON")

echo "== user login =="
USER_LOGIN=$(curl -sf -H 'Content-Type: application/json' \
  -d "{\"username\":\"${USERNAME}\",\"password\":\"eval-pass-123\"}" \
  "$API/api/auth/login")
USER_SESSION=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["session_token"])' "$USER_LOGIN")
auth_user=(-H "Authorization: Bearer ${USER_SESSION}" -H "Content-Type: application/json")

echo "== user builds gateway with only notes_list =="
TOOLS=$(curl -sf "${auth_user[@]}" "$API/api/catalog/tools")
NOTES_LIST_ID=$(python3 -c 'import json,sys; t=json.loads(sys.argv[1]); print(next(x["id"] for x in t if x["name"]=="notes_list"))' "$TOOLS")
TOKEN_JSON=$(curl -sf "${auth_user[@]}" \
  -d "{\"label\":\"eval\",\"tool_ids\":[${NOTES_LIST_ID}]}" \
  "$API/api/me/gateway")
RAW=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["raw_token"])' "$TOKEN_JSON")
mcp_auth=(-H "Authorization: Bearer ${RAW}" -H "Content-Type: application/json")

echo "== scenario A: tools/list only notes_list =="
LIST=$(curl -sf "${mcp_auth[@]}" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  "$API/mcp")
python3 -c 'import json,sys; data=json.loads(sys.argv[1]); names=[t["name"] for t in data["result"]["tools"]]; print("tools:", names); assert names==["notes_list"], names; print("PASS scenario A")' "$LIST"

echo "== scenario B: tasks_add denied =="
curl -s -o /tmp/gw-deny.json -w "%{http_code}" "${mcp_auth[@]}" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"tasks_add","arguments":{"title":"x"}}}' \
  "$API/mcp" >/tmp/gw-deny.code
python3 -c 'import json; body=json.load(open("/tmp/gw-deny.json")); assert "error" in body, body; print("PASS scenario B")'

echo "== scenario C: notes_list allowed =="
curl -sf "${mcp_auth[@]}" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"notes_list","arguments":{"limit":3}}}' \
  "$API/mcp" >/tmp/gw-notes.json
python3 -c 'import json; body=json.load(open("/tmp/gw-notes.json")); assert "result" in body, body; print("PASS scenario C")'

echo "All evaluation scenarios passed."
