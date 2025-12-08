/**
 * Test utilities for Preact component testing.
 *
 * Provides wrapper components and helper functions for testing.
 */

import { render, RenderOptions } from '@testing-library/preact'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ComponentChildren } from 'preact'

/**
 * Create a new QueryClient configured for testing.
 */
export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Disable retries in tests
        retry: false,
        // Disable refetching in tests
        refetchOnWindowFocus: false,
        // Disable caching for predictable tests
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

interface WrapperProps {
  children: ComponentChildren
}

/**
 * Create a wrapper component with all providers for testing.
 */
export function createWrapper(queryClient?: QueryClient) {
  const client = queryClient ?? createTestQueryClient()

  return function Wrapper({ children }: WrapperProps) {
    return (
      <QueryClientProvider client={client}>
        {children}
      </QueryClientProvider>
    )
  }
}

/**
 * Custom render function that wraps components with necessary providers.
 */
export function renderWithProviders(
  ui: ComponentChildren,
  options?: Omit<RenderOptions, 'wrapper'> & { queryClient?: QueryClient }
) {
  const { queryClient, ...renderOptions } = options ?? {}
  const Wrapper = createWrapper(queryClient)

  return {
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
    queryClient: queryClient ?? createTestQueryClient(),
  }
}

/**
 * Wait for a condition to be true (useful for async operations).
 */
export async function waitFor(
  callback: () => boolean | void,
  { timeout = 1000, interval = 50 } = {}
): Promise<void> {
  const startTime = Date.now()

  return new Promise((resolve, reject) => {
    const check = () => {
      try {
        const result = callback()
        if (result !== false) {
          resolve()
          return
        }
      } catch (error) {
        // Keep trying
      }

      if (Date.now() - startTime >= timeout) {
        reject(new Error(`waitFor timed out after ${timeout}ms`))
        return
      }

      setTimeout(check, interval)
    }

    check()
  })
}

// Re-export everything from testing-library
export * from '@testing-library/preact'
