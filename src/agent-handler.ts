import { WebSocket } from 'ws';
import { spawn } from 'child_process';
import { logger } from './logger';
import { loadUFCContext, buildSystemPrompt, getUserDocuments } from './ufc-loader';

interface AgentRequest {
  type: 'agent_request';
  conversationId?: string;
  message: string;
  systemPrompt?: string;
  includeUFC?: boolean;
}

/**
 * Handles agent requests by spawning Claude CLI with full UFC context
 * Uses streaming to send responses back to the client in real-time
 */
export async function handleAgentRequest(
  ws: WebSocket,
  connectionId: string,
  userId: string,
  request: AgentRequest
): Promise<void> {
  logger.info(`Processing agent request for ${connectionId}`, {
    conversationId: request.conversationId,
    includeUFC: request.includeUFC
  });

  try {
    // Load UFC context if requested (default: true)
    const includeUFC = request.includeUFC !== false;
    let systemPrompt = request.systemPrompt || '';

    if (includeUFC) {
      logger.info('Loading UFC context for agent request');
      const ufcContext = loadUFCContext();
      const userDocs = getUserDocuments(userId);
      systemPrompt = buildSystemPrompt(ufcContext, userDocs);
      logger.info('UFC context loaded and system prompt built');
    }

    // Send acknowledgment
    ws.send(JSON.stringify({
      type: 'agent_processing',
      conversationId: request.conversationId,
      message: 'Processing your request with full UFC context...'
    }));

    // Spawn Claude CLI process with streaming output
    const claudeArgs = ['chat', '--print', '--output-format', 'stream-json', '--verbose'];

    // Add system prompt if provided
    if (systemPrompt) {
      claudeArgs.push('--system-prompt', systemPrompt);
    }

    // Add the user message
    claudeArgs.push(request.message);

    logger.info('Spawning Claude CLI', { args: claudeArgs });

    const claudeProcess = spawn('claude', claudeArgs, {
      env: {
        ...process.env,
        // Claude CLI will use authenticated credentials from volume
      }
    });

    let responseBuffer = '';
    let lineBuffer = '';

    // Handle stdout (streaming response in JSON format)
    claudeProcess.stdout.on('data', (data: Buffer) => {
      const chunk = data.toString();
      lineBuffer += chunk;

      // Process complete lines (newline-delimited JSON)
      const lines = lineBuffer.split('\n');
      lineBuffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (!line.trim()) continue;

        try {
          const jsonChunk = JSON.parse(line);

          // Handle different JSON stream events
          if (jsonChunk.type === 'text' && jsonChunk.text) {
            responseBuffer += jsonChunk.text;

            // Send text chunk to client
            ws.send(JSON.stringify({
              type: 'agent_chunk',
              conversationId: request.conversationId,
              chunk: jsonChunk.text
            }));
          } else if (jsonChunk.type === 'error') {
            logger.error('Claude CLI error event:', jsonChunk);
            ws.send(JSON.stringify({
              type: 'agent_error',
              conversationId: request.conversationId,
              error: jsonChunk.message || 'Unknown error'
            }));
          }
        } catch (parseError) {
          logger.warn('Failed to parse JSON line:', line, parseError);
        }
      }
    });

    // Handle stderr (errors and warnings)
    claudeProcess.stderr.on('data', (data: Buffer) => {
      const error = data.toString();
      logger.warn(`Claude CLI stderr: ${error}`);

      // Send error to client
      ws.send(JSON.stringify({
        type: 'agent_error',
        conversationId: request.conversationId,
        error
      }));
    });

    // Handle process completion
    claudeProcess.on('close', (code) => {
      if (code === 0) {
        logger.info(`Agent request completed successfully for ${connectionId}`);
        ws.send(JSON.stringify({
          type: 'agent_complete',
          conversationId: request.conversationId,
          fullResponse: responseBuffer
        }));
      } else {
        logger.error(`Claude CLI exited with code ${code}`);
        ws.send(JSON.stringify({
          type: 'agent_error',
          conversationId: request.conversationId,
          error: `Claude CLI exited with code ${code}`,
          exitCode: code
        }));
      }
    });

    // Handle process errors
    claudeProcess.on('error', (error) => {
      logger.error('Error spawning Claude CLI:', error);
      ws.send(JSON.stringify({
        type: 'agent_error',
        conversationId: request.conversationId,
        error: `Failed to start Claude CLI: ${error.message}`
      }));
    });
  } catch (error) {
    logger.error('Error handling agent request:', error);
    ws.send(JSON.stringify({
      type: 'agent_error',
      conversationId: request.conversationId,
      error: error instanceof Error ? error.message : String(error)
    }));
  }
}

/**
 * Invokes a specific sub-agent with parameters
 */
export async function invokeSubAgent(
  ws: WebSocket,
  connectionId: string,
  userId: string,
  agentName: string,
  prompt: string
): Promise<void> {
  logger.info(`Invoking sub-agent: ${agentName}`, { connectionId });

  try {
    const claudeArgs = ['task', agentName, prompt];

    logger.info('Spawning Claude CLI for sub-agent', { agentName, args: claudeArgs });

    const claudeProcess = spawn('claude', claudeArgs);

    let responseBuffer = '';

    claudeProcess.stdout.on('data', (data: Buffer) => {
      const chunk = data.toString();
      responseBuffer += chunk;

      ws.send(JSON.stringify({
        type: 'agent_chunk',
        agent: agentName,
        chunk
      }));
    });

    claudeProcess.stderr.on('data', (data: Buffer) => {
      const error = data.toString();
      logger.warn(`Sub-agent ${agentName} stderr: ${error}`);
    });

    claudeProcess.on('close', (code) => {
      if (code === 0) {
        logger.info(`Sub-agent ${agentName} completed successfully`);
        ws.send(JSON.stringify({
          type: 'agent_complete',
          agent: agentName,
          fullResponse: responseBuffer
        }));
      } else {
        logger.error(`Sub-agent ${agentName} exited with code ${code}`);
        ws.send(JSON.stringify({
          type: 'agent_error',
          agent: agentName,
          error: `Sub-agent exited with code ${code}`,
          exitCode: code
        }));
      }
    });

    claudeProcess.on('error', (error) => {
      logger.error(`Error invoking sub-agent ${agentName}:`, error);
      ws.send(JSON.stringify({
        type: 'agent_error',
        agent: agentName,
        error: `Failed to invoke sub-agent: ${error.message}`
      }));
    });
  } catch (error) {
    logger.error(`Error invoking sub-agent ${agentName}:`, error);
    ws.send(JSON.stringify({
      type: 'agent_error',
      agent: agentName,
      error: error instanceof Error ? error.message : String(error)
    }));
  }
}
