# The prober, in the smallest image that can run it.
FROM ghcr.io/astral-sh/uv:0.12 AS uv

FROM python:3.14-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

COPY --from=uv /uv /uvx /bin/

WORKDIR /app

# Dependencies first, so a source change does not rebuild them.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# Never run as root: the prober only needs to talk to the network.
RUN useradd --create-home --uid 10001 anden9 \
    && chown -R anden9:anden9 /app
USER anden9

ENTRYPOINT ["anden9"]
CMD ["run", "--catalog", "full"]
