# MCP Gateway

دروازهٔ مینیمال برای Model Context Protocol (MCP): ادمین کاتالوگ MCP را مدیریت می‌کند، کاربر با username/password وارد می‌شود، از لیست tool انتخاب می‌کند، platform token می‌گیرد، و کلاینت AI فقط همان toolها را از یک endpoint می‌بیند.

پروژه برای پایان‌نامه کارشناسی به‌صورت greenfield پیاده‌سازی شده است.

## مسئله

اتصال مستقیم کلاینت‌های AI به چند MCP server پراکنده است و معمولاً access control در سطح tool وجود ندارد.

## راه‌حل

1. ادمین هر تعداد MCP را با نام یکتا ثبت، sync یا حذف می‌کند  
2. ادمین کاربر با username/password می‌سازد  
3. کاربر وارد می‌شود و در «Gateway من» toolها را انتخاب می‌کند  
4. platform token صادر می‌شود؛ بعداً می‌تواند همان Gateway را ویرایش و toolها را کم/زیاد کند  
5. کلاینت فقط با همان token به `/mcp` وصل می‌شود و فقط toolهای مجاز را می‌بیند  

## اجزا

| مسیر | نقش |
| --- | --- |
| `backend/` | Auth کاربر، کاتالوگ MCP، allowlist، پروکسی `/mcp` |
| `frontend/` | UI فارسی/RTL + login + Gateway من |
| `demo-mcp/` | upstream نمونه (notes + tasks) |
| `docs/` | مستندات دفاع |
| `scripts/` | ارزیابی خودکار |

## اجرای سریع

```bash
docker compose up --build
```

| سرویس | آدرس |
| --- | --- |
| UI | http://localhost:3001 |
| Gateway / MCP | http://localhost:8000 |
| demo-mcp | http://localhost:8100/mcp |

ورود ادمین پیش‌فرض: `admin` / `dev-admin-key`

### فلو دمو

1. ورود ادمین  
2. کاتالوگ MCP → افزودن `demo-mcp` (یا MCP دیگر با نام یکتا) → Sync  
3. کاربران → ساخت کاربر با username/password  
4. خروج و ورود با همان کاربر  
5. Gateway من → انتخاب toolها → ساخت token  
6. در صورت نیاز: «ویرایش toolها» روی همان token برای کم/زیاد کردن allowlist  
7. اتصال کلاینت به `http://localhost:8000/mcp` با Bearer token  

راهنما: [`docs/user-guide-fa.md`](docs/user-guide-fa.md)  
فهرست اسناد: [`docs/INDEX.md`](docs/INDEX.md)

## ارزیابی

```bash
./scripts/eval_scenarios.sh
```

سناریوها: فقط `notes_list` در list دیده شود؛ `tasks_add` رد شود؛ `notes_list` اجرا شود.

## خارج از محدوده

چند transport هم‌زمان برای کلاینت (مثل stdio)، OAuth سازمانی کامل، Kubernetes، audit سازمانی سنگین، rate limiting پیشرفته.

هدر احراز **upstream** (`auth_header`) داخل محدوده است؛ خیلی از MCPهای عمومی برای Sync به API key نیاز دارند. جزئیات: [`docs/architecture-fa.md`](docs/architecture-fa.md).
