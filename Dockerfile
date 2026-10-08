FROM python:3.12-slim
WORKDIR /srv/app
COPY pyproject.toml ./
COPY rag ./rag
COPY app ./app
COPY scripts ./scripts
COPY data ./data
RUN pip install --no-cache-dir .
ENV RAG_STORAGE=/srv/app/storage
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
