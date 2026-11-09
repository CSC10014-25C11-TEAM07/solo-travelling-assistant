/** ADAPT contract for S04–S06. MOCK records are illustrative, not verified locations. */
export type AdaptKind = 'rest' | 'rain';
export type ActivityStatus = 'TODO' | 'DONE' | 'SKIPPED' | 'REPLACED';
export type Activity = { id: string; title: string; time: string; status: ActivityStatus; outdoor?: boolean };
export type CurrentTrip = { id: string; version: number; day: number; restStart: string; restEnd: string; deadline: string; activities: Activity[] };
export type AdaptRequest = { kind: AdaptKind; tripId: string; baseVersion: number; activityId?: string; restUntil?: string; preferredKeep?: string };
export type Proposal = { id: string; baseVersion: number; kind: AdaptKind; title: string; summary: string; explanation: string; tradeoff: string; finish: string; removeId?: string; replaceId?: string; replacement?: string; restUntil?: string };
export type ProposalResponse = { proposals: Proposal[]; conflict?: string; source: 'MOCK' | 'API' };

export const demoTrip: CurrentTrip = {
  id: 'MOCK-TRIP-01', version: 1, day: 2, restStart: '13:00', restEnd: '14:00', deadline: '16:30',
  activities: [
    { id: 'A01', title: 'Ga Đà Lạt', time: '08:00–09:30', status: 'DONE' },
    { id: 'A02', title: 'Thiền viện Trúc Lâm', time: '09:45–12:00', status: 'DONE' },
    { id: 'A03', title: 'Hồ Xuân Hương', time: '15:30–16:30', status: 'TODO', outdoor: true },
    { id: 'A04', title: 'Vườn hoa Đà Lạt', time: '15:30–16:30', status: 'TODO', outdoor: true },
  ],
};

export function toMinutes(hhmm: string): number {
  if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(hhmm)) throw new Error('Nhập giờ theo định dạng HH:mm (00:00–23:59).');
  const [h, m] = hhmm.split(':').map(Number);
  return h * 60 + m;
}

export function validateRequest(trip: CurrentTrip, req: AdaptRequest): string | null {
  if (req.tripId !== trip.id || req.baseVersion !== trip.version) return 'Lịch đã thay đổi. Hãy tạo lại phương án.';
  if (req.kind === 'rest') {
    try {
      if (!req.restUntil || toMinutes(req.restUntil) <= toMinutes(trip.restEnd)) return 'Giờ nghỉ mới phải sau giờ nghỉ hiện tại.';
    } catch (e) { return (e as Error).message; }
  } else {
    const activity = trip.activities.find(a => a.id === req.activityId);
    if (!activity || !activity.outdoor || activity.status !== 'TODO') return 'Chỉ chọn hoạt động ngoài trời chưa thực hiện.';
  }
  return null;
}

/** Deterministic UI-only sample. The backend must validate real locations, opening hours and travel time. */
export function mockProposals(trip: CurrentTrip, req: AdaptRequest): ProposalResponse {
  const error = validateRequest(trip, req);
  if (error) return { proposals: [], conflict: error, source: 'MOCK' };
  if (req.kind === 'rain') {
    // Day-2 JSON sample only: all locations, times and travel estimates below are illustrative.
    const selected = trip.activities.find(a => a.id === req.activityId)!;
    return {
      source: 'MOCK',
      proposals: [
        {
          id: `MOCK-RAIN-A-${selected.id}`, baseVersion: trip.version, kind: 'rain',
          title: 'Phương án A · Không gian triển lãm',
          summary: `${selected.title} → Không gian triển lãm trong nhà`,
          explanation: 'Chuyển sang hoạt động trong nhà để tránh mưa; giờ mở cửa và thời gian di chuyển chỉ là minh họa.',
          tradeoff: `Không tham quan ${selected.title} ngoài trời.`, finish: '16:15',
          replaceId: selected.id, replacement: 'Không gian triển lãm trong nhà',
        },
        {
          id: `MOCK-RAIN-B-${selected.id}`, baseVersion: trip.version, kind: 'rain',
          title: 'Phương án B · Quán cà phê trong nhà',
          summary: `${selected.title} → Quán cà phê trong nhà`,
          explanation: 'Một lựa chọn trong nhà khác, thiên về nghỉ ngơi; địa điểm và thời gian chưa được xác minh.',
          tradeoff: `Thay trải nghiệm tham quan ${selected.title} bằng nghỉ tại quán.`, finish: '16:15',
          replaceId: selected.id, replacement: 'Quán cà phê trong nhà',
        },
      ],
    };
  }
  if (toMinutes(req.restUntil!) >= toMinutes(trip.deadline) - 15) return {
    proposals: [], source: 'MOCK', conflict: 'Giờ nghỉ mới không còn đủ tối thiểu 15 phút di chuyển trước mốc 16:30.',
  };
  if (req.restUntil !== '15:00') return {
    proposals: [], source: 'MOCK', conflict: 'Hiện chưa thể đề xuất lịch cho giờ nghỉ này. Vui lòng thử nghỉ đến 15:00.',
  };
  const options: Proposal[] = [
    { id: 'MOCK-DROP-A03', baseVersion: trip.version, kind: 'rest', title: 'Một chiều say giữa sắc hoa · Giữ Vườn hoa Đà Lạt', summary: 'Nghỉ 13:00–14:00 → 13:00–15:00; bỏ A03', explanation: 'Theo bộ giờ mô phỏng, kết thúc dự kiến 16:15 trước hạn 16:30.', tradeoff: 'Không thực hiện A03; giữ A04 và hai hoạt động đã hoàn thành.', finish: '16:15', removeId: 'A03', restUntil: '15:00' },
    { id: 'MOCK-DROP-A04', baseVersion: trip.version, kind: 'rest', title: 'Hòa mình nghe gió kể · Giữ Hồ Xuân Hương', summary: 'Nghỉ 13:00–14:00 → 13:00–15:00; bỏ A04', explanation: 'Theo bộ giờ mô phỏng, kết thúc dự kiến 16:15 trước hạn 16:30.', tradeoff: 'Không thực hiện A04; giữ A03 và hai hoạt động đã hoàn thành.', finish: '16:15', removeId: 'A04', restUntil: '15:00' },
  ];
  // Figma defines A = keep flower garden; B = keep Xuan Huong lake. Keep this stable.
  return { proposals: options, source: 'MOCK' };
}

export function applyMock(trip: CurrentTrip, proposal: Proposal): CurrentTrip {
  if (trip.version !== proposal.baseVersion) throw new Error('Đề xuất đã cũ. Hãy tạo lại phương án.');
  if (proposal.kind === 'rain') {
    if (!proposal.replaceId || !proposal.replacement) throw new Error('Phương án thay thế không hợp lệ.');
    const activity = trip.activities.find(a => a.id === proposal.replaceId);
    if (!activity || activity.status !== 'TODO' || !activity.outdoor) throw new Error('Hoạt động không còn đủ điều kiện thay thế.');
    return { ...trip, version: trip.version + 1,
      activities: trip.activities.map(a => a.id === proposal.replaceId
        ? { ...a, title: proposal.replacement!, outdoor: false, status: 'REPLACED' as const } : a) };
  }
  if (!proposal.restUntil || !proposal.removeId) throw new Error('Phương án nghỉ thêm không hợp lệ.');
  return { ...trip, version: trip.version + 1, restEnd: proposal.restUntil,
    activities: trip.activities.map(a => a.id === proposal.removeId && a.status === 'TODO' ? { ...a, status: 'SKIPPED' as const } : a) };
}
