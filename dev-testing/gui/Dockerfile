FROM python:3.11

ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        xvfb \
        x11vnc \
        fluxbox \
        supervisor \
        novnc \
        websockify \
        libsdl2-dev \
        libsdl2-image-dev \
        libsdl2-mixer-dev \
        libsdl2-ttf-dev \
        libsdl2-gfx-dev \
        fonts-dejavu-core \
        curl \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY dev-testing/gui/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dev-testing/gui/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY dev-testing/gui/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN mkdir -p /var/log/supervisor

EXPOSE 5900 6080

ENTRYPOINT ["/entrypoint.sh"]
