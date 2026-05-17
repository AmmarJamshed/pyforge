FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pyinstaller==6.11.1

WORKDIR /build
RUN mkdir -p /output /scripts

COPY scripts/build_desktop.sh /scripts/build_desktop.sh
RUN chmod +x /scripts/build_desktop.sh

ENV PYTHONUNBUFFERED=1
