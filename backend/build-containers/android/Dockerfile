FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv git zip unzip openjdk-17-jdk \
    autoconf automake libtool pkg-config zlib1g-dev libncurses5-dev \
    libncurses5 cmake libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir buildozer==1.5.0 cython==0.29.36

WORKDIR /build
RUN mkdir -p /output /scripts

COPY scripts/build_android.sh /scripts/build_android.sh
RUN chmod +x /scripts/build_android.sh
