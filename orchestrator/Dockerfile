FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# System dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    jq \
    openssh-client \
    python3 \
    python3-pip \
    unzip \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# JDK 17
RUN apt-get update && apt-get install -y openjdk-17-jdk-headless \
    && rm -rf /var/lib/apt/lists/*

# Gradle 8.7
RUN curl -fsSL https://services.gradle.org/distributions/gradle-8.7-bin.zip -o /tmp/gradle.zip \
    && unzip /tmp/gradle.zip -d /opt && rm /tmp/gradle.zip \
    && ln -s /opt/gradle-8.7/bin/gradle /usr/local/bin/gradle

# gh CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

# Copilot CLI (installed globally via npm)
# The exact package may change — this installs the GitHub Copilot CLI agent
RUN npm install -g @githubnext/github-copilot-cli 2>/dev/null || true

# Python orchestrator dependencies
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Playwright + Chromium for web screenshots
RUN pip3 install playwright \
    && python3 -m playwright install chromium \
    && python3 -m playwright install-deps chromium

# Copy orchestrator source
COPY . /app
WORKDIR /app

# Create workspace directory
RUN mkdir -p /workspaces

# Git config for agent commits + HTTPS token auth
RUN git config --global user.name "Nibble Agent" \
    && git config --global user.email "agent@nibble.dev" \
    && git config --global init.defaultBranch main

# Entrypoint script to configure git HTTPS auth from GITHUB_TOKEN
RUN printf '#!/bin/bash\n\
# Configure git to use GITHUB_TOKEN for HTTPS clones\n\
if [ -n "$GITHUB_TOKEN" ]; then\n\
  git config --global url."https://${GITHUB_TOKEN}@github.com/".insteadOf "https://github.com/"\n\
  echo "$GITHUB_TOKEN" | gh auth login --with-token 2>/dev/null || true\n\
fi\n\
exec "$@"\n' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["python3", "orchestrator.py"]
