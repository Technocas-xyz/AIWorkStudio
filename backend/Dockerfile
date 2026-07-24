FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    postgresql-client \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create upload directories
RUN mkdir -p app/uploads/originals app/uploads/previews app/uploads/versions app/uploads/generations

# Make scripts executable
RUN chmod +x scripts/start.sh

# Expose port
EXPOSE 8000

# Run application with startup script
CMD ["bash", "scripts/start.sh"]
