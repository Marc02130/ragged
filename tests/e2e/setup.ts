import { vi } from 'vitest'
import '@testing-library/jest-dom'

// Mock environment variables for e2e tests
process.env.SUPABASE_URL = 'https://test.supabase.co'
process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-service-key'
process.env.OPENAI_API_KEY = 'test-openai-key'

// Mock Supabase client for e2e tests
vi.mock('@supabase/supabase-js', () => {
  const createMockChain = () => {
    const mockResolvedValue = vi.fn()
    const mockChain = {
      select: vi.fn(() => mockChain),
      eq: vi.fn(() => mockChain),
      order: vi.fn(() => mockChain),
      limit: vi.fn(() => mockChain),
      single: vi.fn(() => mockChain),
      insert: vi.fn(() => mockChain),
      update: vi.fn(() => mockChain),
      delete: vi.fn(() => mockChain),
      mockResolvedValue,
      mockResolvedValueOnce: mockResolvedValue,
      mockReturnValue: vi.fn(() => mockChain),
      mockReturnValueOnce: vi.fn(() => mockChain),
      mock: {
        calls: []
      }
    }
    return mockChain
  }

  return {
    createClient: vi.fn(() => ({
      auth: {
        getUser: vi.fn()
      },
      from: vi.fn(() => createMockChain()),
      rpc: vi.fn(() => createMockChain())
    }))
  }
})

// Mock OpenAI for e2e tests
vi.mock('@langchain/openai', () => ({
  OpenAIEmbeddings: vi.fn().mockImplementation(() => ({
    embedQuery: vi.fn(),
    embedDocuments: vi.fn()
  })),
  OpenAI: vi.fn().mockImplementation(() => ({
    call: vi.fn()
  }))
}))

// Global test utilities for e2e tests
global.console = {
  ...console,
  log: vi.fn(),
  error: vi.fn(),
  warn: vi.fn(),
  info: vi.fn()
} 