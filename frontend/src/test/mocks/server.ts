/**
 * MSW server setup for tests.
 *
 * This creates a mock server that intercepts HTTP requests during tests.
 */

import { setupServer } from 'msw/node'
import { handlers } from './handlers'

// Create the mock server with default handlers
export const server = setupServer(...handlers)
