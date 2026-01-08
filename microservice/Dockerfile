FROM python:3.13-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:0.9.22 /uv /uvx /bin/


WORKDIR /app
COPY pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project

COPY . /app/

EXPOSE 5000
CMD ["uv", "run", "app.py"]