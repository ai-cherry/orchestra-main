import { test, expect } from '@playwright/test'

test('query endpoint works', async ({ request }) => {
  const resp = await request.post('http://localhost:3001/api/query', { data: { query: 'ping' } })
  expect(resp.ok()).toBeTruthy()
})
