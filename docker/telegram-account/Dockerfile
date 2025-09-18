# Telegram Account Isolation Container
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN useradd -m -u 1000 telegram_user

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY telegram_validator.py .
COPY telegram_mtp_validator.py .

# Create directories with proper permissions
RUN mkdir -p /app/sessions /app/data /app/logs && \
    chown -R telegram_user:telegram_user /app

# Switch to non-root user
USER telegram_user

# Expose port for health checks
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start the validator service
CMD ["python", "telegram_validator.py"]