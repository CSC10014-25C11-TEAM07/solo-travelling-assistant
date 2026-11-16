import { configured, request as sharedRequest, type Trip } from '@/features/plan/api';
import type { AdaptRequest, CurrentTrip, ProposalResponse } from './model';
import { mapProposalResponse, fromItinerary } from './adapter';

/** Explicit opt-in for isolated demo. Never silently replace an API error with MOCK. */
export const mockMode = process.env.EXPO_PUBLIC_ADAPT_MOCK_ENABLED === 'true';
export const apiConfigured = configured && !mockMode;

type CurrentResponse = { itinerary: Trip | null };
type DecisionResponse = {
  proposal_id: string; decision: 'ACCEPT' | 'REJECT'; option_id: string | null; itinerary: Trip;
};

export async function fetchCurrent(): Promise<Trip | null> {
  if (!configured) throw new Error('Thiếu EXPO_PUBLIC_API_URL trong mobile/.env.');
  const result = await sharedRequest('/api/v1/itineraries/current') as CurrentResponse;
  return result.itinerary ?? null;
}

export async function propose(req: AdaptRequest, trip: CurrentTrip): Promise<ProposalResponse> {
  if (!apiConfigured) throw new Error('Chưa cấu hình kết nối API ADAPT.');
  const restActivityId = 'restActivityId' in trip ? trip.restActivityId : undefined;
  const body = req.kind === 'rest'
    ? { type: 'EXTEND_REST', base_version: req.baseVersion,
        rest_activity_id: restActivityId, rest_until: req.restUntil,
        preferred_keep_activity_id: req.preferredKeep || null }
    : { type: 'REPLACE_LOCATION', base_version: req.baseVersion,
        activity_id: req.activityId, reason: 'RAIN' };
  if (req.kind === 'rest' && !restActivityId) {
    throw new Error('Ngày này chưa có khoảng REST đang chờ thực hiện.');
  }
  try {
    const data = await sharedRequest(`/api/v1/itineraries/${encodeURIComponent(req.tripId)}/adapt-proposals`,
      { method: 'POST', body: JSON.stringify(body) });
    return mapProposalResponse(data);
  } catch (error) {
    const status = (error as Error & { status?: number }).status;
    if (status === 404) {
      throw new Error('Backend chưa đăng ký API tạo đề xuất F05. Cần Nhật/Bảo 06 nối endpoint /adapt-proposals.');
    }
    throw error;
  }
}

export async function decide(proposalId: string, decision: 'ACCEPT' | 'REJECT', optionId?: string): Promise<DecisionResponse> {
  if (!apiConfigured) throw new Error('Chưa cấu hình kết nối API ADAPT.');
  return sharedRequest(`/api/v1/adapt-proposals/${encodeURIComponent(proposalId)}/decision`,
    { method: 'POST', body: JSON.stringify({
      decision, ...(decision === 'ACCEPT' ? { option_id: optionId } : {}),
    }) }) as Promise<DecisionResponse>;
}
export function afterDecision(data: DecisionResponse, selectedDay: number) {
  if (!data.itinerary?.itinerary_id || !Number.isInteger(data.itinerary.version)) {
    throw new Error('API F06 không trả về itinerary hợp lệ.');
  }
  return fromItinerary(data.itinerary, selectedDay);
}
