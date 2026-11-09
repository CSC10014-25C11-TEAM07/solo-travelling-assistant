/** Run against a local server with an isolated demo DB; creates a test account. */
import assert from 'node:assert/strict';
import { randomBytes } from 'node:crypto';
import { fetchRecommendations } from '../src/services/places.ts';

const port = Number(process.env.F01_TEST_PORT ?? 8001);
assert(Number.isInteger(port) && port > 0 && port <= 65535, 'Invalid F01_TEST_PORT');
const apiUrl = `http://127.0.0.1:${port}`;
const credentials = {
  username: `f01_smoke_${randomBytes(6).toString('hex')}`,
  password: randomBytes(24).toString('hex'),
};
const jsonRequest = {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(credentials),
};

assert.equal((await fetch(`${apiUrl}/api/v1/auth/register`, jsonRequest)).status, 201);
const login = await fetch(`${apiUrl}/api/v1/auth/login`, jsonRequest);
assert.equal(login.status, 200);
const { access_token: accessToken } = await login.json();
assert.equal(typeof accessToken, 'string');
const headers = { Authorization: `Bearer ${accessToken}` };
try {
  for (const interests of [['coffee'], ['nature', 'culture']]) {
    const response = await fetchRecommendations({ apiUrl, accessToken, interests });
    assert(response.places.length > 0 && response.places.length <= 3);
    console.log(`PASS ${interests.join('+')}: ${response.places.map(p => p.place_id).join(', ')}`);
  }
  const missing = await fetch(`${apiUrl}/api/v1/places/recommendations?interests=coffee`);
  assert.equal(missing.status, 401);
  const invalid = await fetch(`${apiUrl}/api/v1/places/recommendations?interests=invalid`, { headers });
  assert.equal(invalid.status, 422);
  assert.equal((await invalid.json()).field, 'interests');
  await assert.rejects(fetchRecommendations({ apiUrl, accessToken: 'INVALID-TEST-ONLY', interests: ['coffee'] }), {
    status: 401, code: 'INVALID_SESSION',
  });
} finally {
  assert.equal((await fetch(`${apiUrl}/api/v1/auth/logout`, { method: 'POST', headers })).status, 200);
}
await assert.rejects(fetchRecommendations({ apiUrl, accessToken, interests: ['coffee'] }), {
  status: 401, code: 'INVALID_SESSION',
});
console.log('PASS real registration/login, HTTP validation, invalid/revoked sessions. No token logged.');
