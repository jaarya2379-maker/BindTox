FROM python:3.11-slim

WORKDIR /app

# Install system deps for common packages (adjust if Vina or RDKit are needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy sources
COPY pyproject.toml requirements.txt /app/
COPY src /app/src
COPY streamlit_app.py /app/streamlit_app.py
COPY start_app.sh /app/start_app.sh

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 8000 8501

CMD ["/bin/sh", "-c", "PYTHONPATH=src uvicorn bindtox.backend_api:app --host 0.0.0.0 --port 8000"]
