FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir uv && uv pip install --system -e ".[dev]"
COPY vhir_adapter_ezyvet/ vhir_adapter_ezyvet/

EXPOSE 8001
CMD ["uvicorn", "vhir_adapter_ezyvet.app:app", "--host", "0.0.0.0", "--port", "8001"]
