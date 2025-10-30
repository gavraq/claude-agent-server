# Claude Agent Server

Home server running Claude Agent SDK with full UFC (Universal File Context) integration, providing WebSocket-based access to Claude with complete access to Gavin's personal context, MCP servers, and specialized sub-agents.

## Architecture

```
Web Browser (Vercel)
    ↓ WebSocket (wss://agent.gavinslater.com/ws)
NGINX Proxy Manager (port 443)
    ↓ Forward to port 8090
Docker Container (claude-agent-server)
    ├── Claude Agent SDK (claude CLI)
    ├── UFC Context (mounted from /home/gavin/projects/life/.claude/context)
    ├── Agent Definitions (mounted from /home/gavin/projects/life/.claude/agents)
    ├── Obsidian Vault (mounted from ~/Library/.../GavinsiCloudVault)
    ├── Documents Storage (mounted from /home/gavin/claude-documents)
    └── MCP Servers (configured via Claude CLI)
```

## Features

- **Full UFC Context**: Complete access to Gavin's profile, goals, active projects, and tools
- **WebSocket Streaming**: Real-time streaming responses from Claude
- **JWT Authentication**: Secure token-based authentication
- **MCP Server Access**: All configured MCP servers available (Gmail, Obsidian, GitHub, etc.)
- **Specialized Sub-Agents**: Access to all 10+ specialized agents
- **Obsidian Integration**: Read/write access to knowledge vault
- **Document Awareness**: Knows about uploaded documents from web interface

## Prerequisites

- Docker and Docker Compose installed on home server
- Node.js 20+ (for local development)
- Claude CLI authenticated (`claude auth login`)
- NGINX Proxy Manager configured

## Quick Start

### 1. Clone and Setup

```bash
cd /home/gavin/projects/life/claude-agent-server
cp .env.example .env
```

### 2. Configure Environment

Edit `.env`:

```bash
JWT_SECRET=<same-secret-as-vercel>
PORT=8090
NODE_ENV=production
```

### 3. Build and Run with Docker

```bash
docker-compose up -d --build
```

### 4. Authenticate Claude CLI

**Important**: You must authenticate Claude CLI inside the container:

```bash
docker exec -it claude-agent-server claude auth login
```

Follow the prompts to authenticate. Credentials will be stored in the `claude-auth` volume.

### 5. Check Health

```bash
curl http://localhost:8090/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-30T...",
  "uptime": 123.45
}
```

## Volume Mounts

The container mounts several directories for full system access:

| Host Path | Container Path | Access | Purpose |
|-----------|----------------|--------|---------|
| `/home/gavin/projects/life/.claude/context` | `/ufc` | Read-only | UFC context files |
| `/home/gavin/projects/life/.claude` | `/claude-config` | Read-only | Agent definitions and commands |
| `/home/gavin/Library/.../GavinsiCloudVault` | `/vault` | Read-write | Obsidian vault |
| `/home/gavin/claude-documents` | `/documents` | Read-write | User uploaded documents |
| `/home/gavin/projects/life` | `/projects` | Read-only | Full project source |
| `claude-auth` (volume) | `/root/.config/claude` | Persistent | Claude CLI credentials |

## NGINX Proxy Manager Configuration

### Create Proxy Host

1. **Domain Names**: `agent.gavinslater.com`
2. **Scheme**: `http`
3. **Forward Hostname / IP**: `localhost` (or container IP)
4. **Forward Port**: `8090`
5. **Websockets Support**: ✅ **ENABLED**
6. **SSL**: Let's Encrypt certificate
7. **Force SSL**: ✅ **ENABLED**

### Custom NGINX Configuration (Advanced)

If needed, add to Custom Locations:

```nginx
location /ws {
    proxy_pass http://localhost:8090;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 86400;
}
```

## WebSocket Protocol

### Connection

Connect to: `wss://agent.gavinslater.com/ws?token=<jwt-token>`

Or use Authorization header: `Bearer <jwt-token>`

### Message Types

#### Client → Server

**Agent Request:**
```json
{
  "type": "agent_request",
  "conversationId": "optional-conversation-id",
  "message": "User's message here",
  "includeUFC": true
}
```

**Ping:**
```json
{
  "type": "ping"
}
```

#### Server → Client

**Connected:**
```json
{
  "type": "connected",
  "connectionId": "conn_xxx",
  "message": "Connected to Claude Agent Server",
  "capabilities": {
    "ufcContext": true,
    "mcpServers": true,
    "obsidianVault": true,
    "specializedAgents": true
  }
}
```

**Processing:**
```json
{
  "type": "agent_processing",
  "conversationId": "...",
  "message": "Processing your request..."
}
```

**Streaming Chunk:**
```json
{
  "type": "agent_chunk",
  "conversationId": "...",
  "chunk": "Partial response text..."
}
```

**Complete:**
```json
{
  "type": "agent_complete",
  "conversationId": "...",
  "fullResponse": "Complete response text"
}
```

**Error:**
```json
{
  "type": "agent_error",
  "conversationId": "...",
  "error": "Error message",
  "exitCode": 1
}
```

**Pong:**
```json
{
  "type": "pong",
  "timestamp": 1234567890
}
```

## Development

### Local Development (without Docker)

```bash
npm install
npm run dev
```

Server will start on `http://localhost:8090`

### Build TypeScript

```bash
npm run build
```

### Lint Code

```bash
npm run lint
```

## Logging

Logs are written to stdout in JSON format (production) or pretty format (development).

View logs:

```bash
docker logs -f claude-agent-server
```

Log levels: `error`, `warn`, `info`, `debug`

Configure via `.env`:
```bash
LOG_LEVEL=info
```

## Monitoring

### Health Check

The container includes a health check that runs every 30 seconds:

```bash
docker ps  # Check HEALTH status
```

### Manual Health Check

```bash
curl http://localhost:8090/health
```

## Security

### JWT Authentication

- All WebSocket connections must provide a valid JWT token
- Tokens are generated by Vercel using the shared `JWT_SECRET`
- Tokens expire after 24 hours (configurable)

### Network Security

- Only port 8090 exposed to NGINX Proxy Manager
- All external access via HTTPS (NGINX terminates SSL)
- Volume mounts are read-only except where write access is required

### Best Practices

1. Keep `JWT_SECRET` secure and synchronized with Vercel
2. Regularly update Docker image and dependencies
3. Monitor logs for suspicious activity
4. Use firewall rules to restrict access to port 8090

## Troubleshooting

### Container won't start

```bash
docker logs claude-agent-server
```

Common issues:
- Missing `JWT_SECRET` in `.env`
- Volume paths don't exist on host
- Port 8090 already in use

### WebSocket connection fails

1. Check NGINX Proxy Manager WebSocket setting is enabled
2. Verify JWT token is valid
3. Check firewall allows port 8090
4. Review container logs

### Claude CLI not authenticated

```bash
docker exec -it claude-agent-server claude auth login
```

### UFC context not loading

1. Verify volume mounts in `docker-compose.yml`
2. Check file permissions on host
3. Review container logs for file access errors

## Updating

### Pull latest code

```bash
cd /home/gavin/projects/life/claude-agent-server
git pull
```

### Rebuild and restart

```bash
docker-compose down
docker-compose up -d --build
```

### Re-authenticate Claude CLI (if needed)

```bash
docker exec -it claude-agent-server claude auth login
```

## Integration with Vercel

The Vercel chat API needs to be updated to support agent routing. See the next phase of implementation for details.

## License

MIT

## Support

For issues or questions, contact Gavin Slater.
