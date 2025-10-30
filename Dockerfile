FROM node:20-slim

# Install dependencies (including Python for daily-brief-system)
RUN apt-get update && apt-get install -y \
    curl \
    git \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Claude CLI globally
RUN npm install -g @anthropic-ai/claude-sdk

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install application dependencies
RUN npm ci --only=production

# Copy application source
COPY . .

# Install daily-brief-system Python dependencies
RUN pip3 install --break-system-packages -r daily-brief-system/requirements.txt

# Build TypeScript
RUN npm run build

# Expose WebSocket port
EXPOSE 8090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:8090/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1))"

# Run the server
CMD ["node", "dist/server.js"]
