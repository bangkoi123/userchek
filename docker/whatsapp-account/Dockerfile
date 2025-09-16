# Dockerfile untuk WhatsApp Account Container
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps

# Copy application code
COPY . .

# Create directories for sessions and logs
RUN mkdir -p /app/sessions /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV ACCOUNT_ID=""
ENV PROXY_URL=""
ENV PROXY_USERNAME=""
ENV PROXY_PASSWORD=""
ENV MONGO_URL="mongodb://mongo:27017"
ENV MAIN_API_URL="http://main-api:8001"

# Expose port for health checks
EXPOSE 8080

# Run the WhatsApp account service
CMD ["python", "whatsapp_account_service.py"]