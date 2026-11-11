/** F01 transport for S01. Screen state and rendering remain owned by the caller. */

export const INTERESTS = ["nature", "coffee", "culture", "food"] as const;
export type Interest = (typeof INTERESTS)[number];

export type PlaceRecommendation = {
  place_id: string;
  name: string;
  image_url: string | null;
  reason: string;
};

export type RecommendationsResponse = { places: PlaceRecommendation[] };

export class RecommendationsError extends Error {
  readonly code: string;
  readonly status: number | null;
  readonly field?: string;

  constructor(message: string, code: string, status: number | null = null, field?: string) {
    super(message);
    this.name = "RecommendationsError";
    this.code = code;
    this.status = status;
    this.field = field;
  }
}

type RequestOptions = {
  apiUrl: string;
  accessToken: string;
  interests: readonly Interest[];
  signal?: AbortSignal;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isResponse(value: unknown): value is RecommendationsResponse {
  return isRecord(value) && Array.isArray(value.places) && value.places.length <= 3 &&
    value.places.every((place: unknown) => isRecord(place) &&
      typeof place.place_id === "string" && typeof place.name === "string" &&
      typeof place.reason === "string" &&
      (place.image_url === null || typeof place.image_url === "string"));
}

export async function fetchRecommendations(options: RequestOptions): Promise<RecommendationsResponse> {
  const { apiUrl, accessToken, interests, signal } = options;
  if (!accessToken.trim()) {
    throw new RecommendationsError("Vui lòng đăng nhập.", "AUTH_REQUIRED");
  }
  if (!interests.length || interests.some((interest) => !INTERESTS.includes(interest))) {
    throw new RecommendationsError("Chọn ít nhất một sở thích hợp lệ.", "VALIDATION_ERROR", 422, "interests");
  }
  let base: URL;
  try {
    base = new URL(apiUrl);
    if (!["http:", "https:"].includes(base.protocol) || base.username || base.password ||
        base.search || base.hash || !["", "/"].includes(base.pathname)) {
      throw new Error("Invalid API root");
    }
  } catch {
    throw new RecommendationsError("Địa chỉ backend cần là HTTP(S) và không kèm đường dẫn API.", "INVALID_API_URL");
  }
  const query = new URLSearchParams();
  for (const interest of new Set(interests)) query.append("interests", interest);
  const url = `${base.origin}/api/v1/places/recommendations?${query.toString()}`;
  let response: Response;
  try {
    response = await fetch(url, {
      headers: { Authorization: `Bearer ${accessToken}` },
      signal,
    });
  } catch (error) {
    if (signal?.aborted || (error instanceof Error && error.name === "AbortError")) throw error;
    throw new RecommendationsError("Chưa kết nối được backend. Kiểm tra địa chỉ và Wi-Fi.", "NETWORK_ERROR");
  }
  let body: unknown;
  try {
    body = await response.json();
  } catch (error) {
    if (signal?.aborted || (error instanceof Error && error.name === "AbortError")) throw error;
    throw new RecommendationsError("Backend trả dữ liệu không đúng định dạng.", "INVALID_RESPONSE", response.status);
  }
  if (!response.ok) {
    const record = isRecord(body) ? body : {};
    throw new RecommendationsError(
      typeof record.message === "string" ? record.message : `Không lấy được gợi ý (HTTP ${response.status}).`,
      typeof record.code === "string" ? record.code : "HTTP_ERROR",
      response.status,
      typeof record.field === "string" ? record.field : undefined,
    );
  }
  if (!isResponse(body)) {
    throw new RecommendationsError("Danh sách gợi ý không đúng hợp đồng F01.", "INVALID_RESPONSE", response.status);
  }
  return body;
}
