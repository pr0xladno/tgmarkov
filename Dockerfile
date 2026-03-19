# Use the official uv image with Python 3.12
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set working directory
WORKDIR /app

# Copy pyproject.toml
COPY pyproject.toml ./

# Export dependencies to requirements.txt and install
RUN uv export --format requirements-txt --output-file requirements.txt && \
    uv pip install --system --no-cache-dir -r requirements.txt && \
    rm requirements.txt

# Copy the rest of the application
COPY . .

# Command to run the application
CMD ["python", "main.py"]