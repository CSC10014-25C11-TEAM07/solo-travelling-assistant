import { AdaptRequest, CurrentTrip, Proposal, ProposalResponse } from './model';

/** Endpoints are provisional: reconcile with docs/api and Bảo 06 before enabling API mode. */
const base = process.env.EXPO_PUBLIC_API_URL?.replace(/\/$/, '');
export const apiConfigured = !!base && process.env.EXPO_PUBLIC_ADAPT_API_ENABLED === 'true';
async function request<T>(path: string, body: unknown): Promise<T> {
  if (!apiConfigured) throw new Error('Chưa cấu hình API ADAPT.');
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(`${base}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal: controller.signal });
    if (response.status === 409) throw new Error('Lịch đã thay đổi. Hãy tạo lại phương án.');
    if (!response.ok) throw new Error(`API lỗi HTTP ${response.status}. Lịch hiện hành không đổi.`);
    return await response.json() as T;
  } finally { clearTimeout(timeout); }
}
export function propose(req: AdaptRequest) { return request<ProposalResponse>('/adapt/proposals', req); }
export function accept(trip: CurrentTrip, proposal: Proposal) {
  return request<CurrentTrip>('/adapt/apply', { tripId: trip.id, expectedVersion: trip.version, proposalId: proposal.id });
}
