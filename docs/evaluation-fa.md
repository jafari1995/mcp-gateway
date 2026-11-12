# سند ارزیابی سامانه

هدف: اثبات سیاست allowlist روی `/mcp` و فلو login کاربر.

## ۱. محیط

| جزء | مقدار |
| --- | --- |
| Gateway | http://localhost:8000 |
| UI | http://localhost:3001 |
| اسکریپت | `scripts/eval_scenarios.sh` |

## ۲. سناریوها

### سناریو Auth
ادمین login می‌کند، کاربر می‌سازد، همان کاربر با password خودش login می‌کند.

### سناریو A — Allowlist visibility
کاربر Gateway را فقط با `notes_list` می‌سازد.  
`tools/list` باید فقط `notes_list` را برگرداند.

### سناریو B — Deny unauthorized call
همان platform token برای `tasks_add` باید رد شود.

### سناریو C — Allowed call
`tools/call` برای `notes_list` باید موفق باشد.

### سناریو D — ویرایش Gateway (دستی / e2e)
1. روی همان token با `PUT /api/me/tokens/{id}/grants` tool مربوط به `tasks_add` را اضافه کنید → در `tools/list` دیده شود و call موفق باشد.  
2. دوباره فقط `notes_list` بگذارید → `tasks_add` رد شود.  
3. افزودن چند MCP با نام یکتا، Sync، و حذف از مسیر `/gw` باید `204` برگرداند.

## ۳. اجرای خودکار

```bash
./scripts/eval_scenarios.sh
```

خروجی موفق:

- `PASS scenario A`
- `PASS scenario B`
- `PASS scenario C`
- `All evaluation scenarios passed.`

سناریو D در تست e2e دستی/اسکریپت کمکی پوشش داده می‌شود.

## ۴. جدول دفاع

| سناریو | تاریخ | نتیجه | مشاهده‌گر |
| --- | --- | --- | --- |
| Auth + gateway build |  | Pass/Fail |  |
| A |  | Pass/Fail |  |
| B |  | Pass/Fail |  |
| C |  | Pass/Fail |  |
| D (ویرایش grant / حذف MCP) |  | Pass/Fail |  |

## ۵. ادعا

این ارزیابی صحت access control سطح tool، فلو کاربرمحور، و امکان ویرایش بعدی allowlist را نشان می‌دهد؛ بنچمارک مقیاس نیست.
