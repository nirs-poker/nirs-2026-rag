FROM node:24-bookworm-slim@sha256:873f586f3794f52281bd039bf02c048a0be08fde619338f9941bad1eb6b34530 AS frontend
WORKDIR /build
COPY code/client/package*.json ./
RUN npm ci
COPY code/client/ ./
COPY code/ports.json /ports.json
RUN npm run build

FROM almalinux:8.10@sha256:768bedc30fe0a536adb0a65d2eddb7caad364e514fbddd0ae9e026975f590342
ARG PYTHON_VERSION=3.14.6
ARG PASSENGER_VERSION=6.2.0
RUN dnf install -y gcc gcc-c++ make curl tar xz openssl-devel bzip2-devel \
    libffi-devel zlib-devel readline-devel sqlite-devel libuuid-devel \
    httpd httpd-devel ruby ruby-devel rubygems libcurl-devel redhat-rpm-config \
    && dnf clean all
# Build the hosting's Python version against AlmaLinux libraries.
RUN curl -fsSL "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz" -o /tmp/python.tar.xz \
    && tar -xJf /tmp/python.tar.xz -C /tmp \
    && cd "/tmp/Python-${PYTHON_VERSION}" \
    && ./configure --prefix=/opt/python --with-ensurepip=install \
    && make -j2 && make install \
    && rm -rf /tmp/Python-* /tmp/python.tar.xz
RUN for spec in rack-2.2.17 rackup-1.0.1 rake-13.0.6 logger-1.7.0 passenger-${PASSENGER_VERSION}; do \
        curl --retry 3 --connect-timeout 15 --max-time 120 -fsSL "https://rubygems.org/downloads/${spec}.gem" -o "/tmp/${spec}.gem"; \
    done \
    && gem install /tmp/*.gem --local --ignore-dependencies --no-document \
    && rm /tmp/*.gem \
    && passenger-install-apache2-module --auto --languages python \
    && passenger-config --root > /tmp/passenger-root \
    && ruby -e 'root = File.read("/tmp/passenger-root").strip; puts "LoadModule passenger_module #{root}/buildout/apache2/mod_passenger.so\nPassengerRoot #{root}\nPassengerPython /opt/python/bin/python3"' > /etc/httpd/conf.modules.d/10-passenger.conf
RUN useradd --create-home app \
    && /opt/python/bin/python3 -m venv /home/app/poker-trainer-venv \
    && mkdir -p /app/public /app/tmp /run/httpd \
    && chown -R app:app /home/app /app
ENV PATH="/home/app/poker-trainer-venv/bin:/opt/python/bin:${PATH}" POKER_APP_ROOT=/app
WORKDIR /app
COPY --chown=app:app code/server/requirements.txt code/server/requirements.txt
RUN python3 -m pip install --no-cache-dir -r code/server/requirements.txt
COPY --chown=app:app code/server/ code/server/
COPY --chown=app:app passenger_wsgi.py ./
COPY --chown=app:app code/ports.json code/ports.json
COPY --from=frontend --chown=app:app /build/dist/ code/client/dist/
COPY docker/httpd.conf /etc/httpd/conf.d/poker.conf
EXPOSE 80
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s CMD curl -fsS http://127.0.0.1/api/health || exit 1
CMD ["/usr/sbin/httpd", "-DFOREGROUND"]
