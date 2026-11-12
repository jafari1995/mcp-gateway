# متغیرهای محیطی و اجرا

## Docker Compose

```bash
docker compose up --build
```

### backend

| متغیر | پیش‌فرض | نقش |
| --- | --- | --- |
| `ADMIN_USERNAME` | `admin` | نام کاربری ادمین seed‌شده |
| `ADMIN_API_KEY` | `dev-admin-key` | رمز اولیه ادمین |
| `DATABASE_URL` | `sqlite:///./data/gateway_v2.db` | مسیر DB |
| `CORS_ORIGINS` | شامل 3000/3001 | برای دسترسی مستقیم به API |
| `DEMO_MCP_URL` | `http://demo-mcp:8100/mcp` | آدرس داخلی demo |

### frontend

| متغیر | پیش‌فرض | نقش |
| --- | --- | --- |
| `INTERNAL_API_URL` | `http://backend:8000` | مقصد proxy داخل کانتینر |
| `NEXT_PUBLIC_API_BASE` | `/gw` | پایهٔ درخواست‌های مرورگر |

## اجرای محلی بدون Docker

Backend:

```bash
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install .
mkdir -p data
uvicorn app.main:app --reload --port 8000
```

demo-mcp:

```bash
cd demo-mcp && python3 -m venv .venv && source .venv/bin/activate
pip install .
python -m demo_mcp.server
```

Frontend:

```bash
cd frontend
INTERNAL_API_URL=http://127.0.0.1:8000 npm run dev
```

UI را از آدرس Next باز کنید و login کنید.

## پاک‌سازی DB

```bash
docker compose down -v
```
