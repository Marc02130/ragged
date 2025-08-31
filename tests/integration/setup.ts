import { vi } from 'vitest'
import '@testing-library/jest-dom'

// Mock environment variables for integration tests
process.env.SUPABASE_URL = 'https://test.supabase.co'
process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-service-key'
process.env.OPENAI_API_KEY = 'test-openai-key'

// Mock Supabase client for integration tests
vi.mock('@supabase/supabase-js', () => ({
  createClient: vi.fn(() => ({
    auth: {
      getUser: vi.fn()
    },
    from: vi.fn(() => ({
      select: vi.fn(() => ({
        eq: vi.fn(() => ({
          single: vi.fn(),
          order: vi.fn(() => ({
            limit: vi.fn()
          }))
        })),
        insert: vi.fn(() => ({
          select: vi.fn(() => ({
            single: vi.fn()
          }))
        })),
        update: vi.fn(() => ({
          eq: vi.fn()
        })),
        delete: vi.fn(() => ({
          eq: vi.fn()
        }))
      })),
      rpc: vi.fn()
    }))
  }))
}))

// Mock OpenAI for integration tests
vi.mock('@langchain/openai', () => ({
  OpenAIEmbeddings: vi.fn().mockImplementation(() => ({
    embedQuery: vi.fn(),
    embedDocuments: vi.fn()
  }))
}))

// Global test utilities for integration tests
global.console = {
  ...console,
  log: vi.fn(),
  error: vi.fn(),
  warn: vi.fn(),
  info: vi.fn()
} 