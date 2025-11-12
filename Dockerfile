FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Install python3, scraper dependencies, and browser runtime
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-requests \
    py3-beautifulsoup4 \
    py3-pandas \
    py3-numpy \
    py3-lxml \
    py3-openpyxl \
    chromium \
    chromium-chromedriver \
    nss \
    harfbuzz \
    freetype \
    ttf-freefont

# Copy package files
COPY package*.json ./

# Install only production dependencies
RUN npm ci --only=production && npm cache clean --force

# Set up Python virtual environment for scraper dependencies
COPY --from=builder /app/requirements.txt ./
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy built application and required scripts from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/scheduler.js ./
COPY --from=builder /app/scraper_marketplace_url.py ./
COPY --from=builder /app/start.sh ./

# Ensure startup script is executable
RUN chmod +x /app/start.sh

# Create public directory if it doesn't exist
RUN mkdir -p public

# Expose port 3000
EXPOSE 3000

# Environment variables for Selenium Chromium
ENV CHROME_BINARY=/usr/bin/chromium-browser \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHON_BIN=/opt/venv/bin/python

# Start scheduler and Next.js server
CMD ["/bin/sh", "/app/start.sh"]
