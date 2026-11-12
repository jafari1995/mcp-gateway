# معماری سامانهٔ MCP Gateway

## ۱. هدف

یک endpoint واحد برای AI clientها، با access control در سطح tool، و هویت جدا برای ادمین/کاربر داشبورد.

ایدهٔ مرکزی:

> login کاربر → انتخاب tool از کاتالوگ → platform token → `/mcp` فقط toolهای مجاز

## ۲. اجزا

| جزء | مسیر | مسئولیت |
| --- | --- | --- |
| Backend | `backend/` | Auth session، کاتالوگ MCP، grant، پروکسی MCP |
| Frontend | `frontend/` | UI فارسی/RTL + proxy `/gw` |
| Demo MCP | `demo-mcp/` | upstream نمونه notes/tasks |
| Database | SQLite (`gateway_v2.db`) | کاربران، session hash، سرورها، toolها، grants |

## ۳. دو سطح credential

| نوع | مصرف | Header |
| --- | --- | --- |
| Session token (`sess_...`) | داشبورد وب بعد از login | `Authorization: Bearer sess_...` |
| Platform token (`mcpgw_...`) | کلاینت AI برای `/mcp` | `Authorization: Bearer mcpgw_...` |

Session برای مدیریت است؛ platform token برای اجرای tool.

## ۴. نقش‌ها

### Admin
- ساخت کاربر با username/password  
- ثبت چند سرور MCP با نام یکتا، Sync و حذف  
- مشاهده همه  

### User
- login با رمز خودش  
- دیدن کاتالوگ  
- ساخت Gateway شخصی (انتخاب tool + صدور platform token)  
- ویرایش بعدی allowlist همان token (کم/زیاد کردن tool بدون تعویض token)  
- ابطال tokenهای خودش  

## ۵. دیاگرام

```text
Admin UI / User UI (Next.js, /gw proxy)
        |  Bearer sess_...
        v
FastAPI Control Plane (/api/*)
        |                      \
   SQLite users/servers/tools   \
                                 \
AI Client ------------------------> /mcp  (Bearer mcpgw_...)
                                      |
                                 allowlist policy
                                      |
                                      v
                                 upstream MCP (demo-mcp)
```

## ۶. مدل داده

- `User`: username, password_hash, role, session_token_hash  
- `Token`: platform token هر کاربر (فقط hash در DB)  
- `McpServer`: کاتالوگ upstream  
- `Tool`: toolهای sync‌شده  
- `TokenToolGrant`: allowlist هر platform token  

## ۷. جریان ساخت و ویرایش Gateway کاربر

### ساخت
1. کاربر login می‌کند  
2. `GET /api/catalog/tools`  
3. toolها را انتخاب می‌کند  
4. `POST /api/me/gateway` با `tool_ids`  
5. platform token یک‌بار برمی‌گردد  
6. کلاینت با آن token به `/mcp` وصل می‌شود  

### ویرایش allowlist
1. `GET /api/me/tokens/{id}/grants` وضعیت فعلی را می‌آورد  
2. کاربر toolها را کم/زیاد می‌کند  
3. `PUT /api/me/tokens/{id}/grants` با `tool_ids` جدید  
4. خودِ platform token عوض نمی‌شود؛ از `tools/list` بعدی مجموعهٔ جدید دیده می‌شود  
5. token باطل‌شده قابل ویرایش نیست؛ حداقل یک tool لازم است  

## ۸. سیاست `/mcp`

1. Bearer platform token  
2. hash و یافتن token فعال  
3. `tools/list` → فقط grant شده‌ها  
4. `tools/call` → اگر grant نباشد رد می‌شود؛ وگرنه پروکسی به upstream  

## ۹. پروتکل و هدرها (تعمداً محدود)

سامانه دو مسیر جدا دارد؛ نیاز هدر/پروتکل در هر مسیر فرق می‌کند.

| مسیر | پروتکل در این نسخه | هدر |
| --- | --- | --- |
| کلاینت AI → Gateway (`/mcp`) | فقط HTTP + JSON-RPC به‌صورت remote / streamable-http | فقط `Authorization: Bearer mcpgw_...` |
| Gateway → upstream MCP | همان remote HTTP | اختیاری: `auth_header` = مقدار هدر `Authorization` به upstream |

**چرا کلاینت را ساده نگه داشتیم؟**  
ارزش محصول در allowlist و platform token است، نه سوپرمارکت transport. پشتیبانی هم‌زمان از stdio، چند نسخهٔ SSE، و UI پیچیده برای هدرهای دلخواه روی هر اتصال کلاینت، برای پایان‌نامه و دمو اضافه است و پیچیدگی دفاع را بالا می‌برد.

**چرا هدر upstream داخل محدوده است؟**  
بسیاری از MCPهای عمومی/hosted برای Sync و call به API key یا Bearer جدا نیاز دارند. بدون `auth_header`، ادمین نمی‌تواند همان سرورها را به کاتالوگ اضافه کند. مقدار هدر فقط سمت Gateway به upstream فرستاده می‌شود؛ به کلاینت AI لو نمی‌رود و در پاسخ لیست سرورها هم برنمی‌گردد.

**خارج از محدودهٔ این نسخه:** multi-transport کامل (مثل میزبانی stdio داخل Gateway)، OAuth سازمانی برای کلاینت، و ویرایشگر عمومی «هر هدر دلخواه» روی اتصال کلاینت.

## ۱۰. نکات پیاده‌سازی مهم

- UI از `/gw` به backend پروکسی می‌کند تا CORS اذیت نکند  
- proxy برای statusهای `204/205/304` بدنه نمی‌فرستد (وگرنه حذف سرور در UI می‌ترکید)  
- هنگام به‌روزرسانی grantها ابتدا رکوردهای قبلی حذف و `flush` می‌شوند تا UNIQUE نقض نشود  
- demo-mcp برای Docker، DNS-rebinding سخت‌گیرانه را خاموش/مجاز کرده تا Host مربوط به `demo-mcp` کار کند  
- ادمین اولیه در startup با `ADMIN_USERNAME` / `ADMIN_API_KEY` seed می‌شود  
- هنگام ثبت MCP، فیلد اختیاری `auth_header` مقدار کامل هدر `Authorization` سمت upstream است (مثلاً `Bearer sk-...`)؛ نام هدر جداگانه پشتیبانی نمی‌شود
