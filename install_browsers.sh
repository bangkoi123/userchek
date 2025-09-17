#!/bin/bash
# WhatsApp Browser Setup for Production

echo "🌐 Installing Playwright browsers for WhatsApp automation..."

# Install Playwright browsers
pip install playwright
playwright install chromium

# Install system dependencies
apt-get update
apt-get install -y \
    libnss3-dev \
    libatk-bridge2.0-dev \
    libdrm-dev \
    libxcomposite-dev \
    libxdamage-dev \
    libxrandr-dev \
    libgbm-dev \
    libxss-dev \
    libasound2-dev

# Create browser session directory
mkdir -p /app/data/whatsapp_sessions
chmod 755 /app/data/whatsapp_sessions

echo "✅ Browser setup complete for WhatsApp automation"