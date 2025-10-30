import { WebSocketServer, WebSocket } from 'ws';
import express from 'express';
import { createServer } from 'http';
import dotenv from 'dotenv';
import { logger } from './logger';
import { authenticateConnection } from './auth-middleware';
import { handleAgentRequest } from './agent-handler';

dotenv.config();

const app = express();
const server = createServer(app);
const wss = new WebSocketServer({ server, path: '/ws' });

const PORT = process.env.PORT || 8090;

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// Connection tracking
const connections = new Map<string, WebSocket>();

wss.on('connection', async (ws: WebSocket, req) => {
  const connectionId = `conn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  logger.info(`New WebSocket connection: ${connectionId}`);

  // Authenticate the connection
  const authResult = await authenticateConnection(req);

  if (!authResult.authenticated) {
    logger.warn(`Authentication failed for ${connectionId}: ${authResult.error}`);
    ws.send(JSON.stringify({
      type: 'error',
      error: 'Authentication failed',
      details: authResult.error
    }));
    ws.close();
    return;
  }

  logger.info(`Connection ${connectionId} authenticated for user: ${authResult.userId}`);
  connections.set(connectionId, ws);

  // Send welcome message
  ws.send(JSON.stringify({
    type: 'connected',
    connectionId,
    message: 'Connected to Claude Agent Server',
    capabilities: {
      ufcContext: true,
      mcpServers: true,
      obsidianVault: true,
      specializedAgents: true
    }
  }));

  ws.on('message', async (data: Buffer) => {
    try {
      const message = JSON.parse(data.toString());
      logger.info(`Received message from ${connectionId}:`, { type: message.type });

      if (message.type === 'agent_request') {
        await handleAgentRequest(
          ws,
          connectionId,
          authResult.userId!,
          message
        );
      } else if (message.type === 'ping') {
        ws.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
      } else {
        logger.warn(`Unknown message type: ${message.type}`);
        ws.send(JSON.stringify({
          type: 'error',
          error: `Unknown message type: ${message.type}`
        }));
      }
    } catch (error) {
      logger.error(`Error processing message from ${connectionId}:`, error);
      ws.send(JSON.stringify({
        type: 'error',
        error: 'Failed to process message',
        details: error instanceof Error ? error.message : String(error)
      }));
    }
  });

  ws.on('close', () => {
    logger.info(`Connection closed: ${connectionId}`);
    connections.delete(connectionId);
  });

  ws.on('error', (error) => {
    logger.error(`WebSocket error for ${connectionId}:`, error);
    connections.delete(connectionId);
  });
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, closing server...');
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, closing server...');
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

// Start server
server.listen(PORT, () => {
  logger.info(`Claude Agent Server listening on port ${PORT}`);
  logger.info(`WebSocket endpoint: ws://localhost:${PORT}/ws`);
  logger.info(`Health check: http://localhost:${PORT}/health`);
});
