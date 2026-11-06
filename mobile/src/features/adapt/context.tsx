import React, { createContext, useContext, useState } from 'react';
import { accept, apiConfigured, propose } from './api';
import { AdaptKind, AdaptRequest, CurrentTrip, demoTrip, mockProposals, Proposal, ProposalResponse, applyMock } from './model';

export type AdaptDraft = { restUntil: string; preferredKeep: string; activityId: string };
type Result = { applied: boolean; message: string; choice?: 'A' | 'B' };
type AdaptContextValue = {
  trip: CurrentTrip; kind: AdaptKind; setKind: (kind: AdaptKind) => void;
  draft: AdaptDraft; setDraft: (draft: Partial<AdaptDraft>) => void;
  request: AdaptRequest | null; response: ProposalResponse | null; result: Result | null;
  busy: boolean; error: string | null; isMock: boolean;
  generate: (req: AdaptRequest) => Promise<boolean>; choose: (proposal: Proposal) => Promise<boolean>;
  reject: () => void; reset: () => void;
};
const AdaptContext = createContext<AdaptContextValue | null>(null);
export function AdaptProvider({ children }: { children: React.ReactNode }) {
  const [trip, setTrip] = useState<CurrentTrip>(demoTrip);
  const [draft, updateDraft] = useState<AdaptDraft>({ restUntil: '15:00', preferredKeep: 'A04', activityId: 'A04' });
  const setDraft = (patch: Partial<AdaptDraft>) => updateDraft(prev => ({ ...prev, ...patch }));
  const [kind, setKind] = useState<AdaptKind>('rest');
  const [request, setRequest] = useState<AdaptRequest | null>(null);
  const [response, setResponse] = useState<ProposalResponse | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  async function generate(next: AdaptRequest) {
    setBusy(true); setError(null);
    try {
      const data = apiConfigured ? await propose(next) : mockProposals(trip, next);
      setRequest(next); setResponse(data); setResult(null); return true;
    } catch (e) { setError(e instanceof Error ? e.message : 'Không tạo được phương án.'); return false; }
    finally { setBusy(false); }
  }
  async function choose(p: Proposal) {
    setBusy(true); setError(null);
    try {
      if (p.baseVersion !== trip.version) throw new Error('Đề xuất đã cũ. Hãy tạo lại phương án.');
      const updated = apiConfigured ? await accept(trip, p) : applyMock(trip, p);
      if (updated.version <= trip.version) throw new Error('API không trả về phiên bản lịch mới hợp lệ.');
      setTrip(updated); setResult({ applied: true, choice: response?.proposals[0]?.id === p.id ? 'A' : 'B', message: `Đã áp dụng ${p.title}. Lịch trình đã được điều chỉnh.` }); return true;
    } catch (e) { setError(e instanceof Error ? e.message : 'Không lưu được. Lịch hiện hành vẫn giữ nguyên.'); return false; }
    finally { setBusy(false); }
  }
  function reject() { setError(null); setResult({ applied: false, message: `Lịch trình hiện tại được giữ nguyên. Không có thay đổi nào được áp dụng.` }); }
  function reset() { updateDraft({ restUntil: '15:00', preferredKeep: 'A04', activityId: 'A04' }); setTrip(demoTrip); setRequest(null); setResponse(null); setResult(null); setError(null); }
  return <AdaptContext.Provider value={{ trip, kind, setKind, draft, setDraft, request, response, result, busy, error, isMock: !apiConfigured, generate, choose, reject, reset }}>{children}</AdaptContext.Provider>;
}
export function useAdapt() { const value = useContext(AdaptContext); if (!value) throw new Error('AdaptProvider missing'); return value; }
