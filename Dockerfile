FROM python:3.12-slim AS build

LABEL org.opencontainers.image.source=https://github.com/genomicmedlab/anyvlm
LABEL org.opencontainers.image.description="AnyVLM container image"
LABEL org.opencontainers.image.licenses=Apache-2.0

ARG ANYVLM_VERSION
RUN echo "Building AnyVLM version: ${ANYVLM_VERSION}"
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_ANYVLM=${ANYVLM_VERSION}

RUN apt-get update && \
    apt-get install -y libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
COPY src ./src

RUN pip install --upgrade pip setuptools setuptools_scm
RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "anyvlm.main:app", "--host", "0.0.0.0", "--port", "8000"]
