# Symphony Orchestrator
# Based on openai/symphony Elixir reference implementation

FROM elixir:1.17-otp-27-alpine AS build

RUN apk add --no-cache git build-base openssh-client

WORKDIR /app

# Clone Symphony reference implementation
RUN git clone --depth 1 https://github.com/openai/symphony.git /app

WORKDIR /app/elixir

# Install Elixir dependencies
RUN mix local.hex --force && \
    mix local.rebar --force && \
    MIX_ENV=prod mix deps.get && \
    MIX_ENV=prod mix compile

# Runtime stage
FROM elixir:1.17-otp-27-alpine AS runtime

RUN apk add --no-cache git openssh-client bash curl

WORKDIR /app

COPY --from=build /app/elixir /app

# Install runtime hex/rebar
RUN mix local.hex --force && mix local.rebar --force

# Setup entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
