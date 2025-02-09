FROM python:3.12-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container.
COPY . /app

# Install the application dependencies.
WORKDIR /app
# RUN uv sync 
RUN uv sync --frozen --no-cache

# Run the application.
# CMD ["uv", "run", "fastapi", "run", "--port", "80", "--host", "0.0.0.0"]