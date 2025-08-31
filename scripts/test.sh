# Install dependencies
npm install

# Run all tests - does not work with e2e tests
npm test

# Run specific test categories
npm run test:unit        # Unit tests only
npm run test:integration # Integration tests only  
npm run test:e2e         # E2E tests only

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch