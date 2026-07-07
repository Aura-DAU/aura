import '@testing-library/jest-dom'

process.env.INTERNAL_JWT_SECRET = 'mock-secret'
process.env.NEXTAUTH_SECRET = 'mock-secret'
process.env.GOOGLE_CLIENT_ID = 'mock-client'
process.env.GOOGLE_CLIENT_SECRET = 'mock-client'
process.env.INTERNAL_RESOLVE_SECRET = 'mock-secret'
