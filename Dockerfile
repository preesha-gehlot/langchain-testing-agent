FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything else
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/google_application_credentials.json
ENV LOG_LEVEL=INFO
ENV PORT=8080

# Create necessary directories
RUN mkdir -p /app/downloads /app/artifacts

# Make everything executable
RUN chmod -R 755 /app

EXPOSE 8080

# Start the FastAPI application
CMD ["sh", "-c", "cd /app && echo 'Current dir:' && pwd && echo 'Files:' && ls -la && echo 'Starting app...' && uvicorn main:app --host 0.0.0.0 --port 8080"]