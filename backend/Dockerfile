# Contexte de build : la racine du dépôt (voir docker-compose.yml).
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

ENV HF_HOME=/app/hf_cache \
    GOVIA_EMBED_MODEL=paraphrase-multilingual-MiniLM-L12-v2

WORKDIR /app/backend

# PyTorch CPU : une image bien plus légère, suffisante pour les embeddings.
COPY backend/requirements.txt .
# Délais longs : ces paquets sont lourds sur une connexion lente. Couches séparées pour
# ne pas tout retélécharger après une coupure.
RUN pip install --no-cache-dir --default-timeout=300 --retries 10 torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --default-timeout=300 --retries 10 -r requirements.txt

# Le modèle d'embeddings est embarqué à la construction : aucune donnée de requête
# ne passe par un service externe, et le démarrage fonctionne hors ligne.
RUN python -c "import os; from sentence_transformers import SentenceTransformer; SentenceTransformer(os.environ['GOVIA_EMBED_MODEL'])"

COPY backend/ /app/backend/
COPY knowledge_base/ /app/knowledge_base/

RUN useradd --system --uid 1001 govia \
    && mkdir -p /app/chroma_db /app/logs \
    && chown -R govia /app/chroma_db /app/logs /app/hf_cache
USER govia

ENV HF_HUB_OFFLINE=1 ANONYMIZED_TELEMETRY=False
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
