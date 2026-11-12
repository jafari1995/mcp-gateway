FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY demo_mcp ./demo_mcp
RUN pip install --no-cache-dir .
EXPOSE 8100
CMD ["python", "-m", "demo_mcp.server"]
