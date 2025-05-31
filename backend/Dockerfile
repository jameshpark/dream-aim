FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-traditional \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pipenv
RUN pip install pipenv

# Copy Pipfile and Pipfile.lock
COPY Pipfile Pipfile.lock ./

# Install dependencies
RUN pipenv install --deploy --system

# Create a non-root user
RUN useradd -m appuser

# Copy the rest of the application
COPY . .

RUN chown -R appuser:appuser /app

# Set environment variables
ENV PYTHONPATH=/app
ENV DATABASE_URL=postgresql://postgres:postgres@db/dream_aim

# Expose the port
EXPOSE 8000

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the database initialization and then the FastAPI server
CMD ["bash", "-c", "python init_database.py && python run.py"]
