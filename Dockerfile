# ============================================================
# HepaTwin Backend — Dockerfile untuk deployment Koyeb.
#
# - Python 3.11-slim (runtime minimal).
# - PyTorch CPU-only via requirements-koyeb.txt
#   (--extra-index-url https://download.pytorch.org/whl/cpu) —
#   optimal untuk Micro Instance Koyeb (512 MB RAM).
# - Aplikasi listen di 0.0.0.0:8000 (Koyeb default HTTP port 8000;
#   pastikan exposed port service = 8000).
# ============================================================
FROM python:3.11-slim

# libgomp1: wheel RDKit membutuhkan OpenMP runtime (libgomp.so.1)
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependency manifests + paket ml (dibutuhkan oleh `-e ./ml`)
COPY requirements-koyeb.txt ./
COPY ml ./ml
RUN pip install --no-cache-dir -r requirements-koyeb.txt

# Source aplikasi (termasuk artefak model app/models/*.pt, metadata,
# dan kalibrator) + Procfile sebagai referensi start command.
COPY app ./app
COPY Procfile ./

# Default produksi (bisa di-override lewat Koyeb Service Variables)
ENV AI_MODEL_PATH=app/models/model_gatnn_dnn.pt
ENV DEBUG=False

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
