/** ADAPT contract for S04–S06. MOCK records are illustrative, not verified locations. */
export type AdaptKind = 'rest' | 'rain';
export type ActivityStatus = 'TODO' | 'PENDING' | 'DONE' | 'SKIPPED' | 'DROPPED' | 'REPLACED';
export type TravelLeg = { activity_id: string; from_place_id: string; to_place_id: string; start_time: string; end_time: string; status: 'PENDING' | 'DONE' | 'REPLACED'; type: 'TRAVEL'; data_status: 'MOCK' };
export type TravelChange = { action: 'RESCHEDULE' | 'REPLACE' | 'CREATE'; before?: TravelLeg; after?: TravelLeg };
export const isActive = (status: ActivityStatus | TravelLeg['status']) => status === 'PENDING' || status === 'TODO' || status === 'DONE';
export type Activity = { id: string; title: string; time: string; status: ActivityStatus; outdoor?: boolean };
export type CurrentTrip = { id: string; version: number; day: number; restStart: string; restEnd: string; restPlaceId?: string; deadline: string; activities: Activity[]; travelLegs?: TravelLeg[] };
export type AdaptRequest = { kind: AdaptKind; tripId: string; baseVersion: number; activityId?: string; restUntil?: string; preferredKeep?: string };
export type Proposal = { apiChanges?: string[]; id: string; baseVersion: number; kind: AdaptKind; title: string; summary: string; explanation: string; tradeoff: string; finish: string; removeId?: string; replaceId?: string; replacement?: string; restUntil?: string; travelChanges?: TravelChange[] };
export type ProposalResponse = { proposalId?: string; proposals: Proposal[]; conflict?: string; source: 'MOCK' | 'API' };

export const demoTrip: CurrentTrip = {
  id: 'MOCK-TRIP-01', version: 1, day: 2, restStart: '13:00', restEnd: '14:00', restPlaceId: 'A02', deadline: '16:30',
  activities: [
    { id: 'A01', title: 'Ga Đà Lạt', time: '08:00–09:30', status: 'DONE' },
    { id: 'A02', title: 'Thiền viện Trúc Lâm', time: '09:45–12:00', status: 'DONE' },
    { id: 'A03', title: 'Hồ Xuân Hương', time: '14:15–15:00', status: 'TODO', outdoor: true },
    { id: 'A04', title: 'Vườn hoa Đà Lạt', time: '15:15–16:00', status: 'TODO', outdoor: true },
  ],
  // MOCK topology only: IDs are illustrative, not verified travel times.
  travelLegs: [
    { activity_id: 'T01', from_place_id: 'A02', to_place_id: 'A03', start_time: '14:00', end_time: '14:15', status: 'PENDING', type: 'TRAVEL', data_status: 'MOCK' },
    { activity_id: 'T02', from_place_id: 'A03', to_place_id: 'A04', start_time: '15:00', end_time: '15:15', status: 'PENDING', type: 'TRAVEL', data_status: 'MOCK' },
    { activity_id: 'T03', from_place_id: 'A04', to_place_id: 'END-DAY', start_time: '16:00', end_time: '16:15', status: 'PENDING', type: 'TRAVEL', data_status: 'MOCK' },
  ],
};

/** UI labels only. Stable IDs remain unchanged for F05/F06 and persisted history. */
export function placeName(trip: CurrentTrip, placeId: string): string {
  const known = trip.activities.find(a => a.id === placeId);
  if (known) return known.title;
  const names = 'placeNames' in trip ? trip.placeNames as Record<string, string> : undefined;
  if (names?.[placeId]) return names[placeId];
  if (placeId === 'END-DAY') return 'Điểm kết thúc ngày';
  if (placeId.startsWith('MOCK-INDOOR-')) {
    const optionId = placeId.slice('MOCK-INDOOR-'.length);
    return optionId.startsWith('MOCK-RAIN-A-') ? 'Không gian triển lãm trong nhà'
      : optionId.startsWith('MOCK-RAIN-B-') ? 'Quán cà phê trong nhà'
      : 'Địa điểm trong nhà (MOCK)';
  }
  // Preserve unknown API identifiers rather than inventing a location name.
  return placeId;
}

/** Show the rest location from itinerary data, never a hard-coded homestay. */
export function restPlaceName(trip: CurrentTrip): string {
  if (!trip.restPlaceId) return 'địa điểm nghỉ theo lịch';
  const label = placeName(trip, trip.restPlaceId);
  return 'rawDays' in trip && label === trip.restPlaceId ? 'địa điểm nghỉ theo lịch (chưa có tên)' : label;
}

export function travelRouteName(trip: CurrentTrip, from: string, to: string): string {
  return `${placeName(trip, from)} → ${placeName(trip, to)}`;
}

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
    if (!activity || activity.status !== 'TODO' || (!activity.outdoor && !('rawDays' in trip))) return 'Chỉ chọn hoạt động ngoài trời chưa thực hiện.';
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
    { id: 'MOCK-DROP-A03', baseVersion: trip.version, kind: 'rest', title: 'Một chiều say giữa sắc hoa · Giữ Vườn hoa Đà Lạt', summary: 'Nghỉ 13:00–14:00 → 13:00–15:00; bỏ Hồ Xuân Hương', explanation: 'Theo bộ giờ mô phỏng, kết thúc dự kiến 16:15 trước hạn 16:30.', tradeoff: 'Không thực hiện Hồ Xuân Hương; giữ Vườn hoa Đà Lạt và hai hoạt động đã hoàn thành.', finish: '16:15', removeId: 'A03', restUntil: '15:00' },
    { id: 'MOCK-DROP-A04', baseVersion: trip.version, kind: 'rest', title: 'Hòa mình nghe gió kể · Giữ Hồ Xuân Hương', summary: 'Nghỉ 13:00–14:00 → 13:00–15:00; bỏ Vườn hoa Đà Lạt', explanation: 'Theo bộ giờ mô phỏng, kết thúc dự kiến 16:15 trước hạn 16:30.', tradeoff: 'Không thực hiện Vườn hoa Đà Lạt; giữ Hồ Xuân Hương và hai hoạt động đã hoàn thành.', finish: '16:15', removeId: 'A04', restUntil: '15:00' },
  ];
  // Figma defines A = keep flower garden; B = keep Xuan Huong lake. Keep this stable.
  return { proposals: options, source: 'MOCK' };
}

/** Only a UI MOCK adapter. F05/F06 remain the authority for real route validation and persistence. */
export function mockTravelChanges(trip: CurrentTrip, proposal: Proposal): TravelChange[] {
  const legs = (trip.travelLegs ?? []).filter(l => l.status === 'PENDING');
  const selected = proposal.kind === 'rest' ? proposal.removeId : proposal.replaceId;
  if (!selected) return [];
  const inbound = legs.find(l => l.to_place_id === selected);
  const outbound = legs.find(l => l.from_place_id === selected);
  if (!inbound || !outbound) return [];

  // Fixed, explicitly MOCK timetable: rest ends at 15:00, travel 15 min,
  // retained visit 15:15–16:00, final leg 16:00–16:15.
  // Rain keeps the original visit window and replaces only its two adjacent legs.
  const desired: Omit<TravelLeg, 'activity_id'>[] = [];
  if (proposal.kind === 'rest') {
    if (proposal.restUntil !== '15:00') return [];
    const kept = trip.activities.find(a => a.status === 'TODO' && a.id !== selected);
    if (!kept) return [];
    desired.push(
      { from_place_id: 'A02', to_place_id: kept.id, start_time: '15:00', end_time: '15:15', status: 'PENDING', type: 'TRAVEL', data_status: 'MOCK' },
      { from_place_id: kept.id, to_place_id: 'END-DAY', start_time: '16:00', end_time: '16:15', status: 'PENDING', type: 'TRAVEL', data_status: 'MOCK' },
    );
  } else {
    const replacement = `MOCK-INDOOR-${proposal.id}`;
    desired.push(
      { from_place_id: inbound.from_place_id, to_place_id: replacement, start_time: inbound.start_time, end_time: inbound.end_time, status: 'PENDING', type: 'TRAVEL', data_status: 'MOCK' },
      { from_place_id: replacement, to_place_id: outbound.to_place_id, start_time: outbound.start_time, end_time: outbound.end_time, status: 'PENDING', type: 'TRAVEL', data_status: 'MOCK' },
    );
  }

  const changes: TravelChange[] = [];
  const matched = new Set<string>();
  // Preserve activity_id whenever endpoints stay the same; change only its time.
  desired.forEach((target, index) => {
    if (target.from_place_id === target.to_place_id) return;
    const existing = legs.find(l => !matched.has(l.activity_id) && l.from_place_id === target.from_place_id && l.to_place_id === target.to_place_id);
    if (existing) {
      matched.add(existing.activity_id);
      if (existing.start_time !== target.start_time || existing.end_time !== target.end_time)
        changes.push({ action: 'RESCHEDULE', before: existing, after: { ...existing, start_time: target.start_time, end_time: target.end_time } });
    } else {
      changes.push({ action: 'CREATE', after: { ...target, activity_id: `MOCK-T-${proposal.id}-${index + 1}` } });
    }
  });
  // Only the affected portion of the route changes; DONE legs are untouched.
  const affected = proposal.kind === 'rest' ? legs : [inbound, outbound];
  for (const old of affected) {
    if (!matched.has(old.activity_id)) changes.unshift({ action: 'REPLACE', before: old, after: { ...old, status: 'REPLACED' } });
  }
  return changes;
}

export function previewTravelChanges(trip: CurrentTrip, proposal: Proposal): TravelChange[] {
  // Never invent route changes for API proposals that omit F05 travel data.
  return proposal.travelChanges ?? (proposal.id.startsWith('MOCK-') ? mockTravelChanges(trip, proposal) : []);
}

export function applyMock(trip: CurrentTrip, proposal: Proposal): CurrentTrip {
  if (trip.version !== proposal.baseVersion) throw new Error('Đề xuất đã cũ. Hãy tạo lại phương án.');
  const selected = proposal.kind === 'rain' ? proposal.replaceId : proposal.removeId;
  const original = trip.activities.find(a => a.id === selected);
  if (!selected || !original || !isActive(original.status) || original.status === 'DONE') throw new Error('Hoạt động không còn đủ điều kiện điều chỉnh.');
  if (proposal.kind === 'rain' && (!original.outdoor || !proposal.replacement)) throw new Error('Phương án thay thế không hợp lệ.');
  if (proposal.kind === 'rest' && !proposal.restUntil) throw new Error('Phương án nghỉ thêm không hợp lệ.');
  // Apply exactly the changes shown on S05, not a separately recomputed route.
  const changes = previewTravelChanges(trip, proposal);
  if (!changes.length) throw new Error('Phương án chưa có dữ liệu thay đổi chặng để áp dụng.');
  const travelLegs = (trip.travelLegs ?? []).map(leg => ({ ...leg }));
  const existingIds = new Set(travelLegs.map(l => l.activity_id));
  for (const change of changes) {
    if (change.action === 'CREATE') {
      if (!change.after || change.after.status !== 'PENDING') throw new Error('Chặng mới không hợp lệ.');
      if (change.after.from_place_id === change.after.to_place_id) continue;
      if (existingIds.has(change.after.activity_id)) throw new Error('Mã chặng mới đã tồn tại.');
      travelLegs.push({ ...change.after });
      existingIds.add(change.after.activity_id);
      continue;
    }
    if (!change.before || !change.after) throw new Error('Thiếu dữ liệu thay đổi chặng.');
    const index = travelLegs.findIndex(l => l.activity_id === change.before!.activity_id);
    if (index < 0) throw new Error('Không tìm thấy chặng cũ trong lịch.');
    const current = travelLegs[index];
    if (current.status !== 'PENDING') throw new Error('Không được thay đổi chặng đã hoàn thành hoặc đã thay.');
    if (change.action === 'REPLACE') {
      if (change.after.activity_id !== current.activity_id || change.after.status !== 'REPLACED')
        throw new Error('Chặng thay thế không hợp lệ.');
      travelLegs[index] = { ...current, status: 'REPLACED' };
    } else {
      // RESCHEDULE only updates times: endpoints, ID and status remain unchanged.
      if (change.after.activity_id !== current.activity_id ||
        change.after.from_place_id !== current.from_place_id ||
        change.after.to_place_id !== current.to_place_id)
        throw new Error('Đổi điểm đầu/cuối phải tạo chặng mới.');
      travelLegs[index] = { ...current, start_time: change.after.start_time, end_time: change.after.end_time };
    }
  }
  const activities = trip.activities.map(a => a.id === selected
    ? { ...a, status: (proposal.kind === 'rest' ? 'DROPPED' : 'REPLACED') as ActivityStatus } : { ...a });
  if (proposal.kind === 'rest') {
    const kept = activities.find(a => a.status === 'TODO' && a.id !== selected);
    if (!kept) throw new Error('Không tìm thấy hoạt động được giữ.');
    kept.time = '15:15–16:00'; // MOCK only; matches the travel timetable shown on S05.
  }
  if (proposal.kind === 'rain') activities.push({
    id: `MOCK-VISIT-${proposal.id}`, title: proposal.replacement!, time: original.time,
    status: 'PENDING', outdoor: false,
  });
  // Validate active travel and visit intervals before exposing the accepted MOCK itinerary.
  const activeIntervals = [
    ...travelLegs.filter(l => l.status === 'PENDING').map(l => [toMinutes(l.start_time), toMinutes(l.end_time)]),
    ...activities.filter(a => a.status === 'TODO' || a.status === 'PENDING').map(a => {
      const [start, end] = a.time.split('–');
      return [toMinutes(start), toMinutes(end)];
    }),
  ].sort((a, b) => a[0] - b[0]);
  if (activeIntervals.some(([start, end], i) => start >= end || (i > 0 && start < activeIntervals[i - 1][1])))
    throw new Error('Phương án MOCK có hoạt động hoặc chặng di chuyển chồng giờ: ' + JSON.stringify(activeIntervals));
  if (activeIntervals.some(([, end]) => end > toMinutes(trip.deadline)))
    throw new Error('Phương án vượt quá hạn kết thúc ngày.');
  if (proposal.kind === 'rest' && activeIntervals.some(([start]) => start < toMinutes(proposal.restUntil!)))
    throw new Error('Phương án di chuyển trước khi kết thúc nghỉ thêm.');
  return { ...trip, version: trip.version + 1, restEnd: proposal.kind === 'rest' ? proposal.restUntil! : trip.restEnd,
    activities, travelLegs };
}

/** Current itinerary must not include historical REPLACED/DROPPED activities. */
export function activeTravelLegs(trip: CurrentTrip): TravelLeg[] {
  return (trip.travelLegs ?? [])
    .filter(l => l.status === 'PENDING' || l.status === 'DONE')
    .sort((a, b) => a.start_time.localeCompare(b.start_time) || a.end_time.localeCompare(b.end_time) || a.activity_id.localeCompare(b.activity_id));
}
