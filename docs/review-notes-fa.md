# نتیجهٔ بازبینی مستندات

## سیاست اصطلاحات
متن فارسی است؛ اصطلاحات فنی انگلیسی می‌مانند  
(`MCP`, `Gateway`, `endpoint`, `platform token`, `allowlist`, `grant`, `sync`, `upstream`, `tools/list`, `tools/call`, ...).

## هم‌خوانی با سامانه فعلی

اسناد برای این فلو به‌روز شده‌اند:

1. login با username/password  
2. نقش admin / user  
3. صفحهٔ Gateway من: ساخت + ویرایش toolها (کم/زیاد کردن allowlist)  
4. تفکیک session token و platform token  
5. کاتالوگ MCP: چند سرور با نام یکتا، Sync، حذف  
6. proxy `/gw` (CORS + عبور درست پاسخ `204`)  
7. demo-mcp از نوع notes/tasks  
8. ارزیابی خودکار A/B/C؛ سناریوی ویرایش grant / حذف MCP به‌صورت دستی در دمو  

فایل‌های اصلی به‌روزشده:

- `README.md`
- `docs/user-guide-fa.md`
- `docs/architecture-fa.md`
- `docs/api-reference-fa.md`
- `docs/evaluation-fa.md`
- `docs/defense-script-fa.md`
- `docs/faq-defense-fa.md`
- `docs/env-and-run-fa.md`
- `docs/thesis-outline-fa.md`
- بخش‌های کلیدی `docs/article-fa.md`

## حکم

پس از هم‌تراز کردن FAQ با اسکریپت ارزیابی، اصلاح NFR5/FR11، و شفاف‌سازی `auth_header` به‌عنوان مقدار `Authorization` upstream، README و docs با کد فعلی هم‌خوان‌اند. قبل از دفاع یک‌بار `./scripts/eval_scenarios.sh` را اجرا کنید.
