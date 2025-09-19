FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ZEYREK_CACHE_DIR=/srv/.zeyrek_cache
WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cache klasörü — imaj içinde hazır dursun
RUN mkdir -p ${ZEYREK_CACHE_DIR}

COPY app.py /srv/app.py

RUN python - <<'PY'\n\
    import os, zeyrek\n\
    os.makedirs(os.environ.get("ZEYREK_CACHE_DIR","/srv/.zeyrek_cache"), exist_ok=True)\n\
    a = zeyrek.MorphAnalyzer()\n\
    a.lemmatize("deneme")\n\
    print("Zeyrek warmup at build time: OK")\n\
    PY

EXPOSE 8077
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8077","--no-server-header"]
