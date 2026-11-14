import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { usePlan } from '@/features/plan/state';
import type { Trip } from '@/features/plan/api';
import { afterDecision, decide, fetchCurrent, mockMode, propose } from './api';
import { fromItinerary } from './adapter';
import { AdaptKind, AdaptRequest, CurrentTrip, demoTrip, mockProposals, Proposal, ProposalResponse, applyMock } from './model';

export type AdaptDraft = { restUntil: string; preferredKeep: string; activityId: string };
type Result = { applied: boolean; message: string; choice?: 'A' | 'B' };
type AdaptContextValue = {
  trip: CurrentTrip; ready: boolean; available: boolean;
  kind: AdaptKind; setKind: (kind: AdaptKind) => void;
  draft: AdaptDraft; setDraft: (draft: Partial<AdaptDraft>) => void;
  request: AdaptRequest | null; response: ProposalResponse | null; result: Result | null;
  busy: boolean; error: string | null; isMock: boolean;
  load: (day?: number) => Promise<boolean>;
  generate: (req: AdaptRequest) => Promise<boolean>; choose: (proposal: Proposal) => Promise<boolean>;
  reject: () => Promise<boolean>; reset: () => void;
};
const AdaptContext = createContext<AdaptContextValue | null>(null);

export function AdaptProvider({ children }: { children: React.ReactNode }) {
  const { setTrip: setPlanTrip } = usePlan();
  const setPlanTripRef = useRef(setPlanTrip);
  setPlanTripRef.current = setPlanTrip;
  const [trip, setTrip] = useState<CurrentTrip>(demoTrip);
  const [available, setAvailable] = useState(mockMode);
  const [ready, setReady] = useState(mockMode);
  const [draft, updateDraft] = useState<AdaptDraft>({ restUntil: '15:00', preferredKeep: 'A04', activityId: 'A04' });
  const setDraft = (patch: Partial<AdaptDraft>) => updateDraft(prev => ({ ...prev, ...patch }));
  const [kind, setKind] = useState<AdaptKind>('rest');
  const [request, setRequest] = useState<AdaptRequest | null>(null);
  const [response, setResponse] = useState<ProposalResponse | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inFlight = useRef(false);

  const load = useCallback(async (day?: number) => {
    if (mockMode) { setReady(true); setAvailable(true); return true; }
    if (inFlight.current) return false;
    inFlight.current = true;
    setBusy(true); setError(null);
    try {
      const current = await fetchCurrent();
      setReady(true);
      setAvailable(current !== null);
      setPlanTripRef.current(current);
      if (current) {
        const mapped = fromItinerary(current, day);
        setTrip(mapped);
        updateDraft({ restUntil: mapped.restEnd, preferredKeep: '', activityId: '' });
      }
      return current !== null;
    } catch (err) {
      setReady(true); setAvailable(false);
      setError(err instanceof Error ? err.message : 'Không thể tải lịch hiện hành.');
      return false;
    } finally { inFlight.current = false; setBusy(false); }
  }, []);

  useEffect(() => { if (!mockMode) void load(); }, [load]);

  async function generate(next: AdaptRequest) {
    if (inFlight.current || !available) return false;
    inFlight.current = true; setBusy(true); setError(null);
    try {
      const data = mockMode ? mockProposals(trip, next) : await propose(next, trip);
      setRequest(next); setResponse(data); setResult(null);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không tạo được phương án.'); return false;
    } finally { setBusy(false); inFlight.current = false; }
  }

  async function choose(option: Proposal) {
    if (inFlight.current || !response) return false;
    inFlight.current = true; setBusy(true); setError(null);
    try {
      if (option.baseVersion !== trip.version) throw new Error('Lịch đã thay đổi. Hãy tải lại và tạo đề xuất.');
      const choice = response.proposals[0]?.id === option.id ? 'A' : 'B';
      let updated: CurrentTrip;
      if (mockMode) {
        updated = applyMock(trip, option);
      } else {
        if (!response.proposalId) throw new Error('Phản hồi F05 thiếu proposal_id.');
        const decision = await decide(response.proposalId, 'ACCEPT', option.id);
        updated = afterDecision(decision, trip.day);
        setPlanTrip(decision.itinerary);
      }
      if (updated.version <= trip.version) throw new Error('API chưa xác nhận phiên bản lịch mới. Tải lại lịch trước khi tiếp tục.');
      setTrip(updated);
      setResult({ applied: true, choice, message: `Đã áp dụng ${option.title}. Lịch đã được lưu.` });
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Chưa xác nhận lưu lịch thành công. Hãy kiểm tra lại.');
      return false;
    } finally { setBusy(false); inFlight.current = false; }
  }

  async function reject() {
    if (inFlight.current || !response) return false;
    inFlight.current = true; setBusy(true); setError(null);
    try {
      if (!mockMode) {
        if (!response.proposalId) throw new Error('Phản hồi F05 thiếu proposal_id.');
        const decision = await decide(response.proposalId, 'REJECT');
        const updated = afterDecision(decision, trip.day);
        setTrip(updated);
        setPlanTrip(decision.itinerary);
      }
      setResult({ applied: false, message: 'Đã từ chối phương án. Lịch hiện hành được giữ nguyên.' });
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không gửi được quyết định giữ lịch.');
      return false;
    } finally { setBusy(false); inFlight.current = false; }
  }

  function reset() {
    if (!mockMode) return;
    updateDraft({ restUntil: '15:00', preferredKeep: 'A04', activityId: 'A04' });
    setTrip(demoTrip); setRequest(null); setResponse(null); setResult(null); setError(null);
  }

  return <AdaptContext.Provider value={{
    trip, ready, available, kind, setKind, draft, setDraft, request, response, result, busy, error,
    isMock: mockMode, load, generate, choose, reject, reset,
  }}>{children}</AdaptContext.Provider>;
}
export function useAdapt() { const value = useContext(AdaptContext); if (!value) throw Error('AdaptProvider missing'); return value; }
