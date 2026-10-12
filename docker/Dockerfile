FROM node@sha256:2c87ef9bd3c6a3bd4b472b4bec2ce9d16354b0c574f736c476489d09f560a203 AS node
FROM python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f AS tools
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
 && apt-get update && apt-get install -y --no-install-recommends git curl ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir pytest==8.3.5 PyYAML==6.0.2 \
 && mkdir /workspace /opt/ihb && useradd -u 10001 -m bench
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOME=/home/bench
WORKDIR /workspace
FROM tools AS agent
RUN npm install --prefix /opt/openclaw --omit=dev openclaw@2026.9.7 \
 && ln -s /opt/openclaw/node_modules/.bin/openclaw /usr/local/bin/openclaw \
 && npm cache clean --force
COPY runtime/agent.py /opt/ihb/agent.py
USER 10001:10001
CMD ["python", "/opt/ihb/agent.py"]
FROM tools AS relay
COPY runtime/relay.py /opt/ihb/relay.py
COPY bench/rotation.py /opt/ihb/bench/rotation.py
COPY bench/__init__.py /opt/ihb/bench/__init__.py
ENV PYTHONPATH=/opt/ihb
USER 10001:10001
CMD ["python", "/opt/ihb/relay.py"]
FROM tools AS helper
COPY runtime/mock_api.py /opt/ihb/mock_api.py
USER 10001:10001
CMD ["python", "/opt/ihb/mock_api.py"]
FROM tools AS grader
COPY private_tasks /opt/ihb/tasks
COPY runtime/grader.py /opt/ihb/grader.py
COPY validation /opt/ihb/validation
USER 10001:10001
CMD ["python", "/opt/ihb/grader.py"]
