FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir uv && uv pip install --system -e ".[dev]"
COPY vhir_server/ vhir_server/

EXPOSE 8000
CMD ["uvicorn", "vhir_server.main:app", "--host", "0.0.0.0", "--port", "8000"]
