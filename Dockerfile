FROM python:3.11-slim

LABEL maintainer="AdaptNXT Technology Solutions <queries@adaptnxt.com>"
LABEL description="Industrial Modbus-to-MQTT Telemetry Encoder & Edge Buffer"
LABEL org.opencontainers.image.source="https://github.com/adaptnxt/modbus-mqtt-telemetry-encoder"

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY examples/ ./examples/

RUN pip install --no-cache-dir -e .

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["adaptnxt-telemetry"]
CMD ["demo"]
