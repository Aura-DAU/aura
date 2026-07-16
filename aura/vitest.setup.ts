import '@testing-library/jest-dom'

process.env.INTERNAL_JWT_SECRET = 'mock-secret'
process.env.NEXTAUTH_SECRET = 'mock-secret'
process.env.GOOGLE_CLIENT_ID = 'mock-client'
process.env.GOOGLE_CLIENT_SECRET = 'mock-client'
process.env.INTERNAL_RESOLVE_SECRET = 'mock-secret'

const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value },
    removeItem: (key: string) => { delete store[key] },
    clear: () => { store = {} },
  }
})()

Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock })
