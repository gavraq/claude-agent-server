import jwt from 'jsonwebtoken';
import { IncomingMessage } from 'http';
import { logger } from './logger';

const JWT_SECRET = process.env.JWT_SECRET;

if (!JWT_SECRET) {
  throw new Error('JWT_SECRET environment variable is required');
}

export interface AuthResult {
  authenticated: boolean;
  userId?: string;
  error?: string;
}

export interface JWTPayload {
  userId: string;
  iat: number;
  exp: number;
}

/**
 * Authenticates a WebSocket connection by verifying the JWT token
 * Token can be provided in:
 * 1. Query parameter: ?token=xxx
 * 2. Authorization header: Bearer xxx
 */
export async function authenticateConnection(req: IncomingMessage): Promise<AuthResult> {
  try {
    // Extract token from query parameter or Authorization header
    let token: string | undefined;

    // Check query parameter
    if (req.url) {
      const url = new URL(req.url, `http://${req.headers.host}`);
      token = url.searchParams.get('token') || undefined;
    }

    // Check Authorization header if no query token
    if (!token && req.headers.authorization) {
      const authHeader = req.headers.authorization;
      if (authHeader.startsWith('Bearer ')) {
        token = authHeader.substring(7);
      }
    }

    if (!token) {
      return {
        authenticated: false,
        error: 'No authentication token provided'
      };
    }

    // Verify the JWT token
    const decoded = jwt.verify(token, JWT_SECRET) as JWTPayload;

    logger.info('Token verified successfully', { userId: decoded.userId });

    return {
      authenticated: true,
      userId: decoded.userId
    };
  } catch (error) {
    logger.error('Authentication error:', error);
    return {
      authenticated: false,
      error: error instanceof Error ? error.message : 'Invalid token'
    };
  }
}

/**
 * Generates a JWT token for a user
 * Used by Vercel to create tokens for authenticated users
 */
export function generateToken(userId: string, expiresIn: string = '24h'): string {
  return jwt.sign(
    { userId },
    JWT_SECRET,
    { expiresIn }
  );
}
