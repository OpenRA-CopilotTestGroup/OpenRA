FROM ubuntu:22.04

# 安装基础依赖（如有 .NET 依赖可在此补充）
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libx11-6 \
    libxrender1 \
    libxi6 \
    libxcursor1 \
    libxrandr2 \
    libxtst6 \
    libnss3 \
    libasound2 \
    libpulse0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN chmod +x run.sh
ENTRYPOINT ["./run.sh"]

