# مرجع API — MCP Gateway

پایه: `http://localhost:8000`  
از UI معمولاً از مسیر `/gw` استفاده می‌شود.

## ۱. Authentication داشبورد

### `POST /api/auth/login`

```json
{ "username": "admin", "password": "dev-admin-key" }
```

پاسخ:

```json
{
  "ok": true,
  "session_token": "sess_...",
  "user": { "id": 1, "username": "admin", "role": "admin", "...": "..." }
}
```

### `GET /api/auth/me`
Header: `Authorization: Bearer sess_...`

### `POST /api/auth/logout`
Header: `Authorization: Bearer sess_...`

---

## ۲. Overview / Connect

همه با session Bearer.

- `GET /api/overview`
- `GET /api/connect`

---

## ۳. کاربران (فقط admin)

### `GET /api/users`

### `POST /api/users`

```json
{
  "name": "Ali",
  "username": "ali",
  "email": "ali@example.com",
  "password": "secret123",
  "role": "user"
}
```

---

## ۴. Gateway کاربر (me)

### `GET /api/catalog/tools`
لیست toolهای قابل انتخاب از کاتالوگ عمومی.

### `GET /api/me/tokens`

### `POST /api/me/gateway`

```json
{
  "label": "my-gateway",
  "tool_ids": [2, 3]
}
```

پاسخ شامل `raw_token` یک‌باره است.

### `POST /api/me/tokens/{id}/revoke`

### `GET /api/me/tokens/{id}/grants`
وضعیت grant همهٔ toolها برای آن token (`granted: true/false`).

### `PUT /api/me/tokens/{id}/grants`
ویرایش allowlist همان Gateway بدون تعویض token.

```json
{
  "tool_ids": [2, 5, 7]
}
```

قوانین:
- حداقل یک `tool_id`
- token باید متعلق به کاربر جاری و باطل‌نشده باشد
- toolهای تکراری در بدنه یک‌بار لحاظ می‌شوند
- پاسخ همان شکل `GET .../grants` است

---

## ۵. کاتالوگ MCP

### `GET /api/servers`
کاربر: فقط public. ادمین: همه.

### `POST /api/servers/demo` (admin)
اگر `demo-mcp` از قبل باشد همان را برمی‌گرداند؛ برای چند سرور از `POST /api/servers` با نام یکتا استفاده کنید.

### `POST /api/servers` (admin)
### `POST /api/servers/{id}/sync` (admin)
### `DELETE /api/servers/{id}` (admin)
پاسخ `204 No Content`. از UI از مسیر `/gw` هم کار می‌کند.

### `GET /api/servers/{id}/tools`

بدنهٔ ساخت سرور:

```json
{
  "name": "notes-prod",
  "base_url": "https://example-mcp.example/mcp",
  "transport": "streamable-http",
  "auth_header": "Bearer sk-upstream-key"
}
```

`name` باید یکتا باشد؛ `name` و `base_url` خالی مجاز نیست. چند سرور می‌توانند به یک URL اشاره کنند اگر نام‌شان فرق کند.

- `transport`: در این نسخه عملاً remote HTTP / `streamable-http`؛ multi-transport عمداً نیست.  
- `auth_header` اختیاری است؛ باید همان مقدار کامل هدر `Authorization` سمت upstream باشد (مثلاً `Bearer sk-...`). نام هدر دلخواه پشتیبانی نمی‌شود. در پاسخ `GET /api/servers` برنمی‌گردد.

---

## ۶. MCP endpoint کلاینت AI

### `POST /mcp`
Header: `Authorization: Bearer mcpgw_...`

Methodهای پشتیبانی‌شده: `initialize`, `tools/list`, `tools/call`, `ping`

نمونه list:

```json
{ "jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {} }
```

نمونه call:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": { "name": "notes_list", "arguments": { "limit": 5 } }
}
```

---

## ۷. کدهای مهم

| کد | معنی |
| --- | --- |
| 401 | session/platform token نامعتبر |
| 403 | نقش ناکافی یا tool grant نشده |
| 422 | بدنه نامعتبر |
| 502 | خطای upstream هنگام Sync/call |
