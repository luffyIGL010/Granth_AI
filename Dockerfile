FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HF_HOME=/app/.hf_cache
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt


RUN pip install --force-reinstall --no-deps torch torchvision \
    --index-url https://download.pytorch.org/whl/cpu

# sanity check: yahan fail hua to turant pata chal jayega
RUN python -c "import torch, torchvision; print(torch.__version__, torchvision.__version__)"



RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"

COPY *.py index_manifest.json ./
COPY documents ./documents
COPY videos ./videos
COPY chroma_db ./chroma_db
COPY cache ./cache

EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]