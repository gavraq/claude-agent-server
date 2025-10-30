import fs from 'fs';
import path from 'path';
import { logger } from './logger';

const UFC_PATH = process.env.UFC_PATH || '/ufc';
const CLAUDE_CONFIG_PATH = process.env.CLAUDE_CONFIG_PATH || '/claude-config';
const VAULT_PATH = process.env.VAULT_PATH || '/vault';
const DOCUMENTS_PATH = process.env.DOCUMENTS_PATH || '/documents';
const PROJECTS_PATH = process.env.PROJECTS_PATH || '/projects';

export interface UFCContext {
  profile: {
    coreIdentity: string;
    goalsObjectives: string;
  };
  activeProjects: {
    [key: string]: string;
  };
  tools: {
    [key: string]: string;
  };
  agentDefinitions: {
    [key: string]: string;
  };
  commands: {
    [key: string]: string;
  };
}

/**
 * Loads the complete UFC context from mounted volumes
 * This provides the full system awareness for the Claude agent
 */
export function loadUFCContext(): UFCContext {
  logger.info('Loading UFC context...');

  const context: UFCContext = {
    profile: {
      coreIdentity: '',
      goalsObjectives: ''
    },
    activeProjects: {},
    tools: {},
    agentDefinitions: {},
    commands: {}
  };

  try {
    // Load profile context
    const profilePath = path.join(UFC_PATH, 'profile');
    if (fs.existsSync(profilePath)) {
      context.profile.coreIdentity = readFile(path.join(profilePath, 'core-identity.md'));
      context.profile.goalsObjectives = readFile(path.join(profilePath, 'goals-objectives.md'));
      logger.info('Profile context loaded');
    }

    // Load active projects
    const projectsPath = path.join(UFC_PATH, 'active-projects');
    if (fs.existsSync(projectsPath)) {
      const projectFiles = fs.readdirSync(projectsPath).filter(f => f.endsWith('.md'));
      for (const file of projectFiles) {
        const projectName = file.replace('.md', '');
        context.activeProjects[projectName] = readFile(path.join(projectsPath, file));
      }
      logger.info(`Loaded ${projectFiles.length} active projects`);
    }

    // Load tools context
    const toolsPath = path.join(UFC_PATH, 'tools');
    if (fs.existsSync(toolsPath)) {
      const toolFiles = fs.readdirSync(toolsPath).filter(f => f.endsWith('.md'));
      for (const file of toolFiles) {
        const toolName = file.replace('.md', '');
        context.tools[toolName] = readFile(path.join(toolsPath, file));
      }
      logger.info(`Loaded ${toolFiles.length} tool contexts`);
    }

    // Load agent definitions
    const agentsPath = path.join(CLAUDE_CONFIG_PATH, 'agents');
    if (fs.existsSync(agentsPath)) {
      const agentFiles = fs.readdirSync(agentsPath).filter(f => f.endsWith('.md'));
      for (const file of agentFiles) {
        const agentName = file.replace('.md', '');
        context.agentDefinitions[agentName] = readFile(path.join(agentsPath, file));
      }
      logger.info(`Loaded ${agentFiles.length} agent definitions`);
    }

    // Load commands
    const commandsPath = path.join(CLAUDE_CONFIG_PATH, 'commands');
    if (fs.existsSync(commandsPath)) {
      const commandFiles = fs.readdirSync(commandsPath).filter(f => f.endsWith('.md'));
      for (const file of commandFiles) {
        const commandName = file.replace('.md', '');
        context.commands[commandName] = readFile(path.join(commandsPath, file));
      }
      logger.info(`Loaded ${commandFiles.length} commands`);
    }

    logger.info('UFC context loaded successfully');
    return context;
  } catch (error) {
    logger.error('Error loading UFC context:', error);
    throw error;
  }
}

/**
 * Builds a comprehensive system prompt with full UFC context
 */
export function buildSystemPrompt(ufcContext: UFCContext, userDocuments?: string[]): string {
  let prompt = `# Gavin's Personal AI Assistant with Full UFC Context

You are Claude, operating with complete access to Gavin's Universal File Context (UFC) system.

## Core Identity & Values
${ufcContext.profile.coreIdentity}

## Goals & Objectives
${ufcContext.profile.goalsObjectives}

## Active Projects
`;

  // Add all active projects
  for (const [projectName, content] of Object.entries(ufcContext.activeProjects)) {
    prompt += `\n### ${projectName}\n${content}\n`;
  }

  prompt += `\n## Available Tools & Integrations\n`;

  // Add tools context
  for (const [toolName, content] of Object.entries(ufcContext.tools)) {
    prompt += `\n### ${toolName}\n${content}\n`;
  }

  prompt += `\n## Specialized Sub-Agents Available\n`;

  // List available agents
  for (const agentName of Object.keys(ufcContext.agentDefinitions)) {
    prompt += `- ${agentName}\n`;
  }

  prompt += `\n## Available Commands\n`;

  // List available commands
  for (const commandName of Object.keys(ufcContext.commands)) {
    prompt += `- /${commandName}\n`;
  }

  // Add user documents if provided
  if (userDocuments && userDocuments.length > 0) {
    prompt += `\n## User's Uploaded Documents\n`;
    userDocuments.forEach((doc, index) => {
      prompt += `${index + 1}. ${doc}\n`;
    });
  }

  prompt += `\n## Available Resources
- Obsidian Vault: ${VAULT_PATH}
- Documents Directory: ${DOCUMENTS_PATH}
- Projects Directory: ${PROJECTS_PATH}

## Operating Instructions
1. **Context-Aware**: You have full awareness of Gavin's goals, projects, and life context
2. **Tools-First**: Leverage existing integrations (Gmail, FreeAgent, LinkedIn, Parkrun, Owntracks, Obsidian)
3. **Goal-Aligned**: Every action should connect to Gavin's objectives and GTD horizons
4. **Quantified Self**: Provide data-driven insights and track progress
5. **Proactive**: Identify opportunities and optimization suggestions

You have access to all MCP servers and specialized sub-agents configured in the system.
`;

  return prompt;
}

/**
 * Helper function to read file contents
 */
function readFile(filePath: string): string {
  try {
    return fs.readFileSync(filePath, 'utf-8');
  } catch (error) {
    logger.warn(`Could not read file: ${filePath}`, error);
    return '';
  }
}

/**
 * Gets list of user's uploaded documents
 */
export function getUserDocuments(userId: string): string[] {
  const userDocsPath = path.join(DOCUMENTS_PATH, userId);

  if (!fs.existsSync(userDocsPath)) {
    return [];
  }

  try {
    return fs.readdirSync(userDocsPath);
  } catch (error) {
    logger.error(`Error reading user documents for ${userId}:`, error);
    return [];
  }
}
