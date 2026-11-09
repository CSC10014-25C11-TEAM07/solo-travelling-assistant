import assert from "node:assert/strict";
import { afterEach, test } from "node:test";
import { fetchRecommendations, RecommendationsError } from "../src/services/places.ts";

const originalFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = originalFetch; });
const options = { apiUrl: "http://127.0.0.1:8001/", accessToken: "TEST-ONLY", interests: ["nature", "coffee"] };
const place = { place_id: "P001", name: "Test place", image_url: null, reason: "Test reason" };

test("uses repeated unique interests and Bearer; accepts null image", async () => {
  globalThis.fetch = async (url, request) => {
    const parsed = new URL(url);
    assert.equal(parsed.pathname, "/api/v1/places/recommendations");
    assert.deepEqual(parsed.searchParams.getAll("interests"), ["nature", "coffee"]);
    assert.equal(request.headers.Authorization, "Bearer TEST-ONLY");
    return Response.json({ places: [place] });
  };
  assert.deepEqual(await fetchRecommendations({ ...options, interests: ["nature", "coffee", "coffee"] }), { places: [place] });
});

test("empty recommendations are valid", async () => {
  globalThis.fetch = async () => Response.json({ places: [] });
  assert.deepEqual(await fetchRecommendations(options), { places: [] });
});

test("propagates session errors and validation field", async () => {
  for (const [status, code, field] of [[401, "SESSION_EXPIRED", undefined], [422, "VALIDATION_ERROR", "interests"], [503, "AUTH_NOT_READY", undefined]]) {
    globalThis.fetch = async () => Response.json({ code, message: "Test error", field }, { status });
    await assert.rejects(fetchRecommendations(options), (error) => {
      assert(error instanceof RecommendationsError);
      assert.equal(error.status, status);
      assert.equal(error.code, code);
      assert.equal(error.field, field);
      return true;
    });
  }
});

test("does not send requests with missing credentials or invalid preferences", async () => {
  globalThis.fetch = () => { throw new Error("Should not fetch"); };
  await assert.rejects(fetchRecommendations({ ...options, accessToken: " " }), { code: "AUTH_REQUIRED" });
  await assert.rejects(fetchRecommendations({ ...options, interests: [] }), { code: "VALIDATION_ERROR" });
  await assert.rejects(fetchRecommendations({ ...options, interests: ["unknown"] }), { field: "interests" });
});

test("rejects malformed response and more than three places", async () => {
  for (const body of [{}, { places: [1] }, { places: [{ ...place, image_url: undefined }] }, { places: [place, place, place, place] }]) {
    globalThis.fetch = async () => Response.json(body);
    await assert.rejects(fetchRecommendations(options), { code: "INVALID_RESPONSE" });
  }
});

test("rejects an invalid backend root before sending a token", async () => {
  globalThis.fetch = () => { throw new Error("Should not fetch"); };
  for (const apiUrl of ["invalid", "ftp://example.com", "http://example.com/api/v1", "http://user:pass@example.com", "http://example.com?token=x"]) {
    await assert.rejects(fetchRecommendations({ ...options, apiUrl }), { code: "INVALID_API_URL" });
  }
});

test("network error gets a usable error code", async () => {
  globalThis.fetch = async () => { throw new TypeError("Fetch failed"); };
  await assert.rejects(fetchRecommendations(options), { code: "NETWORK_ERROR" });
});

test("passes AbortSignal and preserves AbortError", async () => {
  const controller = new AbortController();
  controller.abort();
  globalThis.fetch = async (_url, request) => {
    assert.equal(request.signal, controller.signal);
    throw new DOMException("Aborted", "AbortError");
  };
  await assert.rejects(fetchRecommendations({ ...options, signal: controller.signal }), { name: "AbortError" });
});

test("preserves cancellation while reading the response body", async () => {
  const controller = new AbortController();
  globalThis.fetch = async () => ({
    ok: true,
    status: 200,
    json: async () => {
      controller.abort();
      throw new DOMException("Aborted", "AbortError");
    },
  });
  await assert.rejects(fetchRecommendations({ ...options, signal: controller.signal }), { name: "AbortError" });
});
