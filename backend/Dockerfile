FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create models directory
RUN mkdir -p models

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Copy and set executable startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Health check - use PORT environment variable or default to 8000
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests, os; requests.get(f'http://localhost:{os.environ.get(\"PORT\", \"8000\")}/health')" || exit 1

# Run the application using startup script
CMD ["/app/start.sh"]