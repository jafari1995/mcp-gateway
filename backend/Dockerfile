FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir . && mkdir -p /app/data
EXPOSE 8000
ENV DATABASE_URL=sqlite:///./data/gateway.db
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
