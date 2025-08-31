import { vi, beforeEach } from 'vitest'
import '@testing-library/jest-dom'

// Mock environment variables
process.env.SUPABASE_URL = 'https://test.supabase.co'
process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-service-key'
process.env.OPENAI_API_KEY = 'test-openai-key'

// Mock Supabase client
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

// Mock OpenAI
vi.mock('@langchain/openai', () => ({
  OpenAIEmbeddings: vi.fn().mockImplementation(() => ({
    embedQuery: vi.fn(),
    embedDocuments: vi.fn()
  })),
  OpenAI: vi.fn().mockImplementation(() => ({
    call: vi.fn()
  }))
}))

// Mock Langchain text splitter
vi.mock('@langchain/textsplitters', () => ({
  RecursiveCharacterTextSplitter: vi.fn().mockImplementation(() => ({
    createDocuments: vi.fn()
  }))
}))

// Mock Langchain Document
vi.mock('langchain/document', () => ({
  Document: vi.fn()
}))

// Global test utilities
global.console = {
  ...console,
  log: vi.fn(),
  error: vi.fn(),
  warn: vi.fn(),
  info: vi.fn(),
  debug: vi.fn()
}

// Suppress all console output during tests
beforeEach(() => {
  vi.clearAllMocks()
}) 