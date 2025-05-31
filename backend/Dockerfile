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

# Create a wait-for-it script to ensure the database is ready
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
host="$1"\n\
port="$2"\n\
shift 2\n\
cmd="$@"\n\
\n\
until nc -z "$host" "$port"; do\n\
  >&2 echo "Waiting for $host:$port..."\n\
  sleep 1\n\
done\n\
\n\
>&2 echo "$host:$port is available"\n\
\n\
exec $cmd' > /app/wait-for-it.sh

# Create a script to initialize the database and start the server
RUN echo '#!/bin/bash\n\
echo "Checking database..."\n\
python init_database.py\n\
echo "Starting server..."\n\
exec python run.py' > /app/start.sh

RUN chmod +x /app/wait-for-it.sh /app/start.sh
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

# Run the wait-for-it script and then the start script
CMD ["/bin/bash", "-c", "/app/wait-for-it.sh db 5432 /app/start.sh"]
